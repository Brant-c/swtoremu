# MessageHeaders and C++ reference follow-up

The user highlighted `Packets/MessageHeaders`, which is relevant and has been
used by earlier work: `Diagnostics/Decode-Style7Replication.py` explicitly uses
`base_gom_update.h`, and `WorldEntry-Handshake-Findings.md` references both the
headers and C++ world-server implementation for startup analysis.

The previous comparison covered the C# legacy server and parser in swtoremu2.
Its finding that all 48 C# symbolic opcode names are retained is accurate but
does not mean the current logs use every better name in the C++ reference.
In particular `Server/Framework/Src/Network/Packet.h:50` identifies
`0x61116AD5` as `CMSG_CHARACTER_SYNC`. Current logs retain CMsg61116AD5.
This is a known-name presentation gap, not an unknown numeric opcode.
No C++ CharacterSync handler was found in the searched Server source.

Reviewed headers:

- `msg_player_move_state.h`: heading, move vector, end position and conditional
  transaction/time/platform fields selected by a uint16 mask, with padding.
  This is useful format evidence, but it does not declare its numeric opcode.
  Its width/order must be compared with actual April packets before changing
  the existing bounded C5 decoder; don't silently equate layouts by name.
- `msg_area_hack_pack.h`: four-u32 records, all named Unknown, with a fixed
  54-record array. The Tython legacy capture discussed in earlier work has
  35 records. The header is not an unconditional April/Tython count contract.
- `msg_0x7cb9a193.h`: envelope plus an opaque length-prefixed byte payload,
  without a semantic decode of that payload.
- `msg_client_request_rpc_1.h` and `_2.h`: envelope plus request byte vector,
  without mapping numeric opcodes or decoding script selector/arguments.
- `base_gom_update.h`: contract and object updates, parent references, field
  data, removal-list framing; several fields remain unknown/opaque.
- `msg_area_client_replication_transaction.h`, `msg_area_awareness_entered.h`
  and `msg_awareness_exited.h`: useful existing container/envelope layouts.
- `msg_set_character_rendezvous_point.h`: typed fields but mostly unknown
  meaning, agreeing with the existing rendezvous-point shape under study.

Knowing the envelope and field order is distinct from knowing the required
values, creation order, room references, and runtime transitions. The latest
client trace is aimed at those inputs. These findings do not establish a
missing opcode, a valid exterior stream or a packet that should be sent next.
Keep the existing headers as format references; do not reinvent them.
