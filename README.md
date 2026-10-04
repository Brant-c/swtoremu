# SWTORClassic emulator research

This fork aims to reconstruct a server for the **April 2012 SWTOR client**.
It derives from [g91/swtoremu](https://github.com/g91/swtoremu), retaining the
original Domo/Emulator Nexus sources and history. The current local runtime is
the C# `SharpServer` implementation. The original C++ `Server` tree remains
important architectural and protocol evidence.

Local world entry, movement and retreat exit/reentry have been demonstrated
with compatibility patches and captured state. General character persistence,
area lifecycle, dynamic replication, quests and combat are incomplete. Taxi
creation and travel have not been demonstrated. See [project state](docs/project-state.md).

## Build and setup

Windows, Visual Studio with MSBuild and the .NET Framework 4.8 targeting pack
are needed for the two active C# executables. From the repository root:

```powershell
.\scripts\Build-Server.ps1
.\scripts\Start-Servers.ps1 -CheckOnly
.\scripts\Start-Servers.ps1
.\scripts\Collect-Logs.ps1
```

The build produces `SharpServer/bin/Debug/NexusToRServer.exe` and
`SharpServer/ShardListServer/bin/Debug/ShardListServer.exe`. Server-only startup
does not launch a client or enable feature experiments. It runs each executable
from its required working directory. The server uses ports 7979, 20060 and
20066; shard-list listens on 443 and 8888. Existing fixtures in
`SharpServer/bin/Debug/AreaServer` are **required data**, despite their location
under a build directory. The shard service also needs `Shards.xml` and its
existing certificate inputs; see the workflow for setup boundaries.

A clean source checkout alone is not a complete client installation. The local
April archives, matching client, hook, compatibility bridge and resource cache
must already be prepared. Do not substitute a modern client as a protocol
baseline. `SWTOR_TOR_ARCHIVES` overrides the repository archive root.
See [research workflow](docs/research-workflow.md) for client experiment boundaries,
log locations and validation. Use `build-hook.cmd` / `test-hook.cmd` only when
working on the existing hook; their toolchain assumptions are in `HOOK-BUILD.md`.

## Maintained documentation

- [Architecture and upstream differences](docs/architecture.md)
- [Capability/dependency map and patches](docs/project-state.md)
- [Build, logs, validation and evidence workflow](docs/research-workflow.md)
- [Cleanup findings and final deliverable](docs/repository-cleanup.md)
- `Diagnostics/CURRENT-PICKUP.md`: single active development checkpoint
- `Diagnostics/Protocol-Evidence.csv`: protocol claim registry

Dated Diagnostics documents are evidence, not competing development directions.
`Archive/RepositoryCleanup-20261004` retains retired root probes and prior
instructions. Do not run archived scripts without rechecking their paths and effects.

## Original notices

Original attribution and README notice are preserved verbatim in
[the pre-cleanup README](Archive/RepositoryCleanup-20261004/before-docs/README.md).
`LICENSE` and file-level notices are unchanged. Their differing terms require
manual review before redistribution; this cleanup makes no licensing determination.
