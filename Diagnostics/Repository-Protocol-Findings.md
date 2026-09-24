# April 2012 repository startup

Verified with the visible diagnostic launcher on September 16, 2026. The client
reached the rendered character-selection screen, and all 74 native character
specifications reached state 2 (ready). Evidence is saved under
`character-selection-success-20260916*` in this directory.

## Wire format and routing

The component contains two 16-bit object handles. A server reply reverses the
request handles; both halves matter to native route lookup at VA 009EE9FB.
RepositoryServer advertises server handle 65A8 through SignatureResponse. A
client repository handle of 2 therefore receives component 000265A8.

| Message | Opcode | Payload after opcode and component |
| --- | --- | --- |
| Revision notification | A08C1ACF | Terminated byte string |
| Synchronization request | 45F77B86 | uint64 cached revision |
| Synchronization reply | 26959B72 | Terminated error string; empty means success |
| Resource request | 463B0D17 | uint32 request ID, terminated path string |
| Resource reply | 2F7A6A25 | uint32 ID, error string, path string, uint32, three strings, uint64, length-prefixed byte buffer, uint32 |

All integers are little endian. Strings have a uint32 byte count including the
NUL terminator. The local static repository currently uses revision text `1`;
this is not a recovered historical database timestamp.

The revision notification dispatches through 0063F700. Synchronization reply
dispatch at 0064A67C calls 0063F810, which invokes registered callback 00B46600.
This initializes native state 5 normally, with worker pools already allocated.
No write to force resource-manager readiness is required.

Resource-reply decoding is at 0064A454. Handler 0063EF90 recognizes the literal
`FQN NOT FOUND` and returns native status FACE000F. The emulator has no remote
asset store, so unavailable requests receive this explicit error. This prevents
unanswered requests from occupying the native loader indefinitely. Failure is
not reported as success. Native error callbacks were verified in
`repository-not-found-native-callbacks.log`.

## Assets and diagnostics

Use the full main and English release-48 archive manifests matching the April
retail release-37 executable. `Restore-AprilAssets.ps1` verifies size and MD5,
preserves existing files, and downloads sequentially. Partial downloads are
renamed only after verification. The 500 prototype buckets are the count in
the matching archive, not an arbitrary cap.

The resource command queue is manager+2E8. Pending reads are manager+168.
Active reads are the sum at manager+298, +2B4, and +2D0, capped at 50 by
00B4632E. `Read-ResourceQueue.ps1` reports these separately.

Manual repository attach/result/stack restoration is now opt-in through
`SWTOR_TEST_REPOSITORY_BYPASS`. It conflicted with normal completion and caused
a stale-context crash. Manual revision/init, GUI, and petmouse delivery remain
separate opt-in experiments. Per-asset debugger stops are opt-in through
`SWTOR_TRACE_ASSET_DELIVERY`, because they substantially slow large native loads.
Normal character-spec readiness still gates character-list requests.

World/game/tracking startup packet sender handles match their SignatureResponse
handles (65AB, 65AC, 65B2). Startup messages are sent once after ModulesList,
rather than duplicated during object attachment.

## Remaining boundaries

Character selection is verified. Playable world entry is not. A user-selected
character triggered Tython TravelPending and native active-area completion, but
no AreaServer service attachment was observed during that test.

World packet 8EB28DE9 is a uint32-length byte list. The existing C++ handler
consumes it without replying; SharpServer now does the same with length
validation. Its precise meaning is still unknown. Repository packet B4BF82C3
is emitted after resource replies (0063F1AB calls 00A6B690); RepositoryDataReceipt
now consumes its uint32 value like the existing C++ handler. Directory request 3E7D74F5 is
not implemented; do not invent directory contents or imply these are complete.
