param(
    [string]$HookLog = (Join-Path $PSScriptRoot 'last-nexus-hook.log'),
    [string]$ServerLog = (Join-Path $PSScriptRoot 'last-server-full.log')
)

$ErrorActionPreference = 'Stop'

Write-Host '=== Tython world-entry trace summary ==='

if (Test-Path -LiteralPath $HookLog) {
    $hookLines = Get-Content -LiteralPath $HookLog
    $rpc = foreach ($line in $hookLines) {
        if ($line -match 'AreaRpcHook.*operation=0x([0-9A-Fa-f]{8})') {
            [pscustomobject]@{ Operation = $matches[1].ToUpperInvariant(); Line = $line }
        } elseif ($line -match 'AreaRpcHook.*bytes=C7 [0-9A-Fa-f]{2} [0-9A-Fa-f]{2} [0-9A-Fa-f]{2} [0-9A-Fa-f]{2} ([0-9A-Fa-f]{2}) ([0-9A-Fa-f]{2}) ([0-9A-Fa-f]{2}) ([0-9A-Fa-f]{2})') {
            # Older hook logs did not label the operation field; decode the
            # little-endian dword at payload bytes 5..8 for compatibility.
            [pscustomobject]@{
                Operation = ($matches[4] + $matches[3] + $matches[2] + $matches[1]).ToUpperInvariant()
                Line = $line
            }
        }
    }
    $events = foreach ($line in $hookLines) {
        if ($line -match 'EventDispatchHook.*class=(\d+).*hash=0x([0-9A-Fa-f]{8}).*handlerRva=0x([0-9A-Fa-f]{8})') {
            [pscustomobject]@{
                Class = [int]$matches[1]
                Hash = $matches[2].ToUpperInvariant()
                HandlerRva = $matches[3].ToUpperInvariant()
            }
        }
    }

    Write-Host ("Hook log: {0}" -f $HookLog)
    if ($rpc) {
        Write-Host 'Outbound operations:'
        $rpc | Group-Object Operation | Sort-Object Count -Descending |
            ForEach-Object { Write-Host ("  0x{0}: {1}" -f $_.Name, $_.Count) }
    } else {
        Write-Warning 'No outbound RPC operations were captured.'
    }

    if ($events) {
        Write-Host 'Event dispatcher:'
        $events | Group-Object Class, HandlerRva | Sort-Object Count -Descending |
            ForEach-Object {
                $sample = $_.Group[0]
                $uniqueHashes = @($_.Group.Hash | Sort-Object -Unique).Count
                Write-Host ("  class {0}, handler RVA 0x{1}: {2} samples, {3} payload fingerprints" -f
                    $sample.Class, $sample.HandlerRva, $_.Count, $uniqueHashes)
            }
    } else {
        Write-Warning 'No event-dispatch samples were captured. Confirm event trace=enabled at client startup.'
    }

    $results = @($hookLines | Where-Object { $_ -match 'SMsgResultsHook' })
    $resultEntries = @($hookLines | Where-Object { $_ -match 'OmegaMessageHook.*phase=enter.*opcode=0xD5280283' }).Count
    $resultField1 = @($results | Where-Object { $_ -match 'field=1(?:\s|$)' }).Count
    $resultField2 = @($results | Where-Object { $_ -match 'field=2(?:\s|$)' }).Count
    Write-Host ("Inbound SMSG_RESULTS fields decoded: {0} (field 1: {1}, field 2: {2})" -f
        $results.Count, $resultField1, $resultField2)
    Write-Host ("Inbound SMSG_RESULTS handler entries: {0}" -f $resultEntries)

    $pollCount = @($rpc | Where-Object Operation -eq 'F5F540F2').Count
    if ($pollCount -ge 2) {
        Write-Warning ("Repeated 0xF5F540F2 loading poll detected ({0} captures): client likely remained in its readiness loop." -f $pollCount)
    }
} else {
    Write-Warning ("Hook log not found: {0}" -f $HookLog)
}

if (Test-Path -LiteralPath $ServerLog) {
    $serverText = Get-Content -LiteralPath $ServerLog -Raw
    Write-Host ("Server log: {0}" -f $ServerLog)
    $startupEmitted = [bool]($serverText -match 'AreaStartupBundle: area startup sent')
    $clientDisconnected = [bool]($serverText -match "Client '.*' disconnected")
    $omegaResults = [regex]::Matches($serverText, 'SMSG_RESULTS .* sent via Omega 0x65A7->0x0000').Count
    Write-Host ("  startup bundle emitted: {0}" -f $startupEmitted)
    Write-Host ("  Omega result replies:    {0}" -f $omegaResults)
    Write-Host ("  client disconnected:    {0}" -f $clientDisconnected)

    if (Test-Path -LiteralPath $HookLog) {
        Write-Host 'Diagnosis:'
        if ($omegaResults -eq 0) {
            Write-Warning '  Server never sent the corrected Omega reply; investigate the request/server path.'
        } elseif ($resultEntries -eq 0) {
            Write-Warning '  Server sent Omega replies, but the client message handler never received the opcode; routing or outer framing is wrong.'
        } elseif ($resultField1 -eq 0) {
            Write-Warning '  Client handler received SMSG_RESULTS but never decoded field 1; the reader/payload boundary is wrong.'
        } elseif ($resultField2 -eq 0) {
            Write-Warning '  Client began SMSG_RESULTS decoding but did not finish both fields; payload encoding/length is wrong.'
        } elseif ($pollCount -ge 2) {
            Write-Warning '  Client fully decoded SMSG_RESULTS but kept polling; the remaining gate is after result parsing (matching or script/state handling).'
        } else {
            Write-Host '  Omega replies reached and fully decoded in the client; no repeated readiness loop was captured.'
        }
    }
} else {
    Write-Warning ("Server log not found: {0}" -f $ServerLog)
}
