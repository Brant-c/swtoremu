# Development and research workflow

Find the earliest missing or incorrect shared dependency before pursuing another
visible feature. Compare exact April native-client evidence, original upstream
implementation, current implementation, and identified runtime logs. Preserve
unresolved differences; upstream history is evidence, not automatic correctness.

## Build / start / logs

`scripts/Build-Server.ps1` discovers MSBuild using PATH or VS Installer/vswhere,
builds both existing C# projects as Debug/x86, and copies source Shards.xml for
the normal build. Use `-ValidationOutput Diagnostics/RepositoryCleanup-20261004/build`
to keep binaries/intermediates separate from accepted gameplay inputs. The
normal build updates executable/config inputs and can invalidate historical
launch pins; never silently rewrite identity.csv to make a launch pass.

`scripts/Start-Servers.ps1 -CheckOnly` verifies executables, shard config and the
27 inherited area fixtures. Without CheckOnly it rejects running copies,
inherited experiment switches and occupied ports, snapshots prior logs, then
starts only the existing servers hidden in their required working directories.
It does not prove binding/TLS/readiness or prepare the April client. Shard-list
generates its certificate in code; its legacy credential constants are not
deployment configuration. Main server does not call Database.Initialize.

Runtime log producers remain the existing server `Base/Log.cs`, client hook and
CompatibilityLauncher. `scripts/Collect-Logs.ps1` copies their available output
to a unique `RuntimeLogs/` directory, preserving timestamps and SHA256 hashes.
It can include a specific native log via `-ClientLog`. Source logs are not
rotated/deleted. Console captures from server-only startup also live under
RuntimeLogs/server-*. A live copy is not an atomic cross-process snapshot.

| Producer | Existing source location |
|---|---|
| Server structured log | SharpServer/bin/Debug/NexusToR.log |
| Hook | nexusclient/nexusclient/nexus_hook.log |
| Trace wrapper console | Diagnostics/trace-server.out |
| Latest copied diagnostic logs | Diagnostics/last-{server-full,server-out,nexus-hook,compatibility-run}.log |
| Native client | Operator's SWTOR log location; supply exact path |

RuntimeLogs is ignored local material. Promote only necessary, redacted evidence
to a controlled experiment record with identity/hashes and interpretations.
Mutable `last-*` logs can belong to different runs; compare their enclosed times.
`prelaunch-*` preserves the previous run, not necessarily the folder-date run.

## Client experiments and retained tools

The historical RetreatGateway and Taxi Launch.ps1 chains preserve behavior and
exact input identities; their old pins can be stale. Consult the cleanup pin
audit before use. Neither is advertised as freshly validated. Direct
Trace-Tython/F96/With-Status launchers select different switches and can start a
client, copy files and rotate logs. They remain reference/experiment entry points,
not aliases for server-only startup. Do not use archived root probes as runners.

Use PacketWorkbench for plaintext packets/fixtures; PacketAnalyser for its
existing capture/key/decryption workflow. Tools/Hero/Hero/PackedStream.cs is
the local packed-value reference. SCPTExtractor, `_JPEXTRACT`, tor_tools and
external extracTOR/extracted resources provide semantics, not native wire order.
Specialized Trace*.cpp programs are breakpoint/injection research utilities,
not competing supported runtime loggers. Keep them opt-in and untouched until
their assumptions and unique evidence are understood.

## Validation

For the server assembly use Windows **32-bit** PowerShell and explicitly pass
the assembly being checked. Read each script's parameters first:

```powershell
$host32 = "$env:WINDIR\SysWOW64\WindowsPowerShell\v1.0\powershell.exe"
$assembly = "$PWD\SharpServer\bin\Debug\NexusToRServer.exe"
& $host32 -NoProfile -File Diagnostics/Test-AreaRouting.ps1 -AssemblyPath $assembly
& $host32 -NoProfile -File Diagnostics/Test-AreaBlobFraming.ps1 -AssemblyPath $assembly
& $host32 -NoProfile -File Diagnostics/Test-AreaWireRoundTrip.ps1 -AssemblyPath $assembly
& $host32 -NoProfile -File Diagnostics/Test-WorldEntryOffline.ps1 -AssemblyPath $assembly
& $host32 -NoProfile -File Diagnostics/Test-PacketWorkbench.ps1
```

WorldEntryOffline internally invokes AreaWireRoundTrip with its historical
default build path. Its first observer assertion currently fails; fixing or
removing that assertion requires investigating source/history, not suppressing
the test to claim success. The other four checks pass during this cleanup.
Offline framing/build success never establishes native client acceptance.

Every new protocol claim belongs in Protocol-Evidence.csv with one confidence
level: Captured, Client-derived, Behavior-verified or Hypothesis. Create run
records with New-ProtocolExperiment.ps1; state exact input bytes, positive and
negative predictions and deciding logs before running. Change one protocol
variable per client run. Silence only counts when delivery and handler execution
were independently confirmed. Keep experimental behavior visibly opt-in.

Future AI research tooling must be read-only, version-labelled, isolated from
runtime, and able to cite native addresses, upstream commits, fixture offsets
and identified log times. It is not implemented by this cleanup.
