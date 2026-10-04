# Experiment 2026-09-30-13 — Corrected phase callback address

Question: does the client process the selected character's phase change and complete its exit path?

Existing evidence: experiment12 hit the generic replication apply path but the operator remained at an invisible barrier. Its phase-update observer failed validation, so character phase application was unobserved.

Single variable: correct passive callback observation. Packet behavior remains the experiment12 selected-player clear, CRT3 off, retries off. No collision changes or added transfer messages.

Offline defect: pinned oracle payload GUI method32E3 minus OnPhasedInstanceUpdated25C3 is D20, not720. The previous address was wrong. Generated constant now derives the difference. Regression rejects the old address and corrupt prefixes, validates the callback epilogue and both helper relocations at two load bases. This does not establish the exact old live failure condition, because old logs lacked per-check results.

Input: Run-SWTORClassic-SelectedPhaseExit.cmd; identity.csv pins source/build/launcher inputs. Observer opt-in SWTOR_TRACE_PHASE_UPDATE=1; selected phase clear=1; CRT3=0; lifecycle log-only=1; retry disabled. DLL SHA256 CAD8FCADECE1A8E4349C6C48819D65326C003864A680E186355D287739F19328.

Wire input: S2C AreaClientReplicationTransaction opcode0D446E80, handle8, component65B30008, stream1B502E. Selected839B clear fixture D:\SWTORClassic\swtoremu\Diagnostics\PhaseTransitionAudit-20260930\clear-4000010E218A839B-8.bin; 120bytes SHA256 3A85682CF66160953CBEE04DEC2A232E69E11B58204C0010AA083A10AD3D79DF. Actual selected identity must be recorded for a fresh run; fixture only applies to839B. Server is unchanged.

Procedure: load and stand still. Verify PhaseUpdateHook validation oraclePrefix=1 oracleEnd=1 nativePrefix=1, both helper targets equal expectedTrack, followed by installed. Then approach the barrier once, stop, preserve bounded logs. Do not treat readiness call=enter as story phase entry.

Positive character-state evidence: phase-field-matched plus local-player-comparison-passed, then PHASE.OnPhasedInstanceUpdated and exit checkpoints with newInstanceNameID=0, old-instance exit and exit-gateway branch. These are script-derived state observations, not a separately decoded raw field-storage read.

Negative/diagnostic outcomes: field matched but local equality failed; field callback with still-valid phase info; instance-unchanged-early-return. Name-ID checkpoint and timestamps distinguish old membership from normal periodic calls. No field callback despite confirmed delivery is inconclusive unless coverage was independently exercised during startup.

Invalid: no installed marker or failed checkpoint inspection, mismatched selected identity, missing apply proof, or callback coverage never independently observed. Standstill can validate installation and startup coverage, not guarantee the later callback will execute. Optional validation failure logs details and leaves existing lifecycle hooks eligible.

Visible success requires walking into gnarls_new; callback success alone is insufficient. If exit path completes and barrier remains, next investigate the actual blocking contact/controller rather than repeat phase guesses.

Validation: pinned resource/helper verification, relocated-address regression, existing lifecycle signatures, Release Win32 build pass. Runtime result pending; no processes started by this work.

Deferred execution coverage: executing entity method discovery and checkpoints no longer require CRT depth>0. Exact method bytes still determine identity, and depth remains logged as context. This avoids excluding script notifications that run after packet apply returns. No memory search or extra dump added. Final Win32 rebuild passes.

Live evidence22:05:03 installation/startup coverage confirmed. At doorway22:05:35 same selected entity receives update callback but phsPhase-changed branch and oracle callback absent, while named phase-info destroy returns. See Diagnostics/SelectedPhaseExit-20260930/live-20260930-220503/RESULTS.md. Character phase exit not confirmed; decoded raw storage not yet available. Visible outcome pending.

Operator outcome: Still blocked. Observer repair confirmed; visible exit failed. Phase-field notification branch absent at doorway despite startup coverage.
