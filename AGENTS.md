# SWTORClassic development

- Purpose: reconstruct a server for the April 2012 client; preserve upstream
  emulator history and distinguish original code from later fork changes.
- Read `Diagnostics/CURRENT-PICKUP.md`, `Foundation-Audit-20261004.md`, then
  `Protocol-Evidence-Registry.md`. Maintained overview: `README.md` and `docs/`.
  Dated plans/results are evidence, never competing active instructions.
- Active runtime: `SharpServer/`; original C++ architecture: `Server/`.
  Tools: `Tools/Hero`, `Tools/PacketAnalyser`, `Tools/SCPTExtractor`, `Tools/tor_tools`.
  Research/evidence: `Diagnostics/`; retired scripts: `Archive/` (do not run).
- Preserve dirty work, captured fixtures, pinned experiment inputs and local
  entry/movement/retreat controls. Compare significant changes with upstream
  before removing or replacing them. Do not casually modify `swtoremu2`.
- Build: `scripts/Build-Server.ps1`; server-only preflight/start:
  `scripts/Start-Servers.ps1 -CheckOnly`; logs: `scripts/Collect-Logs.ps1`.
  No automatic client launches. Required area fixtures live under `bin/Debug`.
- Protocol work: PacketWorkbench first; use the April native reader/writer and
  local PackedStream reference. Keep framing, bounded decode and gameplay
  separate; failed decode must not execute gameplay. Do not migrate unrelated
  packets, or turn temporary PhaseExit into a general room-transition service.
- Register each protocol claim in `Diagnostics/Protocol-Evidence.csv` with one
  primary level: Captured, Client-derived, Behavior-verified or Hypothesis.
  Use `New-ProtocolExperiment.ps1`; one variable per client run, exact bytes,
  deciding logs and positive/negative predictions before the run. Experiments
  must be opt-in and visibly logged, excluded from default startup until verified.
- Before/after protocol changes run the five checks listed in
  `docs/research-workflow.md` using their documented x86 host/assembly parameters.
  Offline success does not establish native client acceptance.
- No taxi expansion or new AI/MCP layer until review; earliest missing shared
  foundation takes priority. Preserve uncertainty instead of speculative rewrites.
