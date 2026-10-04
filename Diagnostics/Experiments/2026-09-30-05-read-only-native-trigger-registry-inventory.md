# Experiment 2026-09-30-05 — Read-only native trigger registry inventory

## Question

After stable Tython startup, does the April client contain native TriggerNode instances corresponding to the Masters Retreat INSTANCE_GATEWAY and INSTANCE_REGION volumes, including a candidate at gateway position (-63.6168,-6.7343,-126.8847)?

## Existing evidence

Experiment 03 established no selected-room pointer/state change across the
doorway destroy. Experiment 04 established that the `gnarls_new` match belongs
to a generic HeroNode for a dropship dynPlaceable; it is not a room node.

Client asset evidence identifies an `INSTANCE_GATEWAY` at
`(-63.6167984,-6.7343001,-126.8846970)` with parameter
`tyt_jedi_knight_masters_retreat`, plus three associated `INSTANCE_REGION`
volumes. Captured awareness inventories contain 35 `hydTriggerEntity` records
but no replicated engine `TriggerInstance`. Older checkpoints hypothesize that
the missing trigger registry entry prevents `_AttachGatewayTrigger`; this run
must test that hypothesis directly rather than treat it as a conclusion.

Offline PE32 RTTI analysis establishes native `TriggerNode` runtime vtables at
RVA `0x00D613A4`, `0x00D61384`, and `0x00D6116C`. For a module base of
`0x006E0000` these were `0x014413A4`, `0x01441384`, and `0x0144116C`.

## Single variable

Add one external read-only post-startup inventory of allocations containing the
three ASLR-adjusted `TriggerNode` vtables. Save bounded candidate snapshots and
test them for the exact gateway position and known region/trigger coordinates.
No movement, hook change, process write, packet or environment change.

## Exact input

- Pin the frozen control, client and new inventory script before launch.
- Environment switches: unchanged frozen baseline; actual values preserved.
- No packet is added. Existing startup traffic is observation context only.
- RTTI resolver and output:
  `DoorwayControl-20260930/gnarls-native-map/Find-RttiVtables.py` and
  `trigger-rtti-vtables.txt`.
- Required positive target: gateway coordinates
  `(-63.6167984,-6.7343001,-126.8846970)` within a bounded native TriggerNode
  candidate or a reproducible registry structure that owns it.

## Predictions

Positive observation:

- A TriggerNode candidate or its bounded owner contains the gateway coordinates
  and can be distinguished from captured Hydra triggers. This establishes
  client-local materialization and shifts the question to registry timing/state.

Negative observation:

- TriggerNode scanning works and finds other known trigger coordinates, but no
  gateway or region candidate. This supports missing static engine-trigger
  materialization without yet proving its wire representation.

Invalid/inconclusive conditions:

- No positive-control TriggerNode can be identified, object-base offsets remain
  ambiguous, coordinates are transformed rather than stored directly, startup
  is incomplete, or any process write/new packet occurs.

## Evidence to preserve

- Exact script/build/client hashes, module base and resolved runtime vtables.
- All match addresses, virtual-memory regions and bounded candidate snapshots.
- Stable startup server/hook logs and effective switches.
- Coordinate-match report including explicit positive-control outcome.

## Result

PENDING. Static RTTI targets are resolved; the bounded live inventory is not yet
implemented or run.

## Conclusion

- Outcome: pending
- Confidence change: none
- Registry rows updated: none
- Runtime code retained: none; planned observer is external/read-only
- Next single question: if gateway TriggerNode is absent, which captured native
  area-object stream carries static engine triggers on an original server?

