# Protocol evidence registry

`Protocol-Evidence.csv` is the canonical, machine-readable registry. This file
defines how to maintain it.

## What one row means

A row records a claim about one message identity. Opcode identity, envelope,
body schema, semantics, and lifecycle timing are separate claims. If only the
opcode is known, say so; do not mark the body or purpose as known by association.

Required columns:

- `Opcode`: eight-digit hexadecimal value or `UNKNOWN`.
- `Direction`: `C2S`, `S2C`, or `BOTH`.
- `Name`: stable descriptive name; retain the raw `CMsg...` name if unresolved.
- `Family`: transport/service family such as `Area`, `World`, or `System`.
- `Envelope`: independently established outer layout.
- `BodySchema`: typed body layout, or an explicit unresolved statement.
- `Confidence`: `Captured`, `Client-derived`, `Behavior-verified`, or
  `Hypothesis`.
- `Evidence`: paths to the capture, handler derivation, test, or checkpoint.
- `Notes`: limits and warnings.

## Promotion rules

- `Hypothesis` → `Client-derived` requires the complete relevant native read or
  write order, not a nearby string or dispatch-table entry.
- `Hypothesis` → `Captured` requires bytes from a known direction and lifecycle.
- Any level → `Behavior-verified` requires the April client to produce the
  predicted state change, with preserved logs.
- A behavior result does not automatically prove every field name in a schema.

When evidence conflicts, add the conflict to `Notes` and keep the lower
confidence until reconciled. Do not silently overwrite the previous basis.

## Workbench integration

`PacketWorkbench.ps1` loads the CSV to name known plaintext opcodes. Its decoder
does not claim that a registry row's semantic interpretation is correct; it
reports the confidence and evidence alongside the bytes.

Example:

```powershell
.\Diagnostics\PacketWorkbench.ps1 -Hex 'D5 CD 6D F9 08 00 B3 65 01 02 03'
```

Compare two plaintext packets:

```powershell
.\Diagnostics\PacketWorkbench.ps1 -Path first.bin -ComparePath second.bin
```

Decode Hero transport-version-5 packed unsigned values from a known body
offset:

```powershell
.\Diagnostics\PacketWorkbench.ps1 -Path rpc.bin -PackedOffset 12
```

Packed decoding is deliberately opt-in because arbitrary body bytes are not
necessarily a packed-value stream.

Create a controlled-run record before a live experiment:

```powershell
.\Diagnostics\New-ProtocolExperiment.ps1 `
  -Name 'doorway control' `
  -Question 'Does crossing the doorway emit a correlated client opcode?'
```

