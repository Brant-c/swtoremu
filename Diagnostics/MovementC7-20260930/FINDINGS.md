# April character-sync C7 decoding

Confidence: Client-derived field layout; Captured C5/C7 packet sizes.

The April send wrapper A80080 writes opcode 61116AD5 and invokes AA6920.
AA6920 writes the object+1C mask via 97C7F0: a four-byte little-endian
store, not the uint16 mask in the legacy MessageHeaders header. It then
writes flag1 heading (four bytes), flag2 vector (12 bytes), flag20 jump
(four bytes), flag4 end position (12 bytes), flag8/10 byte fields,
flag40/80 eight-byte fields, flag100 platform (eight bytes), and flag200
platform offset (12 bytes). There is no unconditional two-byte padding.
97C910 confirms the four-byte float store; 97C830 confirms the eight-byte
store; 97C3D0 copies the requested raw byte count.

C5 selects heading, end position and two eight-byte fields: body36/full44.
C7 additionally selects the vector: body48/full56. Full-packet offsets are
heading12, vector16, end position28, tail40. The first captured C7 has
vector (0.59968, 0, 0.01143) and end position (-64.86810, -6.90622,
-127.67088). Reading XYZ at the old C5 offsets would use the vector instead.
Names for the two tail fields come from the reference header; this change
preserves them as opaque bytes and adds no acknowledgement requirements.

Verify-Native.py checks 341 printed instruction prefixes against the pinned
April PE and saves bounded excerpts. These are verified existing-listing
excerpts, not a fresh disassembly. No process scanning or memory dumps.

The handler now accepts only captured masks C5 and C7, consumes the optional
vector before reading end position, preserves the complete body and rejects
truncations, extra bytes and all other masks before gameplay. Existing reply
policy is unchanged. C7 positions now reach the existing crossing detector.

The prior run rejected ten C7 packets, but a later C5 still crossed the
detector and emitted the same phase-info destroy. The native exterior room
was selected and measured retreat trigger collision flags were already
clear while the wall remained. This decoder bug is proven; its relationship
to the wall remains unproven.

Validation: Debug x86 build passed; captured C5/C7 position/body tests,
all100 truncations, dispatcher no-gameplay failures, area routing, blob
framing, wire round trips and packet workbench pass. WorldEntryOffline
fails before and after at the pre-existing missing RequestWorldFadeIn
observer check. Workbench registry uniqueness now uses opcode/direction/name
because multiple named claims share an opcode and local observations use
UNKNOWN; existing opcode/name lookup expectations are retained.

Before source, server executable, tests and registry are preserved here.
Experiment10 changes only server movement acceptance; existing hook and all
experiment09 environment settings remain identical. Older launch identities
remain unchanged and intentionally reject this new server executable.
