# Next target after the completed CRT3 comparison

Both controlled runs remain blocked. Do not repeat this comparison or restart
the client for preparation alone.

## Script boundary

`_JPEXTRACT/phsPhaseInfoClassMethods.txt:70` resolves the parent through
GetParentOfNode, tests parent lookup membership, clears join overrides, and
conditionally calls UpdateGatewayForInstance when the local player resolves.
The live callback logs do not identify which of these branches executed.

`_JPEXTRACT/phsOracleClassMethods.txt:318` resolves the phased instance and
evaluates eligibility. Its `_SetGatewayState` function updates portal effects
and writes the Collidable property of already cached triggers when collision
state changes. This extracted body does not establish a native room-loading
operation or a packet to send.

Older narrative claims that the wall is definitively a room boundary or that
trigger absence was proved must not replace the newer evidence limits. Neither
wall cause nor parent/lookup/trigger state is established by the CRT3 comparison.

## Concrete offline work

Start from the pinned April executable and the existing client-derived native
analysis in `../DoorwayControl-20260930/Native-Room-State-Analysis.md`:

- Follow the area collection loop at VA 0x0071C610 and its activation/deactivation
  callees; distinguish selection, asset readiness and collision installation.
- Trace writers and upstream callers for area selected-object pointers +0x2A0
  and +0x400. Establish how a destination room enters the selected collection.
- Cross-check state transitions at 0x00B7AED0, 0x00B7AF50, 0x00B7B940 and
  0x00B7C390 against their callers and existing resource/packet dispatch evidence.

Deliverable before another live request: an exact native call path, with
executable hash, disassembly references and unresolved inputs stated, showing
what selects/loads adjacent exterior content or what prerequisite blocks it.
Only then choose one minimal implementation or a bounded client-log event
that distinguishes the remaining alternatives. No external memory scans,
fabricated triggers, guessed CRT18 or guessed notification packets.
