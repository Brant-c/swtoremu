# Stage 0 baseline — 2026-09-30 UTC

Workspace: D:\SWTORClassic\swtoremu. No runtime changes made for this baseline.

The isolated Debug/x86 build of SharpServer/NexusToRServer.csproj succeeded
(exit 0; existing compiler warnings retained in build.log). Output and intermediate
files are confined to this new baseline directory; the installed server is untouched.

Tests used Windows SysWOW64 PowerShell and the freshly built assembly:
- Test-AreaRouting: PASS (exit 0), destinations 8/19, all 11 legacy area packets.
- Test-AreaBlobFraming: PASS (exit 0), 38 bodies.
- Test-AreaWireRoundTrip: PASS (exit 0), 54 fixture packets.
- Test-WorldEntryOffline: FAIL (exit 1), "Opt-in RequestWorldFadeIn gate observer is missing."
  This is a pre-existing source-guard failure before packet modifications, not a native-client test.
- Test-PacketWorkbench: PASS (exit 0).

Full outputs are Test-*.log. launcher-switches.txt records every launcher assignment
and inherited retry default verbatim (not a claim about a running process environment).
Notably CRT3, ability experiments and TRACE_PLAYER_FIELDS are enabled; spawn override
is empty; phase retry is inherited/otherwise disabled. No server/client process was
found during baseline inspection. Do not treat launcher comments as evidence.

dirty-before.txt records all pre-existing dirty and untracked files; tracked-before.patch
preserves the tracked diff. The movement source and project file have explicit before
copies. Existing diagnostics and untracked files remain in place. Relevant dirty files
include ToR.cpp, CRT.cs, CMsg61116AD5.cs, CMsgF96DCDB0.cs, AreaPollExperiment.cs,
startup/replication/reply packets, project file and trace launcher; PhaseExit.cs and
PhaseInstanceRetry.cs were already untracked.

Captured: last-server-full.log has two C5 samples, both 36-byte bodies. The first is
preserved verbatim in movement-source.txt and inspected with PacketWorkbench in
movement-workbench.txt. The 16 bytes after heading/XYZ remain opaque; their field
semantics are unresolved. Other observed variants (including C7) are outside this
session's decoder scope. Offline acceptance does not prove native client acceptance.
