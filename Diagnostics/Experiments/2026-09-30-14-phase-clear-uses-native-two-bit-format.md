# Experiment 2026-09-30-14 — Phase clear uses native two-bit format

Question: does the correctly encoded phase clear enter the local phsPhase branch, complete the phase-exit callback and remove the invisible barrier?

Existing evidence: experiment13 observer installed and independently recognized startup phsPhase change. Exit17 reached the same entity but did not match phsPhase, and operator remained blocked.

Native finding (Client-derived): pinned April PE hash2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494. Class-field reader005AC1A0 switch table005AC65C maps style7 to005AC358, which passes one bit at005AC3D3; style8 maps005AC1DE, passes two bits at005AC27C. Both use005B0EB0. Previous decoder treated both as two-bit and falsely confirmed field25. With the native style7 rule, the old mask actually targets field51 chrCurrentInteraction. Correct style8 targets field25 phsPhase. No assumption of extra notification semantics is needed to establish this mismatch.

Single protocol variable: player clear selector byte changes07 to08. Same selected ID, stream1B502E, structure26, packed zero value, field-state bytes, retained effect update and phase-info removal. Clear remains opt-in, default destroy packet unchanged. No client code or room/collision change.

Exact input: S2C opcode0D446E80, component65B30008, handle8,120bytes. D:\SWTORClassic\swtoremu\Diagnostics\PhaseTransitionAudit-20260930\clear-4000010E218A839B-8.bin; SHA256 E87FD3E57125087E3FE40AEE552C28E5F49EDE34DDFD9F18FA741D5BA9CDFFAF. Byte29 changes07->08; four ID/handle fixture pairs show exactly this difference. Selected runtime ID must be verified; fixture describes839B. ServerSHA256 69358050FFCABCB8F3B59332D4CD73B50B769E95025C52CC3369CBCE42523CF7.

Launcher: Run-SWTORClassic-SelectedPhaseExit.cmd; selected clear1; phase observer1; CRT3off; retrydisabled; lifecycle log-only1. Fresh client/server processes and pinned identity checks required. Load and stand still so installed/startup callback coverage can be checked before walking to barrier.

Positive: doorway entity callback phase-field-matched, local-player-comparison-passed, then PHASE.OnPhasedInstanceUpdated resolves zero new instance and executes exit branches. Visible success additionally requires passing barrier and moving into exterior.

Negative: correct observer coverage but phase-field branch absent, or callback returns unchanged instance. Callback completes yet barrier remains means phase-state correction was insufficient for physical traversal.

Invalid: no installed/startup coverage, inspection failure, mismatched selected identity, missing packet apply proof, duplicate stream.

Validation: native PE dispatch/bitwidth assertions; original versus corrected fixtures interpret51 versus25; independent one/two-bit pattern regression; selected-ID integration; Debug x86 server build; routing, blob framing, wire roundtrip, workbench pass. WorldEntryOffline retains pre-existing failure: Opt-in RequestWorldFadeIn gate observer is missing. Not caused by this one-byte clear change; hook source untouched in this step.

Runtime result pending. Existing server/client logs and observer limits are preserved under SelectedPhaseExit-20260930/live-20260930-220503. Old binary/source/fixtures preserved in PhaseFormat-20260930. No processes launched by preparation.


Experiment14 result:22:21:51 corrected phase field recognized for local player; PHASE resolves no current instance, executes exit and gateway/UI branches, returns. Operator UI confirms leaving phase; invisible barrier persists. Phase-state portion behavior-verified, traversal failed. Evidence PhaseFormat-20260930/live-20260930-222139/RESULTS.md. Client closed. Next collision/contact/controller/room boundary evidence, not another phase-clear/observer repeat. Retain opt-in.
