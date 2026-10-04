# Phase exit development plan

Latest active checkpoint (2026-09-30): read
`PhaseLifecycle-20260930/CURRENT-CHECKPOINT.md` first. A valid CRT3-on log-only
crossing established named destroy callback entry/return, no nested gateway
update recorded, and wall persistence. The CRT3-off comparison is complete:
usable startup, identical doorway destroy and named callback entry/return,
no nested gateway recorded, wall persists. Read
`PhaseLifecycle-20260930/live-20260930-151120-crt3off-logonly/RESULTS.md`.
Experiment08 completed: client selected gnarls_new and its activation routine
returned, while wall persisted. Read RoomSelection-20260930/live-20260930-163405/RESULTS.md.
Experiment09 completed: identified retreat regions/gateway had collision and
association bits clear across exterior selection; wall persists. Read
TriggerCollision-20260930/live-20260930-172807/RESULTS.md. Next offline target:
April C7 movement schema; user reported decoder rejection, raw fixtures saved.

## Purpose

Continue development toward the immediate playable result:

> The player can leave the Masters' Retreat through the visible doorway, enter
> `gnarls_new`, and continue moving in a correctly loaded exterior room.

Packet-decoder cleanup supports this goal. It is not a separate rewrite and
must not delay the next evidence-producing client run.

This document is intended to be sufficient for a new development instance.
Do not depend on chat history. Treat older handoffs as evidence sources, not as
authoritative instructions when they conflict with this plan.

## Current established state

1. World entry renders and the character can move.
2. Phase membership is present early enough for the client to display the
   story-area banner and owner information.
3. Crossing the doorway can be detected from `CMsg61116AD5` movement updates.
4. Destroying the player's `phsPhaseInfo` child is delivered and applied, but
   it does not open the invisible wall.
5. Re-sending awareness or replication creation batches is not room streaming;
   these batches are non-idempotent and can produce duplicate-character errors.
6. `_Room_Activate` is a server-only script method, not a client RPC.
7. Experiment08 verified native selection of gnarls_new and activation call
   return while the wall persists. Full content/collision readiness remains
   unresolved; missing streaming is a hypothesis, not a proven cause.
8. The later claim that an `InstanceCreated` or `AssetCreated` message is the
   missing "notify area of new player" packet is unverified. Do not implement
   either message on that assumption alone.
9. `PhaseExit.SendRoomStream()` currently describes a desired CRT18 fixture;
   it does not prove that an `.acrt` replication fixture is the native room
   stream or that such a fixture has been captured.

Primary evidence:

- `Diagnostics/PhaseExit-Checkpoint-20260928.md`
- `Diagnostics/Phase-Mechanics-20260928.md`
- `Diagnostics/Handover-20260929-Notify.md` (use its dispatcher findings, but
  retain its own warning that the notify-message identity is unverified)
- `Diagnostics/RoomStreaming-Plan-20260928.md`

## Working rules

### Evidence labels

Every new protocol claim must be labelled in code or notes as one of:

- **Captured**: byte layout observed in a known client/server capture.
- **Client-derived**: read/write order recovered from a native client handler.
- **Behavior-verified**: exercised in the April client with the predicted result.
- **Hypothesis**: plausible but not yet established.

Do not promote a hypothesis into the default startup bundle. Experimental
messages must remain opt-in and must log their exact bytes and reason.

### One-variable runs

Each client run changes one protocol variable. Before the run, record:

- the question;
- the exact packet or hook change;
- the expected positive observation;
- the expected negative observation;
- the log files that will decide the result.

After the run, preserve the logs and write the result before making another
change. A lack of response is only evidence when delivery and handler execution
were independently confirmed.

### Reference priority

Use sources in this order:

1. A production capture with known behavior.
2. Native April client send/receive-handler disassembly.
3. The known opcode table in `Server/Framework/Src/Network/Packet.h`, confirmed
   against the client dispatcher where practical.
4. Extracted scripts, GOM data, and area assets for semantic meaning.
5. Hypothesis.

`D:\SWTORClassic\assettest\resources` is extracted content/GOM/script data. It
is useful for room, trigger, class, and asset relationships, but it does not by
itself define the network wire format.

## Execution plan

### Stage 0 — preserve and baseline

Goal: establish a repeatable starting state without changing runtime behavior.

1. Inspect `git status` and preserve all existing uncommitted work. Do not
   clean, reset, or overwrite files from prior sessions.
2. Record the active environment switches in
   `Run-SWTORClassic-Trace-Tython.cmd`.
3. Run the existing offline checks before modifying packet code:

   - `Diagnostics/Test-AreaRouting.ps1`
   - `Diagnostics/Test-AreaBlobFraming.ps1`
   - `Diagnostics/Test-AreaWireRoundTrip.ps1`
   - `Diagnostics/Test-WorldEntryOffline.ps1`

   Follow each script's x86 PowerShell and assembly-path requirements.
4. Save the baseline pass/fail results. Do not treat the offline checks as
   proof of native client acceptance; several explicitly test only framing or
   fixture preservation.

Deliverable: a short dated baseline note containing the build result, test
results, active switches, and known dirty files relevant to phase exit.

### Stage 1 — make packet experiments trustworthy

Goal: add the minimum shared decoding structure needed for reliable phase-exit
work. Do not redesign every packet.

1. Fix the inbound execution contract:

   - `TORGamePacketHandler` must call `Run()` only when `Read()` succeeds.
   - A rejected decode must log opcode, component, total length, cursor offset,
     and failure reason without executing gameplay behavior.

2. Add a bounded payload cursor for experimental area messages. It needs:

   - little-endian fixed integers and floats;
   - remaining-byte checks;
   - Hero packed unsigned and signed values;
   - a non-throwing `TryRead` result that reports the failing offset;
   - an explicit end-of-message check.

3. Add one shared routed-message envelope representation:

   - opcode;
   - source and destination handles;
   - body slice;
   - original bytes for logging.

4. Move only the parsing needed by the active investigation into typed
   decoders:

   - `CMsg61116AD5` movement variant;
   - `CMsgF96DCDB0` RPC envelope and selector;
   - ability variants may continue to use their current services, but their
     parser should consume the shared cursor rather than duplicate packed-value
     logic.

5. Add captured-byte regression tests for valid, truncated, wrong-selector,
   and trailing-byte inputs. Keep these compatible with the legacy x86 build;
   extending the existing PowerShell reflection tests is acceptable.

Acceptance gate:

- Existing valid movement and RPC samples decode identically.
- Truncated samples cannot reach `PhaseExit.OnMove`, ability handling, or reply
  generation.
- No startup packet order or serialized server packet changes.

### Stage 2 — prove the actual transition boundary

Goal: determine whether the doorway failure occurs before or after the native
client requests/accepts an area transition.

1. Establish a clean movement timeline around the doorway:

   - decoded position and timestamp;
   - inside-to-outside crossing;
   - phase-info destroy send and client application;
   - all inbound and outbound opcodes within a narrow time window;
   - loading-state changes;
   - room/collision instrumentation already available in the hook.

2. Run a control crossing with no new experimental packet. This becomes the
   reference trace.
3. Confirm whether the client emits any message specifically at crossing.
   Previous runs found no consistently correlated phase-gateway RPC; reproduce
   that conclusion using the typed timeline rather than raw log inspection.
4. Trace the native loading-state transition associated with
   "Waiting for server to notify area of new player":

   - locate writes, not merely reads, to the state field;
   - identify the exact handler or callback that advances it;
   - recover that handler's complete wire read order;
   - map its opcode through the client dispatcher or the known opcode table.

Do not send `AssetCreated`, `InstanceCreated`, or `SendToArea` merely because a
name appears nearby. First prove that the candidate handler writes the relevant
state or initiates the missing room load.

Decision gate:

- If a specific message is proven to advance the state, proceed to Stage 3A.
- If no message gates it and native room residency remains missing, proceed to
  Stage 3B.

### Stage 3A — implement a proven transition message

Use this branch only after Stage 2 identifies an exact message and layout.

1. Create a typed server packet with opcode sourced from the known table.
2. Encode the body in the exact order read by the April client handler.
3. Add a byte-exact serializer test.
4. Send it behind a single opt-in switch at the correct lifecycle point.
5. Verify in the client:

   - handler execution;
   - loading-state advancement;
   - room/collision residency;
   - ability to cross the doorway.

Only make it default after behavior verification. Remove the opt-in only when
the message is shown to be part of the normal transition rather than a bypass.

### Stage 3B — recover and reproduce room streaming

This is the current expected branch.

1. Determine what the live server sends when a player gains an adjacent room.
   Prefer an existing production capture. If none exists, use native client
   handler tracing to identify the object-stream receiver invoked during room
   residency changes.
2. Separate these concepts explicitly:

   - replicated GOM gameplay nodes (`.acrt`);
   - awareness creation sets (`.aaw`);
   - static area/room asset data (`.dat`, `.mag`, collision);
   - native room/object update stream;
   - lifecycle notification that commits the stream.

3. Recover the smallest complete transition into `gnarls_new`:

   - stream/open message;
   - room identifier and instance identifier;
   - payload chunks or referenced assets;
   - completion/commit message;
   - ordering relative to awareness and character movement.

4. Build a typed `RoomTransition` service rather than adding more behavior to
   `PhaseExit.cs`. It should own stream IDs, transition state, ordering, and
   duplicate suppression.
5. Keep `PhaseExit` responsible only for detecting the temporary doorway
   crossing until a real trigger system exists. It should request a room
   transition and phase-membership change through services, not assemble wire
   blobs itself.
6. Test first with one adjacent room and one character. Generalize only after
   the Masters' Retreat → `gnarls_new` transition works.

Acceptance gate:

- The client makes the destination room resident.
- Collision beyond the doorway is loaded and traversable.
- No duplicate-character or duplicate-node errors occur.
- Repeated in/out crossings do not resend non-idempotent creation sets.

### Stage 4 — replace the phase-exit approximation

Goal: convert the successful one-off into the first reusable world-streaming
path.

1. Introduce per-client area state:

   - current area and room;
   - resident rooms;
   - pending transition;
   - active awareness/object sets;
   - issued stream IDs.

2. Move the doorway coordinates and room relationship out of hard-coded packet
   logic. Derive them from area data where possible.
3. Make phase membership and room residency independent state machines. Leaving
   a phase may coincide with entering a room, but they are not the same wire
   operation.
4. Remove or archive disproven runtime experiments after preserving their
   evidence in diagnostics:

   - `_Room_Activate` client RPC builder;
   - awareness resend path;
   - any unverified AssetCreated/InstanceCreated experiment;
   - stale duplicate-instance probe behavior.

### Stage 5 — completion validation

The main goal is complete only when a fresh run demonstrates:

1. Character enters the Masters' Retreat normally.
2. Story-area phase UI and ownership are correct.
3. Walking through the exit changes phase membership once.
4. `gnarls_new` becomes resident without client serialization errors.
5. The invisible wall is gone and the character can move into the exterior.
6. Walking back and exiting again does not corrupt state or duplicate objects.
7. Existing repository, character-selection, world-entry, area-routing, and
   packet-framing offline checks still pass.

Preserve the successful server log, hook log, active environment, relevant
packet hex, and fixture hashes in a final dated checkpoint.

## Suggested code boundaries

Keep the implementation small and compatible with the existing project:

```text
SharpServer/NET/Protocol/
  PacketCursor.cs          bounded primitive and Hero packed-value reads
  RoutedMessage.cs         opcode/component/body envelope
  RpcEnvelope.cs           selector and typed argument decoding

SharpServer/AreaServer/
  RoomTransition.cs        transition state and message ordering
  PhaseMembership.cs       phase-info create/destroy lifecycle
  PhaseExit.cs             temporary crossing detector only
```

Do not migrate unrelated login, repository, character-selection, or mail
packets during this work.

## First concrete work session

A new instance should begin with this bounded task:

1. Produce the Stage 0 baseline note.
2. Change the handler so failed packet reads cannot execute.
3. Add the bounded cursor and tests.
4. Convert only `CMsg61116AD5` movement decoding to the cursor.
5. Verify all existing offline tests still pass.
6. Perform one unchanged control client run and preserve the doorway timeline.

Stop there and evaluate the evidence before selecting Stage 3A or 3B. This
delivers a safer decoder immediately while keeping every change directly tied
to proving and implementing the phase exit.



## 2026-10-01: Tython retreat baseline accepted
User reports gateway timing better. Saved full small logs RetreatGateway-20261001/prelaunch-20261001-003805-442 confirm exit/entry/exit, corresponding callbacks resolve None/retreat/None. Combined with runs16/17: movement past old tether barrier and repeated retreat phase membership work. Use Run-SWTORClassic-RetreatGateway.cmd as known-good opt-in baseline; preserve runtime identities. Local phase work can move to Weller conversation/story interaction and exterior NPC replication, per user goal. General phase/group/quest trigger engine remains separate scope; do not claim it implemented.
