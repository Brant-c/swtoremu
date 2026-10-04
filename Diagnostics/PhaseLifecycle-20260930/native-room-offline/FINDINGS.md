# Offline native room path — 2026-09-30

No client run, process memory scan, runtime edit or packet send occurred.
The script catalogue `_JPEXTRACT/Scriptdef.listdump.csv` was reviewed and
relevant rows preserved in `script-targets.csv`. Both `_BaseClientClassMethods`
and `sysBaseClientClassMethods` are already extracted. No additional JP export
is required for the current native-code trace.

## Verified input and limits

The executable is the same April client used in the controlled runs, SHA-256
`2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494`.
`Trace-NativeRoomOffline.py` saves bounded excerpts of the existing dumpbin
listing and checks every printed instruction-byte prefix in these excerpts
against the current PE bytes. `summary.json` records the number checked.
This is not a fresh independent instruction-boundary decode; omitted continued
bytes are not checked. Direct-call inventory omits indirect callers.

## Client-derived path

1. Native VA `0x00B91AE0` compares its argument against area `+0x298` and
   returns without the change path when equal. On a change it sets dirty flag
   `0x012E393F`, stores the argument at `+0x298` and global `0x014927B0`, and
   calls `0x00B8F5E0`. It contains the `_Room_Transition` script label at
   `0x010BFC84`, independently read as UTF-16 from the executable.
2. `0x00B8F5E0` uses area `+0x298`, calls `0x00B7A040`, resolves a returned
   environment-scheme object/name through `0x007A8770` and area lookup `0x00B8C5A0`, and chooses
   either that collection object or the fallback at `+0x3FC`. It stores the
   choice at area `+0x400` (`0x00B8F6FA`). If requested by its Boolean argument,
   it calls activation `0x00B7C390` for the choice (`0x00B8F779`).
   A later parser trace identifies the input reference as EnviroScheme; this
   path must not be treated as selecting the physical destination by itself.
3. `0x00B7C390` takes different paths depending on object `+0x8C` and `+0x90`.
   With `+0x90 == 6`, it calls `0x00B7AF50`, writes `+0x8C = 3`, calls
   `0x00B79C30`, and conditionally dispatches the `_Room_Activate` label.
   With another auxiliary state it records deferred flags at `+0x26A..+0x26C`.
   The label being dispatched locally does not justify a server RPC.
4. The dirty area collection loop at `0x0071C610` checks `+0x2A0`, global
   `0x014927B0`, a selected object's collection, and `+0x400`; it chooses
   activation `0x00B7C390` or deactivation `0x00B7C8B0` by object state.
5. Selection has multiple callers. The entity path at `0x006DF3D1` passes the
   entity-associated pointer from `+0x98` when the entity is global
   `0x01495F64` and a virtual condition permits it. The position-query path
   at `0x00B925F7` chooses an area collection object after testing the input
   with `0x00B7B010`; that test reads three floats and uses object `+0xC0`.
   These are evidence of local selection inputs, not proof of live execution
   at the blocked doorway or a complete movement path.

## Important distinction from earlier diagnostics

Area `+0x298` is a separate pointer used by the change routine. Earlier room
timeline samples focused on `+0x2A0` and `+0x400`; they do not establish that
the `+0x298` selection input is correct or that its assignment path runs.
Registration at `0x00B90DCD` writes `+0x2A0` when a name comparison matches
`_everywhere_` (UTF-16 at `0x01158040`). Treating that pointer as the current
destination room without further qualification would be unsupported.

## Next exact question

Correction from the next offline audit: `0x00B7A040` copies reference `+0x1BC`
or obtains a fallback through `0x00B8D0F0`. The room-settings parser compares
the key with UTF-16 `EnviroScheme` at VA `0x0115A950`, then calls setter
`0x00B79F70`, which stores that reference at `+0x1BC`. The fallback uses the
name `Area` at VA `0x010BDCE0`. This is an environment-scheme input, not a
proven adjacent-room destination reference. Prior wording "related room" was
premature. See `../startup-order-audit/FINDINGS.md` for authored portal links.

Trace how the player's entity `+0x98` room association is assigned and reaches
area selection `+0x298`. Check the readiness/asset path
which brings the candidate to auxiliary state 6. A missing local selection,
unresolved related room, or not-ready content remain distinct possibilities.
None is established by the two doorway runs. Do not infer a missing network
message or fabricate room data from these addresses.

Before the next live request, prepare a small log-only check of this exact
native selection/readiness path if static evidence cannot distinguish it.
It must log bounded events, not scan or dump memory; existing callback/wall
runs should not be repeated without that new target.
