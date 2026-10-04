# Doorway room-state rerun results — 2026-09-30

## Identity and control

- Frozen server SHA256:
  `FF454DC4CCAE09980DF558FC214CA85188605B3CA9433655DEBC0D6F12926880`.
- Rerun identity manifest SHA256:
  `CAA7F3E3F1E48C05E994812E639D70784C9BF8AA491EE5AA01C0F43F3AFCAE05`;
  all 54 pinned inputs passed launch validation.
- Effective-switch file SHA256:
  `214E70FB419ED4481A4184446B1E800233F3E0065E68B9A9FCE8594C1FF30BC1`.
- Runtime protocol behavior was unchanged from experiment 01. The only added
  variable was the external read-only 20 ms observer.

## Crossing and packet evidence

`movement.csv` records three accepted C5 samples:

| Server log time | X | Y | Z | Detector crossing |
|---|---:|---:|---:|---|
| 00:23:32 | -64.8741 | -6.906221 | -127.6710 | no |
| 00:23:54 | -62.95565 | -6.898841 | -126.2381 | yes |
| 00:23:54 | -62.95174 | -6.898841 | -126.2342 | no |

The decoder rejected every observed C7 packet before gameplay behavior. At the
accepted crossing the server emitted one 46-byte `0x0D446E80` transaction,
stream `0x001B502E`, removing node `0x1AC6F6DC1F`. The exact plaintext is
`phase-destroy.bin`, SHA256
`2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF`.
PacketWorkbench identifies it as a captured-confidence S2C Area
ClientReplicationTransaction. The hook independently logged parsed opcode
`0x0D446E80`, `CrtApplyHook` count 18 entry, and its applied return at 00:23:54.
This is generic apply-route proof; the hook does not identify the removed node.

The server logged CRT18 suppression. No new outbound packet, phase-instance
retry, awareness resend or room activation was introduced.

## Native timeline

The observer attached to PID 45972 with module base `0x006E0000`. It detected
multiple pointer and lifecycle changes during initial startup, including the
primary pointer becoming `0xD2C14500` and the secondary becoming `0xD2C15500`.
Both reached state/aux `3/6` before the doorway attempt.

From 00:23:48 through 00:25:47, spanning the 00:23:54 destroy and crossing, all
observed values remained constant:

| Field | Value |
|---|---|
| Area root | `0xF41439A0`, state/aux `3/6` |
| Primary (`area+0x2A0`) | `0xD2C14500`, state/aux `3/6` |
| Secondary (`area+0x400`) | `0xD2C15500`, state/aux `3/6` |
| Tree begin (`area+0x3E0`) | `0xD2B64E70` |

The observer sampled every 20 ms, emitted a row on signature changes and a
one-second heartbeat. There was no signature change at or after the crossing.
When the client closed at 00:25:48, the observer recorded the global area
pointer becoming null and ended cleanly at 00:25:50.
`native-changes.csv` and `native-crossing-window.csv` preserve the compact
evidence; `timeline-live.csv` is the while-open snapshot and
`timeline-final.csv` contains the clean observer end.

The startup awareness payload at 00:23:31 contains `gnarls_new` inside the
dynPlaceable record for node `0x1AC6F6DC94`: its only occurrence is at fixture
offset `0x51`, within that record's `0x006..0x148` bounds. The offline awareness inventory is
preserved in `awareness-inventory.txt`. This proves the startup bytes name that
object before the crossing. It does not prove the corresponding room or
collision became selected or resident.

## Visible result and conclusion

The operator reported no behavior change: the character remained blocked, with
no observed loading-state, location-text, rendering or collision transition.

For this control, phase-info destruction did not produce a transition in the
two client-selected native object pointers or their observed lifecycle fields.
This falsifies the phase-destroy-only selected-room-transition hypothesis for
these fields. It does not identify the missing lifecycle event and does not
justify emitting CRT18 or another guessed packet.

The next evidence-producing step is to identify which startup native objects
correspond to the `gnarls_new` awareness object, the two selected pointers and
the doorway collision owner. That mapping should be obtained read-only before
testing any outbound lifecycle message.
