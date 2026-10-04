# Native room-state analysis — 2026-09-30

Static April-client disassembly establishes a native object lifecycle field at
object offset `+0x8C`. This is not yet a protocol-message mapping.

- `0x00B7AED0` writes state 1 and then state 2.
- `0x00B7AF50` also writes 1 then 2.
- `0x00B7B940`, when auxiliary state `+0x90` is 6, calls the state-2 path and
  then writes state 3.
- `0x00B7C390` treats state 3 as a distinct active path, temporarily calls the
  state-2 path, restores state 3, and compares the object with the area object's
  pointer at `+0x2A0`.
- The client loop at `0x0071C610` obtains the area object from global
  `0x01496E20`, walks its object collection at `+0x3DC/+0x3E0`, reads each
  object from the collection node at `+0x20`, and tests object state `+0x8C`
  against 3. It also compares object identities against area offsets `+0x2A0`
  and `+0x400` before choosing activation/deactivation calls.

The post-crossing snapshot sampled the area root at `0xF43739A0`, not a proven
`gnarls_new` object. Its value 3 therefore cannot establish destination-room
residency. The next control observes the area root and both client-selected
object pointers, recording pointer identity and `+0x8C/+0x90` state changes.

The observer uses `OpenProcess(0x410)` and `ReadProcessMemory` only. It does not
call client code, suspend threads, install hooks, write memory or send packets.
Addresses and interpretations are Client-derived only to the extent of the
listed read/write order. Room names, the meaning of auxiliary state 6, and the
wire event responsible for any transition remain unresolved.
