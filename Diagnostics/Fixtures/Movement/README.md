# Captured C5 movement fixture

`C5-20260929.hex` is plaintext from `Diagnostics/last-server-full.log`,
2026-09-29 18:21:21, first CMsg61116AD5. The complete AREA-POLL body line is
preserved in `Diagnostics/DecoderBaseline-20260930/movement-source.txt` and
the envelope was checked with PacketWorkbench. Confidence: **Captured**.

44 bytes total, 8-byte opcode/component header, 36-byte body. The four bytes
at body offset 0 are C5 00 00 00. Existing code interprets the next four
little-endian floats as heading/X/Y/Z. The final 16 bytes are preserved as
opaque data, with no claim about identifiers, counters or timestamps.

Tests derive every shorter prefix, wrong variants (including a changed high
variant byte), wrong opcode and an appended byte. These are synthetic negative
cases, not captures. Exact-length acceptance is intentionally conservative;
it does not establish a universal native schema or room-loading behavior.

The unrelated PacketWorkbench test's short synthetic example is an envelope
test, not a valid movement body fixture.
