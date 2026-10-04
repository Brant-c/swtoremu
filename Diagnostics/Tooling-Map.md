# Local tooling map

## Packet and transport work

### `Diagnostics/PacketWorkbench.ps1`

Deterministic command-line inspection of already-decrypted plaintext packet
bytes and binary fixtures. It reports opcode, routing handles, registry
evidence, body bytes, optional Hero packed values, and byte differences.

It intentionally does not decrypt a live session or inflate a stateful capture.

### `Diagnostics/New-ProtocolExperiment.ps1`

Allocates a dated experiment ID, copies the controlled-run template, fills its
question, and adds the pending run to the experiment index. It changes no
runtime behavior.

### `Tools/PacketAnalyser`

Legacy WinForms capture viewer containing Salsa20 and raw-deflate support. Use
it when the existing capture/key workflow is needed. Its packet class consumes
the opcode and component but does not provide maintained message schemas; do
not treat its labels as authoritative protocol evidence.

The `swtoremu2` copy is substantially the same legacy implementation and is a
comparison source, not another active target.

### `Tools/Hero`

Local Hero serialization implementation. In particular,
`Tools/Hero/Hero/PackedStream.cs` defines transport-version packed integer,
string, boolean, version, and end tokens. Prefer it over newly inferred packed
encoding rules.

## Script and content work

### `Tools/SCPTExtractor`

Extracts and inspects HeroScript content. Use it to determine script selectors,
method roles, and client/server annotations. Script semantics do not establish
native wire framing.

### `Tools/tor_tools`

Older TOR/GOM/content libraries used by existing diagnostics and extraction
work. Preserve compatibility with scripts already depending on these projects.

### `D:\SWTORClassic\extracTOR`

Modern standalone archive extraction UI. Use it to obtain content assets. It is
not a protocol decoder and its current README warns that it is early software.

### `D:\SWTORClassic\assettest\resources`

Locally extracted resource tree containing scripts, generated GOM data, area
data, and other assets. Use it for semantic and content relationships, not as a
substitute for native executable network-handler disassembly.

