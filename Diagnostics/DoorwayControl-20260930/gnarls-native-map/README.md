# Read-only gnarls native identity mapping

This is experiment 2026-09-30-04. It launches the unchanged frozen doorway
control and adds one external read-only memory snapshot. The snapshot waits for
the emitted `gnarls_new` startup marker and stable state-3 selected objects. It
does not require a doorway crossing.

Run `Launch.ps1` from a fresh PowerShell with the old client and servers closed.
Enter Tython normally, do not use abilities, and wait in the Masters' Retreat.
Leave the client open until `scanner-console.log` reports a captured map.

The scan searches readable committed client memory for node
`0x1AC6F6DC94`, its packed wire form and ASCII `gnarls_new`. It saves match
addresses and bounded 4096-byte snapshots of the objects currently selected at
`area+0x2A0` and `area+0x400`, then reports exact containment or direct-pointer
relationships. It uses `OpenProcess(0x410)`, `VirtualQueryEx` and
`ReadProcessMemory` only.

The first live invocation waited on literal `gnarls_new` in the server log, but
AREA payload prefixes are logged as hyphenated hex. It made no memory capture.
The preserved corrected invocation waits on the exact ASCII byte sequence in
that hex log. Its data capture completed; only its final self-including manifest
pipeline failed. The manifest was regenerated excluding itself, and the final
script contains both corrections. See the experiment record and capture results.
