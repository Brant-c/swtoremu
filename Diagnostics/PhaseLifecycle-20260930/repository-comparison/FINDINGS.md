# Relevant handling comparison — swtoremu and swtoremu2

The reference tree was read only. Scope: legacy server packet enum/dispatch,
area attach startup, area packet implementations and fixture loaders, parser
opcode catalogue and area parsers; compared with current SharpServer area
startup and packet enum. This is not an audit of every historical branch or
all binaries in either repository.

## Names

`reference-opcode-map.csv` compares the reference server's numeric opcode
assignments with current SharpServer: all 48 distinct opcode keys retain the
same symbolic server name. Original names such as AreaHackPack,
AreaAwarenessEntered, AreaTeleportCharacter, AreaSetCharacter and
AreaClientReplicationTransaction were not replaced by encoded labels.

The reference parser explicitly lists `CMSG_UNK_61116AD5`,
`CMSG_UNK_F96DCDB0`, and `CMSG_UNK_7CB9A193`, with later CMsg aliases. These
are unknown/encoded labels in that tree too, not recovered semantic names.
The reference server has no CMsg61116AD5 handler file or enum assignment.
Its CMsg7CB9A193 and AreaModulesList handlers read only the envelope and have
empty RunImplementation bodies. A symbolic name by itself does not establish
body decoding or working lifecycle behavior.

## Existing handling and captures

Reference `Server/NET/Packets/Client/ObjectReply.cs` area attach branch sends
hack pack, time, awareness range, hardcoded RPCs, teleport, SetCharacter twice,
numbered CRT1..17, effect captures and two awareness captures. This existing
sequence is the source of much of the current startup bundle; it was not
independently invented. The reference CRT loader just reads the numbered
`.acrt` file; it does not implement a room transition.

Reference `Tools/Parser/.../Handlers/AreaHandler.cs` contains useful existing
parsers, but its HackPack parser has an empty frame-body branch. Neither that
parser nor the reviewed runtime paths supplies a proven doorway/gnarls_new
transition implementation. Search of the runtime AreaServer and NET source
found no dedicated room/collision/movement service beyond the startup sends.
This is a bounded absence finding, not proof no original developer ever solved it.

`reference-fixture-comparison.csv` hashes the 20 CRT/awareness/hack-pack files
present in reference bin/Debug/AreaServer against corresponding current files:
19 are byte-identical; the 55-byte CRT3 differs. The live comparison used a
separate matched override for CRT3-on and explicit omission for CRT3-off, so
these disk fixture hashes must not be mistaken for the actual live inputs.
EffectEvent files were outside this fixture comparison.

## Implication

No named original server opcode was found lost from the current enum, and no
working dynamic doorway handler was found in the reviewed reference source.
Existing names, parsers and captures should continue to be reused. The next
question remains whether the adapted startup data/order and client native room
selection agree; this review does not establish a missing opcode.

Current startup differs from the reference in deliberate compatibility and
experiment choices (including placement/order and CRT3 policy). An original
startup replay targeting another client version is not proof those choices
should be blindly reverted for April. Audit each against actual delivery and
native client evidence before a new one-variable run.
