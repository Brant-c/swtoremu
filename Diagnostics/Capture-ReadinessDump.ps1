param(
    [string]$HookLog = (Join-Path $PSScriptRoot '..\nexusclient\nexusclient\nexus_hook.log'),
    [string]$OutputDirectory = $PSScriptRoot,
    [string]$WatcherLog = (Join-Path $PSScriptRoot 'readiness-dump-watcher.log'),
    [int]$TimeoutSeconds = 600
)

$ErrorActionPreference = 'Stop'
$marker = 'ReadinessCaptureWindow: begin'
$started = Get-Date
$initialLength = if (Test-Path -LiteralPath $HookLog) {
    (Get-Item -LiteralPath $HookLog).Length
} else { 0L }
$readOffset = $initialLength

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ReadinessThreadControl {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr OpenProcess(uint access, bool inherit, uint id);
    [DllImport("ntdll.dll")]
    public static extern int NtSuspendProcess(IntPtr process);
    [DllImport("ntdll.dll")]
    public static extern int NtResumeProcess(IntPtr process);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr OpenThread(uint access, bool inherit, uint id);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SuspendThread(IntPtr thread);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr handle);
}
'@

function Suspend-WholeProcess([Diagnostics.Process]$Process) {
    # PROCESS_SUSPEND_RESUME. NtSuspendProcess operates on the process as a
    # unit, avoiding races where a new thread appears during enumeration.
    $handle = [ReadinessThreadControl]::OpenProcess(0x0800, $false, $Process.Id)
    if ($handle -eq [IntPtr]::Zero) {
        throw "Could not open PID $($Process.Id) for process-wide suspension."
    }
    $status = [ReadinessThreadControl]::NtSuspendProcess($handle)
    if ($status -ne 0) {
        [void][ReadinessThreadControl]::CloseHandle($handle)
        throw ('NtSuspendProcess failed with status 0x{0:X8}.' -f $status)
    }
    return $handle
}

function Resume-WholeProcess([IntPtr]$Handle) {
    if ($Handle -eq [IntPtr]::Zero) { return }
    [void][ReadinessThreadControl]::NtResumeProcess($Handle)
    [void][ReadinessThreadControl]::CloseHandle($Handle)
}

function Suspend-ProcessThreads([Diagnostics.Process]$Process, [int]$ExcludedThreadId) {
    $handles = [Collections.Generic.List[IntPtr]]::new()
    $failures = [Collections.Generic.List[int]]::new()
    foreach ($thread in $Process.Threads) {
        if ($thread.Id -eq $ExcludedThreadId) { continue }
        $handle = [ReadinessThreadControl]::OpenThread(0x0002, $false, $thread.Id)
        if ($handle -eq [IntPtr]::Zero) {
            $failures.Add($thread.Id)
            continue
        }
        if ([ReadinessThreadControl]::SuspendThread($handle) -eq [uint32]::MaxValue) {
            [void][ReadinessThreadControl]::CloseHandle($handle)
            $failures.Add($thread.Id)
            continue
        }
        $handles.Add($handle)
    }
    return [pscustomobject]@{
        Handles = $handles.ToArray()
        Failures = $failures.ToArray()
    }
}

function Resume-ProcessThreads($Handles) {
    foreach ($handle in $Handles) {
        [void][ReadinessThreadControl]::ResumeThread($handle)
        [void][ReadinessThreadControl]::CloseHandle($handle)
    }
}

function Write-WatcherLog([string]$Message) {
    $line = '[{0:HH:mm:ss}] [readiness-dump] {1}' -f (Get-Date), $Message
    Write-Host $line
    Add-Content -LiteralPath $WatcherLog -Value $line
}

Set-Content -LiteralPath $WatcherLog -Value ''
Write-WatcherLog "Waiting for the live periodic-VM capture window."
while (((Get-Date) - $started).TotalSeconds -lt $TimeoutSeconds) {
    $process = Get-Process -Name 'swtor-emu' -ErrorAction SilentlyContinue |
        Sort-Object StartTime -Descending | Select-Object -First 1
    if ($process -and (Test-Path -LiteralPath $HookLog)) {
        $stream = [IO.File]::Open($HookLog, 'Open', 'Read', 'ReadWrite')
        try {
            if ($stream.Length -gt $readOffset) {
                $stream.Position = [Math]::Min($readOffset, $stream.Length)
                $reader = [IO.StreamReader]::new($stream)
                $newText = $reader.ReadToEnd()
                $readOffset = $stream.Length
                if ($newText.Contains($marker)) {
                    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
                    $dumpPath = Join-Path $OutputDirectory "readiness-$stamp-$($process.Id).dmp"
                    $window = [regex]::Match($newText,
                        'ReadinessCaptureWindow: begin[^\r\n]*thread=(\d+)')
                    if (-not $window.Success) {
                        throw 'Capture-window marker did not contain its hook thread ID.'
                    }
                    $hookThreadId = [int]$window.Groups[1].Value
                    $suspension = Suspend-ProcessThreads $process $hookThreadId
                    if ($suspension.Failures.Count -gt 0) {
                        Resume-ProcessThreads $suspension.Handles
                        throw "Could not suspend client threads: $($suspension.Failures -join ', ')."
                    }
                    Write-WatcherLog "Observed live VM capture window; kept hook thread $hookThreadId parked, suspended $($suspension.Handles.Count) other threads, and capturing PID $($process.Id) to $dumpPath"
                    try {
                        & "$env:WINDIR\SysWOW64\rundll32.exe" `
                            "$env:WINDIR\SysWOW64\comsvcs.dll,MiniDump" `
                            $process.Id $dumpPath full
                        $deadline = (Get-Date).AddMinutes(3)
                        $finalized = $false
                        $previousLength = -1L
                        $stableSamples = 0
                        while ((Get-Date) -lt $deadline) {
                            if (Test-Path -LiteralPath $dumpPath) {
                                $currentLength = (Get-Item -LiteralPath $dumpPath).Length
                                if ($currentLength -gt 10MB -and $currentLength -eq $previousLength) {
                                    $stableSamples++
                                } else {
                                    $stableSamples = 0
                                }
                                $previousLength = $currentLength
                                if ($stableSamples -ge 6) {
                                    $finalized = $true
                                    break
                                }
                            }
                            Start-Sleep -Milliseconds 500
                        }
                    } finally {
                        Resume-ProcessThreads $suspension.Handles
                    }
                    if (-not $finalized) {
                        throw 'Full-memory capture did not finish within three minutes.'
                    }
                    # A valid x86 full dump is far larger than the roughly
                    # 100-KB metadata-only dump produced when "full" is lost.
                    $dumpLength = (Get-Item -LiteralPath $dumpPath).Length
                    if ($dumpLength -lt 10MB) {
                        throw "Capture is only $dumpLength bytes and has no full-memory stream."
                    }
                    # comsvcs can leave a restrictive ACL even though the dump
                    # was requested by this user. Make the offline artifact
                    # readable by the account running the trace launcher.
                    & "$env:WINDIR\System32\icacls.exe" $dumpPath `
                        /grant "$($env:USERNAME):(F)" | Out-Null
                    Write-WatcherLog "Capture complete ($dumpLength bytes)."
                    exit 0
                }
            }
        } finally {
            $stream.Dispose()
        }
    }
    Start-Sleep -Milliseconds 500
}

throw "No live periodic-VM capture window appeared within $TimeoutSeconds seconds."
