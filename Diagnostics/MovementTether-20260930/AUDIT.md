# Movement tether and retreat membership repair

## Evidence
Captured CRT4 player structure26 field200 (Float, ID4611686254510860000) is the movement tether leash length; field206 (Vector3, ID4611686332315960095) is its anchor. Both are the final present fields in this record. Read their final16 value bytes without guessing offsets through preceding nested containers. Tail offset1287; exact bytes in captured-tether-tail.bin and JSON.
Leash=2.4000000953674316; anchor=[-64.87409973144531, -6.90622091293335, -127.6709976196289]. Logged stop=[-62.9151, -6.8988, -126.2866]; horizontal distance=2.398799015556943. This matches the2.4-unit limit to rounding, but live acceptance of refresh remains unverified.
Jedipedia reader client.gom Fields filter MovementTether confirms IDs/types and shared client/server DOM. Extracted sysBaseCharControlClassMethods GetMovementLeashingInfo lines770-783 returns enabled=not chrPlayerCharacter_IsFollowingTarget, anchor and length for player characters. Script id14988199741616540456 per Scriptdef.listdump.csv. Reader direct script opening did not resolve in this turn; do not claim its code was freshly read there.
Pinned April native737120 calls739D80 before737520. 739D80 resolves UTF16 GetMovementLeashingInfo at11520BC, checks enabled, compares proposed horizontal distance from anchor to squared leash, and restores previous X/Z through6D5D60 at739F8D if outside and moved. Subsequent7B7450 can therefore report clear after the limiting position was already restored. Verified bounded disassembly remains PlayerMovement-20260930/player-behavior-native.txt and verification-output.txt.
6D5FB0 (CharacterNode primary vtable1151154 slotCC) adds desired displacement through6CBFD0; generic absolute setter6D5D60 writes transform and calls slot74->799340. Neither alone proves the limiting cause.
Operator clarifies invisible barrier is beyond green gateway, always traversable. Phase exit/UI/tutorial already work. Inward gateway crossing at end did not restore membership; old PhaseExit is explicitly one-shot.

## Implementation
PlayerMovementState is per connection, weakly held, gated to started Tython sessions with selected character, attached area service and finite decoded coordinates. Anchor field206 alone refreshes at most every250ms; captured2.4 leash retained. CMsg61116AD5 C5/C7 decoding rejects non-finite heading/position before gameplay. These coordinates are decoded client reports, not a new authoritative movement simulation.
Post-startup stream IDs share existing ability allocator. Opt-in anchor mode makes original phase-exit removal allocate from the same sequence; defaults retain prior baseline.
Separate SWTOR_PHASE_REENTRY mode uses per-connection state and hysteresis: outward X=-63.0, inward X=-63.65, corridorY(-8,-5),Z(-130,-124). These detector bounds are a temporary heuristic, not complete trigger-volume geometry. It creates only captured phase-info0x1AC6F6DC1F, parent0x1AC688C97E, structure75, remapping player refs. In the same transaction, creation precedes player field25 restore. Never replays world/awareness/CRT18; ordinary physical collision unchanged.

## Verification
Debug/x86 server builds successfully; SHA256=5277D1037C36EFD58D7E8E77855EEC8BB0601B21102FEF62105AE3CCDAABBC0B. Tests passed: area routing,38 blob bodies,54 raw-deflate packets, packet workbench. WorldEntryOffline retains known failure: Opt-in RequestWorldFadeIn gate observer is missing. Eight custom packets verified exact consumption, only selected fields206/25, both character identities and area handles8/19, unique stream IDs and byte-exact captured phase-info recreation. Non-finite anchor rejected. packet-verification.json and Test-Packets.ps1 contain evidence.
Both new launchers VerifyOnly pass in fresh environments. Prior diagnostic manifest preserved; new manifests pin new server, relevant source and launcher. No client or server launched by agent.

## First manual run
Run-SWTORClassic-MovementTether.cmd enables only anchor refresh; reentry0, new collision diagnostic0, CRT3off/retryoff and confirmed phase-clear baseline retained. Walk through gateway beyond old2.4 boundary. Required server evidence MovementTether EXPERIMENT then visible free exterior movement. Reentry prepared separately in Run-SWTORClassic-RetreatReentry.cmd, to be tested after anchor verification. A failed/missing anchor update or unrelated decode error is inconclusive, not evidence refresh failed at the client.


## 2026-10-01: movement tether behavior verified
Operator passed former barrier with anchor refresh enabled. Full small live logs preserved in MovementTether-20260930/prelaunch-20261001-001118-779; see RESULTS.md and movement-summary.json. Phase exit logged00:02:19. Next: close client and servers, manually run Run-SWTORClassic-RetreatReentry.cmd; walk out beyond old boundary and return through gateway to verify phase UI restoration. Reentry remains pending; do not claim complete gameplay.
