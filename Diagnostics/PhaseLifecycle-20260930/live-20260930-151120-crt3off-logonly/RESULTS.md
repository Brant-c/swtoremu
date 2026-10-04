# CRT3-off doorway result — 2026-09-30 Toronto

Operator loaded Tython, stood still for configuration verification, then walked
once into the green exit and reported: "walked to wall ran into it for a second
and still stuck". The wall persists. No runtime changes or external memory
observer were used during the run.

## Decisive evidence

- Fresh desktop launch 15:11:20; server PID 20116, hooked client PID 20248.
  Server SHA-256 `1931A175025884E2E790363F7EEACEA096FAB3B8C9D41E3C273F426DE706A356`;
  hook SHA-256 `258C834F1A524F039CF96D74EBDED5650A9AA3FE1166759C808CE961AE1A3D36`.
  These match the CRT3-on baseline. The previously verified effective switch
  comparison differs only in CRT3=0 versus 1; retry is disabled.
- CRT3 explicitly suppressed at 15:14:36. No CRT3 fixture emission or named
  player-phase-data create/destroy callback was recorded in the saved logs.
  Four method hooks installed at 15:14:36; area startup completed 15:14:37.
  The operator independently confirmed a rendered world and walking.
- At 15:19:43 the server accepted doorway movement `-64.87 -> -62.94`, emitted
  one 46-byte destroy for node `0x1AC6F6DC1F` on stream `0x001B502E`, and
  explicitly suppressed CRT18. The destroy has SHA-256
  `2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF`.
  PacketWorkbench reports zero byte differences from the CRT3-on destroy.
- At 15:19:43 generic CRT apply 17 brackets named
  `phsPhaseInfo.OnReplicationNodeDestroy` entry and return, argument
  `0x001B502E`, destroyDepth=1. The generic apply then returns. Apply count 17
  versus baseline 18 is consistent with omitting one startup transaction;
  it is not a different doorway packet.
- No nested `phsOracle.UpdateGatewayForInstance` call was recorded. This hook
  logs only calls while phase-info destroy depth is positive; the absence
  claim does not cover unrelated gateway activity.

## Controlled comparison and conclusion

Both runs enter a rendered, movable Tython, apply the identical doorway destroy,
enter and return from the named phase-info destroy callback, record no nested
gateway update, and remain blocked at the wall. The observable startup change
is omission of CRT3 and its named player-phase-data create callback.

Reconstructed CRT3 is not required for usable startup under these specific
settings. Disabling it does not resolve the wall or change the observed
doorway callback/gateway behavior. This weakens CRT3 as the cause of this wall;
it does not prove equivalent global phase state, parent lookup membership,
node removal, trigger state, or native room residency. Phase banner/state was
not separately reported. The destroy callback's conditional branch remains
unresolved; missing native exterior content streaming remains a working
hypothesis, not a demonstrated packet identity.

## Preservation and next work

Full text logs and hashes:
`../../DoorwayControl-20260930/phase-lifecycle-crt3off-blocked-20260930-152018-571/`.
This directory holds startup gates/settings/identity, CRT inventory, named
events, crossing windows, counts, exact destroy and workbench comparison.
No additional offline test is required because this run changed configuration
only and the packet comparison passed. No guessed packets are justified.

The CRT3 comparison is complete. Do not repeat it or request another client run
without a new concrete evidence target. Next work is static analysis of the
April gateway/room-content path and existing evidence, using the established
tools; avoid reopening external memory observer preparation.
