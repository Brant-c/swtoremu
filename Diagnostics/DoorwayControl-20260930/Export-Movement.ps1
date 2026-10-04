param([Parameter(Mandatory=$true)][string]$ServerLog,
      [Parameter(Mandatory=$true)][string]$OutputCsv)
$ErrorActionPreference = 'Stop'
if ([Environment]::Is64BitProcess) { throw 'Use SysWOW64 Windows PowerShell (x86).' }
if (Test-Path $OutputCsv) { throw 'Choose a new output name; do not overwrite evidence.' }
$assembly = [Reflection.Assembly]::LoadFrom((Join-Path $PSScriptRoot 'build/NexusToRServer.exe'))
$type = $assembly.GetType('NexusToRServer.NET.Packets.Client.CMsg61116AD5',$true)
Import-Module (Join-Path (Split-Path $PSScriptRoot -Parent) 'PacketWorkbench.psm1') -Force
$previousX = $null
$lineNo = 0
$rows = foreach ($line in [IO.File]::ReadLines((Resolve-Path $ServerLog))) {
    $lineNo++
    if ($line -notmatch '^\[(?<time>[^\]]+)\].*AREA-POLL CMsg61116AD5: component=0x(?<component>[0-9A-Fa-f]{8}) .* body=(?<hex>[0-9A-Fa-f-]+)$') { continue }
    $stamp=$Matches.time; $component=[Convert]::ToUInt32($Matches.component,16)
    $body=ConvertFrom-PacketHex ($Matches.hex -replace '-',' ')
    # Reconstruct only the logged plaintext header/body, never send or Run it.
    [byte[]]$bytes=@([BitConverter]::GetBytes([uint32]0x61116AD5)) + @([BitConverter]::GetBytes($component)) + @($body)
    $packet=[Activator]::CreateInstance($type,$true)
    $packet.SetBuffers($bytes)
    try {
        if (!$packet.Read()) {
            [pscustomobject]@{LogWriteTime=$stamp; Line=$lineNo; Heading=$null;
                X=$null; Y=$null; Z=$null; CrossesDetectorPlane=$false;
                Plaintext=([BitConverter]::ToString($bytes)); TimestampBasis='server asynchronous log-write time; not receive time'; Accepted=$false}
            continue
        }
        $values=@{}
        foreach($name in @('_heading','_x','_y','_z')) {
            $values[$name]=$type.GetField($name,[Reflection.BindingFlags]'Instance,NonPublic').GetValue($packet)
        }
        [pscustomobject]@{LogWriteTime=$stamp; Line=$lineNo; Heading=$values._heading;
            X=$values._x; Y=$values._y; Z=$values._z;
            CrossesDetectorPlane=($null -ne $previousX -and $previousX -lt -63 -and $values._x -ge -63);
            Plaintext=([BitConverter]::ToString($bytes)); TimestampBasis='server asynchronous log-write time; not receive time'; Accepted=$true}
        $previousX=$values._x
    } finally { $packet.Dispose() }
}
if (!$rows) { throw 'No accepted C5 movement records; no crossing conclusion is possible.' }
$rows | Export-Csv -LiteralPath $OutputCsv -NoTypeInformation
