param(
    [string]$HookLog,
    [string]$ServerLog
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($HookLog)) {
    $snapshot = Join-Path $PSScriptRoot 'last-nexus-hook.log'
    $live = Join-Path (Split-Path $PSScriptRoot -Parent) 'nexusclient\nexusclient\nexus_hook.log'
    $HookLog = @($snapshot, $live) | Where-Object { Test-Path -LiteralPath $_ } |
        Sort-Object { (Get-Item -LiteralPath $_).LastWriteTimeUtc } -Descending |
        Select-Object -First 1
}
if ([string]::IsNullOrWhiteSpace($ServerLog)) {
    $snapshot = Join-Path $PSScriptRoot 'last-server-full.log'
    $live = Join-Path (Split-Path $PSScriptRoot -Parent) 'SharpServer\bin\Debug\NexusToR.log'
    $ServerLog = @($snapshot, $live) | Where-Object { Test-Path -LiteralPath $_ } |
        Sort-Object { (Get-Item -LiteralPath $_).LastWriteTimeUtc } -Descending |
        Select-Object -First 1
}

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
        if ($line -match 'EventDispatchHook.*class=(\d+).*callerRva=0x([0-9A-Fa-f]{8}).*hash=0x([0-9A-Fa-f]{8}).*handlerRva=0x([0-9A-Fa-f]{8})') {
            [pscustomobject]@{
                Class = [int]$matches[1]
                CallerRva = $matches[2].ToUpperInvariant()
                Hash = $matches[3].ToUpperInvariant()
                HandlerRva = $matches[4].ToUpperInvariant()
            }
        } elseif ($line -match 'EventDispatchHook.*class=(\d+).*hash=0x([0-9A-Fa-f]{8}).*handlerRva=0x([0-9A-Fa-f]{8})') {
            [pscustomobject]@{
                Class = [int]$matches[1]
                CallerRva = 'UNKNOWN'
                Hash = $matches[2].ToUpperInvariant()
                HandlerRva = $matches[3].ToUpperInvariant()
            }
        }
    }
    $activeReadiness = @($hookLines | Where-Object { $_ -match 'ReadinessActiveHook.*depth=[1-9]' })
    $readinessVm = @($hookLines | Where-Object { $_ -match 'ReadinessVmHook' })
    $loadingGom = @($hookLines | Where-Object { $_ -match 'LoadingGomHook.*name=' })
    $playerFields = foreach ($line in $hookLines) {
        if ($line -match 'PlayerFieldHook.*name=([^ ]+).*id=0x([0-9A-Fa-f]{16}).*interface=([^ ]+).*result=([^ ]+).*words=([^ ]+).*stack=(.*)$') {
            [pscustomobject]@{
                Name = $matches[1]
                Id = $matches[2].ToUpperInvariant()
                Interface = $matches[3]
                Result = $matches[4]
                Words = $matches[5].ToUpperInvariant()
                Stack = $matches[6]
                Line = $line
            }
        }
    }

    Write-Host ("Hook log: {0}" -f $HookLog)
    Write-Host ("Correlated field-copy contexts (not VM calls): {0}" -f $activeReadiness.Count)
    if ($activeReadiness.Count) {
        $activeReadiness | Select-Object -Unique |
            ForEach-Object { Write-Host ("  {0}" -f $_) }
    }
    Write-Host ("Correlated replicated-field samples: {0}" -f $readinessVm.Count)
    if ($readinessVm.Count) {
        $readinessVm | Select-Object -First 30 |
            ForEach-Object { Write-Host ("  {0}" -f $_) }
    }
    Write-Host ("Observed player-field reads: {0}" -f @($playerFields).Count)
    if ($playerFields) {
        $playerFields | Group-Object Name | Sort-Object Name |
            ForEach-Object {
                $distinctValues = @($_.Group | ForEach-Object {
                    "interface={0} result={1} words={2}" -f $_.Interface, $_.Result, $_.Words
                } | Sort-Object -Unique)
                Write-Host ("  {0}: {1} reads, {2} distinct raw value shapes" -f
                    $_.Name, $_.Count, $distinctValues.Count)
                $distinctValues | Select-Object -First 8 |
                    ForEach-Object { Write-Host ("    {0}" -f $_) }
            }
    } else {
        Write-Warning 'No target player-field reads were observed. This means the client did not naturally call the traced getter for these fields during the captured interval; it does not establish their runtime values.'
    }
    Write-Host ("Loading-screen GOM lookups: {0}" -f $loadingGom.Count)
    if ($loadingGom.Count) {
        $loadingGom | ForEach-Object {
            if ($_ -match 'name=([^ ]+)') { $matches[1] }
        } | Group-Object | Sort-Object Count -Descending |
            ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
        $loadingGom | Select-Object -First 20 |
            ForEach-Object { Write-Host ("  {0}" -f $_) }
    } else {
        Write-Warning 'No loading-screen GOM lookup matched. Confirm loading-screen trace=enabled at client startup.'
    }
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
        Write-Host 'Event-dispatch direct callers:'
        $events | Group-Object CallerRva | Sort-Object Count -Descending |
            ForEach-Object { Write-Host ("  RVA 0x{0}: {1}" -f $_.Name, $_.Count) }
    } else {
        Write-Warning 'No event-dispatch samples were captured. Confirm event trace=enabled at client startup.'
    }

    $bridges = foreach ($line in $hookLines) {
        if ($line -match 'Class1BridgeHook.*phase=enter.*recipient=([0-9A-Fa-f]+).*methodRva=0x([0-9A-Fa-f]{8})') {
            [pscustomobject]@{ Recipient = $matches[1]; MethodRva = $matches[2].ToUpperInvariant() }
        }
    }
    if ($bridges) {
        Write-Host 'Class-1 runtime recipients:'
        $bridges | Group-Object Recipient, MethodRva | Sort-Object Count -Descending |
            ForEach-Object {
                $sample = $_.Group[0]
                Write-Host ("  recipient {0}, method RVA 0x{1}: {2} calls" -f
                    $sample.Recipient, $sample.MethodRva, $_.Count)
            }
    } else {
        Write-Warning 'No class-1 bridge samples were captured; confirm the new hook was installed.'
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

$compatibilityLog = Join-Path $PSScriptRoot 'last-compatibility-run.log'
if (Test-Path -LiteralPath $compatibilityLog) {
    $compatibilityLines = Get-Content -LiteralPath $compatibilityLog
    $onEnter = @($compatibilityLines | Where-Object { $_ -match '^OnEnter batch ' })
    $stateReceiver = @($compatibilityLines | Where-Object { $_ -match '^CharacterChangeState receiver ' })
    $loadingTimerAccess = @($compatibilityLines | Where-Object { $_ -match '^Loading-screen timer access:' })
    $onEnterLookups = @()
    $insideOnEnter = $false
    foreach ($line in $compatibilityLines) {
        if ($line -match '^OnEnter batch callback:') { $insideOnEnter = $true }
        elseif ($line -match '^OnEnter batch returned:') { $insideOnEnter = $false }
        elseif ($insideOnEnter -and $line -match '^Script lookup RVA=') { $onEnterLookups += $line }
    }
    Write-Host ("Client activation boundaries: OnEnter={0}, state-receiver={1}, scoped script-lookups={2}" -f
        $onEnter.Count, $stateReceiver.Count, $onEnterLookups.Count)
    Write-Host ("Loading-screen timer accesses: {0}" -f $loadingTimerAccess.Count)
    if ($loadingTimerAccess.Count) {
        $loadingTimerAccess | ForEach-Object {
            if ($_ -match 'field=([^ ]+)') { $matches[1] }
        } | Group-Object | Sort-Object Count -Descending |
            ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
    } elseif ($compatibilityLines -match 'Loading-screen timer accessor located') {
        Write-Warning '  The generated timer accessor was found, but the loading script never called it during the captured interval.'
    } elseif ($compatibilityLines -match 'Loading-screen timer accessor was not present') {
        Write-Warning '  The generated loading-screen timer accessor was not present when active-area completion ran.'
    }
    if (-not $onEnter) {
        Write-Warning '  The On Enter RPC batch did not reach its client callback.'
    } elseif (-not ($onEnter -match 'returned')) {
        Write-Warning '  The On Enter RPC batch entered but did not return normally.'
    } elseif (-not $onEnterLookups) {
        Write-Warning '  The On Enter callback returned without entering the traced script lookup pipeline.'
    }
    if ($stateReceiver -and -not ($stateReceiver -match 'state-dispatch')) {
        Write-Warning '  CharacterChangeState found no usable character state component; its state was not applied.'
    }
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
        if ($pollCount -ge 2 -and $bridges) {
            Write-Warning '  Readiness polling continued. The class-1 bridge is correlated transport/copy machinery, not a resolved Hero-script recipient.'
        } elseif ($pollCount -ge 2) {
            Write-Warning '  Readiness polling continued, but the class-1 recipient hook produced no evidence.'
        } else {
            Write-Host '  No repeated readiness loop was captured.'
        }
    }
} else {
    Write-Warning ("Server log not found: {0}" -f $ServerLog)
}
