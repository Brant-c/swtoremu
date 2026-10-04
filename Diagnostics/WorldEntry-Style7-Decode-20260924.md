# SWTOR world-entry style-7 decode — 2026-09-24

## Verified

`Diagnostics/Decode-Style7Replication.py` decodes the compact replication
schemas carried by CRT1 and the native field-state stream used by styles 7 and
8.  The bit decoder is a direct port of the April client's routines at RVAs
`0x001B0E00`, `0x001B0EB0`, and `0x001B1070`.  Field states are two-bit values;
state 3 introduces a run of state-2 fields.  The state stream follows the value
payload rather than preceding it.

CRT2 creates player node `0x4000010E218A839C` as `chrPlayerCharacter` using
schema structure 26.  That structure contains 215 inherited fields, including:

| Index | Field | Type |
| ---: | --- | --- |
| 35 | `chrIsMe` | Boolean |
| 89 | `chrCharacterPlayMode` | `chrPlayMode` enum |
| 104 | `chrCharacterPhaseMode` | `chrPlayMode` enum |
| 129 | `chrPlayerLoaded` | Boolean |

The decoded field states are:

| CRT | `chrIsMe` | play mode | phase mode | `chrPlayerLoaded` |
| --- | ---: | ---: | ---: | ---: |
| 2 | 2 | 2 | 0 | 2 |
| 4–11, 13–17 | 2 | 2 | 2 | 2 |

The native class reader skips state 2 without deserializing a value.  Thus the
captured stream transmits **no value** for `chrIsMe`,
`chrCharacterPlayMode`, or `chrPlayerLoaded`, and none of the later player
updates changes them.  CRT2 carries state 0 for `chrCharacterPhaseMode`; this
is a default/reset state, not an explicitly serialized enum payload.  Later
updates omit it.

This establishes transmitted semantics, not the final live values after all
client-side initialization and scripts.  The repository Hero value classes
initialize Boolean to `false` and enum to `0`, so those are the expected values
for a newly constructed field which receives no other initialization.  It is
not yet verified that the native player-node constructor leaves these four
fields at those generic defaults.

## Phase payload boundary

CRT3's owner class is `phsPlayerPhaseData`.  The April GOM identifies its five
direct fields as `phsActivePhases`, `phsInstanceAllowAll`,
`phsOwnerOfShipToBeBoarded`, `phsUniqueActivePhase`, and `phsAuthorityID`.
However, CRT3 declares compact structure 1 while the CRT1 table's structure 1
is `utlTrainerList`.  Therefore that table cannot be used to assign CRT3's
22 value bytes to named phase fields.  The existing active-phase and player
references remain verified byte facts, but their exact field/value boundaries
are still unresolved.  No bytes were inferred or appended.

## Consequence

The leading player-state hypothesis is now narrower: the capture never
explicitly marks the replicated player as `chrIsMe`, never explicitly marks it
loaded, and never explicitly supplies its play mode.  A server-side forced
value is not justified until either native defaults are recovered or a
read-only live observer confirms the post-replication values.  The specific
next live question, if offline default recovery stalls, is to read these four
native fields immediately after CRT2 and after CRT17; it is not a request to
try guessed packets or fabricate CRT3.

## Read-only runtime observer

The April hook now has an opt-in detour on native `HeroClass::getField` at
static VA `0x004F5A00`.  It calls the original getter first, filters only the
four IDs above, and logs the returned interface and its first eight raw DWORDs.
It does not call the getter independently and does not modify the request,
class, output, result, or value interface.  Installation is guarded by the
exact April prologue `55 8B EC 83 E4 F8 6A FF` and by
`SWTOR_TRACE_PLAYER_FIELDS=1`.

This observes natural getter calls rather than forcing snapshots after CRT2
and CRT17.  Therefore a field appearing in `PlayerFieldHook` is positive
evidence that the client read it, while no matching line only means that this
getter path was not naturally used during the capture.  It does not prove a
false, zero, or missing runtime value.  `Analyze-TythonTrace.ps1` reports the
read count and distinct raw value shapes for each observed field and states
this limitation when no reads occur.

The Release/Win32 hook builds cleanly, its executable still has the expected
prologue at RVA `0x000F5A00`, and `Test-WorldEntryOffline.ps1` passes.  A
targeted client run is now justified to determine whether the readiness loop
naturally reads any of these four fields.  The acceptance criterion is one or
more `PlayerFieldHook` records before or during the repeated `0xF5F540F2`
poll.  If there are none, the next offline task is locating a safe replication
completion boundary for a true two-point snapshot—not changing packet bytes.

### Targeted run result (17:11–17:16)

The observer installed successfully (`player-field trace=enabled`).  The
capture recorded six readiness entries and four outbound `0xF5F540F2`
requests, proving that the client reached and repeated the relevant wait loop.
It recorded zero `PlayerFieldHook` entries.  This verifies that the loop does
not naturally read any of the four fields through the observed
`HeroClass::getField` path.  It does **not** establish their runtime values.
The next step is therefore the already-defined offline branch: identify the
replication-completion boundary and native player-node pointer needed for a
read-only two-point snapshot after CRT2 and CRT17.

## Replication-boundary recovery

Static disassembly now verifies the CRT message path.  The dispatcher at
static VA `0x0064ED70` recognizes opcode `0x0D446E80`, reads the stream ID with
`0x0097C4C0`, invokes the replication consumer through virtual slot `+0x40` at
`0x0064F141`, and does not return until that consumer completes.  CRT2's
captured stream ID is `0x001B5013`; CRT17's is `0x001B502D`.

The selected player can be resolved without guessing or pointer scanning.
The native `CharacterChangeState` receiver at RVA `0x317A70` loads the global
character manager from static VA `0x014929DC`, searches its 64-bit-keyed tree,
and reads the mapped character pointer from node offset `+0x18`.  The tree
lookup at RVA `0x42F200` compares the high key DWORD at node `+0x14` and the
low DWORD at `+0x10`.  The snapshot observer reproduces only that read-only
traversal for selected character `0x4000010E218A839B`.

The hook now records the first `0x300` bytes of that character immediately
after CRT2 and CRT17.  It also performs a one-time, read-only scan of executable
memory for the established generated-accessor instruction template containing
each of the four exact field IDs and records candidate code bytes.  These
candidates remain hypotheses until their instructions are decoded; the hook
does not call them.  The Release/Win32 build succeeds with zero warnings and
errors, and the offline world-entry gate passes.

The first attempted snapshot run at 17:25 correctly loaded the new DLL but the
CRT observer stayed disabled.  Its dispatcher guard included a relocated
absolute exception-handler address, so ASLR changed those bytes in memory even
though the invariant function prologue was correct.  An attempted correction
narrowed the guard to the invariant `55 8B EC 6A FF` dispatcher prologue plus
the separate eight-byte `ReadUInt32` prologue.  No snapshot data from that run
is treated as evidence.

A subsequent attempt with the dispatcher detour enabled caused the client to
exit immediately.  The detour, nested `ReadUInt32` interception, in-process
map traversal, and accessor-memory scan have therefore been removed from the
hook.  Their static reverse-engineering notes above remain hypotheses/useful
addresses, but none of that failed instrumentation is active.  Further live
inspection should attach externally after the user reaches character
selection and before Tython load, rather than intercepting the replication
dispatcher.

## External Tython snapshot (17:41)

A full external dump was captured after the player entered the Tython
readiness loop: `Diagnostics/tython-live-20260924-1741-29260.dmp`.
`Diagnostics/Inspect-LivePlayerSnapshot.py` decodes it without another client
hook.

Verified native relationships in that dump:

- the selected native character map resolves node
  `0x4000010E218A839B` to character wrapper `0xE9BECAB0`;
- the GOM hash entry at `0xFA8BCE40` resolves the same node ID to
  `HeroNode 0xD21A9BA0`;
- the repository's old `HeroNode +0x48` comment is not valid for this build;
  the node contains the character wrapper at `+0x50` and the relevant class
  value container at `+0x4C`;
- the live class value container is `0xD4C02E38`, with type descriptor
  `0xEC47A9A0`;
- that type has a sorted 610-field ID array at
  `0xCC5B2FB0..0xCC5B42C0` and a parallel 12-byte descriptor array beginning
  at `0xCC5B42D0`.

The four target fields resolve in that live array as follows:

| Field | Sorted index | Descriptor | Three descriptor words |
|---|---:|---:|---|
| `chrIsMe` | 117 | `0xCC5B484C` | `FA44D1C0, 00001017, 00000FFD` |
| `chrCharacterPlayMode` | 253 | `0xCC5B4EAC` | `FB215E00, 00001028, 00000FA4` |
| `chrCharacterPhaseMode` | 311 | `0xCC5B5164` | `FB218220, 0000102B, 00000FB4` |
| `chrPlayerLoaded` | 401 | `0xCC5B559C` | `FB21F360, 0000103B, 00001006` |

Disassembly of the scalar proxy path establishes the remaining indirection:
the accessor passes `HeroClass + 0x14` to `0x004D0DA0`, which resolves the
field again in the concrete type at `[context+4]`; `[context+8]` is the
storage base.  Routine `0x004D0590` reads the state byte at storage base plus
descriptor word 2 and, for state 0, returns storage base plus descriptor word
3.  Applying that exact path produces these live values:

| Field | State address / byte | Value address | Runtime value |
|---|---|---|---|
| `chrIsMe` | `CC5B6F97 / 00` | `CC5B6F7D` | Boolean **true** |
| `chrCharacterPlayMode` | `CC5B6FA8 / 00` | `CC5B6F24` | enum **1** |
| `chrCharacterPhaseMode` | `CC5B6FAB / 00` | `CC5B6F34` | enum **1** |
| `chrPlayerLoaded` | `CC5B6FBB / 00` | `CC5B6F86` | Boolean **false** |

All four are concrete state 0 values, not inferred defaults.  This also shows
that client-side initialization changes `chrIsMe` and both mode fields after
the captured replication omits or resets them.  `chrPlayerLoaded=false` is a
verified discrepancy at the readiness loop and is now the leading blocker
hypothesis, but it is not yet proven to be the sole gate.

The five named `phsPlayerPhaseData` IDs do not occur in this 610-field player
container.  They belong to a separate phase-data object, consistent with CRT3
having a different owner class.  CRT3's schema mismatch still prevents a
sound packet-level assignment, and no phase value is inferred from nearby
memory.  Locating that separate live instance remains offline work; it does
not justify invented CRT3 bytes.

## `chrPlayerLoaded` script path

An exact 64-bit scan of all 846 decrypted April v5 scripts finds
`0x4000000D5DF53477` in exactly one script,
`C9CA0FEDFE12C16C.scpt`, at payload offset `0x20531`.  The April SDEF maps that
script to definition `0xD000199A7D03034B` (key `0xF81AB49A`, variants 0 and
1).  This is the same method/definition ID recorded by `ReadinessVmHook` each
time the client emits the repeated `0xF5F540F2` readiness poll.  The adjacent
GOM constant table contains, in order, `chrPlayerCharacter`,
`chrPlayerLoaded`, `chrOracle`, `chrReplicatedPlayers`, and player move-state
fields.

This verifies that the readiness script module has a resolved
`chrPlayerLoaded` field constant; it does not by itself prove that the precise
polling function branches on it.  In the live dump the resolved field metadata
pointer appears in the script field record at `0xFA8C59C0`, and that record has
one reference from a runtime constant-pointer table at `0x07BCE514`.  Neither
the state address nor the Boolean value address has a literal pointer reference
in the dump, consistent with the VM resolving storage through field metadata
at execution time.

The next discriminating observation is therefore specific: break externally
on reads and writes of the resolved `chrPlayerLoaded` Boolean after the player
object exists, and retain the accessor/JIT call stack.  A read from the
readiness callback would prove it is a gate; a prior write would identify the
missing initialization path.  If neither occurs, the field is only module
vocabulary and the blocker hypothesis is rejected.  This observation should
not alter the Boolean, inject CRT data, or hook the replication dispatcher.

### External data-breakpoint result (18:45 run)

The external launcher resolved the live Boolean at `0xCBE72176` with value
`0` and armed a one-byte read/write hardware breakpoint before
`CharacterChangeState`. It recorded eight initialization accesses; every
record observed value `0`. The sole static-client hit stopped at RVA
`0x001013C9`. The preceding instruction reads the Boolean (`mov dl,[eax]`),
and the stopped instruction copies it (`mov [ecx],dl`), establishing generic
typed-value copy machinery rather than a setter that marks the player loaded.
The runtime-generated-code hits likewise produced no value transition.

After the breakpoint was armed, the `0xF5F540F2` readiness callback ran at
least three times (18:48:23, 18:48:52, and 18:49:22) under definition
`0xD000199A7D03034B`. None of those invocations accessed the watched byte.
Thus `chrPlayerLoaded=false` remains a verified live discrepancy, but it is
**not the direct condition read by this periodic readiness callback**. The
direct-gate hypothesis is rejected. No value or packet was modified.

## Live phase-object result

CRT3's transaction header creates node `0x00000017BFADF6AC` as
`phsPlayerPhaseData`. Normal traced runs explicitly suppress CRT3 as
known-incomplete. The newest full dump contains zero occurrences of that owner
node ID, while the referenced active phase `0xFF5F184AAA9ECE77` occurs 16
times and replicated player `0x4000010E218A839C` occurs twice. Thus the active
phase resource and player exist, but the phase-data owner object was never
created; there are no live phase-field values to decode in this run.

The wire mismatch is stronger than a missing field-name table. CRT3 declares
compact structure 1, but CRT1 defines structure 1 as one-field
`utlTrainerList` (`ablListRemoteTrainers`), whereas April
`phsPlayerPhaseData` has five verified direct fields. Compact structure numbers
are transaction/schema-session data, not interchangeable class identifiers.
Consequently the 22 value bytes cannot be assigned to the five phase fields
using this CRT1, even if their byte pattern resembles nested maps and IDs.
Doing so would be a hypothesis, not schema-driven decoding.

The current evidence therefore supports a missing/incompatible phase-data
transaction as the next lead, but not sending the saved CRT3 unchanged: that
fixture does not match the active CRT1 schema and has already been classified
as unsafe. The required offline artifact is a matching CRT1/CRT3 pair (or an
exact reconstruction of the compact `phsPlayerPhaseData` structure definition
and value stream). Until then, phase values and replacement bytes remain
unresolved rather than fabricated.

## Compact-schema writer safety gate

`Diagnostics/Build-Style7Schema.py` now implements only the independently
verifiable portion of a style-7 writer: compact unsigned integers and the CRT1
structure table. It decodes and re-encodes all 104 structures byte-exact across
CRT1 offsets `0x8..0xABE9` (44,001 bytes), and does not write or modify an
`.acrt` fixture. The remaining 13,373 transaction bytes are deliberately
outside its output.

Its GOM manifest for `phsPlayerPhaseData` confirms the five direct fields and
their nested types, but refuses to encode them. Both embedded references,
`phsActivePhaseInfo` and `phsUniqueActivePhaseInfo`, lack unique compact
structure numbers in the captured CRT1 table. Those numbers are session schema
references and cannot be replaced by class IDs or guessed constants. The next
offline requirement is therefore to recover how the client constructs compact
structures for those two embedded classes, then prove value and field-state
serialization against a known-good captured object before emitting any phase
transaction.

### Dependency-first phase schema proposal

The captured schema establishes two additional construction rules: all 104
structures sort their selected fields by numeric field ID, and every one of 38
embedded-class references targets a structure whose base class matches the GOM
embedded type. A full type-chain comparison reproduces 2,691 of 2,731 captured
fields exactly. Twenty-two field definitions are absent from the April GOM;
the remaining 18 comparisons are repeated references to `dynVisual` or
`dynVisualState`, for which CRT1 contains two valid structure variants. There
is no unexplained type-shape mismatch.

The phase GOM hierarchy is also verified: `phsActivePhaseInfo` is empty;
`phsUniqueActivePhaseInfo` has four direct fields and names the former as its
sole component; `phsPlayerPhaseData` has five direct fields and no components.
The offline tool can therefore construct this dependency-first proposal:

- structure 105: `phsActivePhaseInfo`, zero components, zero fields;
- structure 106: `phsUniqueActivePhaseInfo`, one component, four fields;
- structure 107: `phsPlayerPhaseData`, zero components, five fields.

The resulting 107-structure table is 44,207 bytes and decodes/re-encodes
byte-exact in memory. Numbers 105-107 are explicitly session-local proposals,
not recovered wire facts. No value/state bytes or `.acrt` file are emitted.
The remaining blocker is validating serialization of the nested map and
embedded values plus their field-state streams against known-good captured
examples.

## Schema-dependent CRT3 value interpretation

CRT1 itself supplies a known-good analogue: structure 1 is a one-field
`Map<UInt64, EmbeddedClass<rnidRemoteNpcIconData>>`. Its live object contains
four entries. Each embedded structure-2 value has an explicit 58-byte value
region followed by exactly one `F8` state byte; the enclosing map field has a
one-byte `80` state region. This proves the nested layout is count, key,
embedded-value length, embedded values, then embedded field-state bits. It
also proves the current scalar-only state helper cannot be applied unchanged
to embedded values, because doing so crosses the captured `F8` boundary.

Against the reconstructed, numerically sorted `phsPlayerPhaseData` fields,
CRT3's complete 22-byte value region divides without residue as:

1. outer map count `1`;
2. `phsTypeEnum` key `1`;
3. inner map count `1`;
4. `Int64` phase key `0xFF5F184AAA9ECE77`
   (signed `-45290762281234825`);
5. embedded `phsActivePhaseInfo` value length `0`, consistent with its verified
   zero-field class;
6. `UInt64` value `0x4000010E218A839C`, the replicated player ID.

The sorted phase schema places `phsActivePhases` first and `phsAuthorityID`
second, so the only coherent field assignment is an active phase of type 1
containing the known phase ID, followed by `phsAuthorityID` equal to the
player. The other three fields have no value bytes. This is a strong
schema-dependent decode, not yet a wire-authoritative decode: CRT3 still says
structure 1 while the available CRT1 assigns structure 1 to `utlTrainerList`,
and the final state byte `00` cannot be labeled exactly without the matching
schema-aware state decoder. No bytes have been changed or generated.

## Isolated schema-matched CRT candidate

`Diagnostics/Generate-MatchedPhaseCrtCandidate.py` now generates an isolated
pair under `Diagnostics/GeneratedPhaseCandidate`; it never edits the
AreaServer fixtures. Candidate CRT1 appends the three proposed structures to
the byte-exact 104-structure table. Its original trailing transaction remains
byte-identical. Candidate CRT3 retains its complete object, 22 value bytes,
and `00` state byte; its sole change is offset `0x1E`, where the mismatched
one-byte structure reference changes from 1 to 107 (`0x6B`). Thus no phase
value or state byte is fabricated.

The files are deliberately not installed or transmitted. Their remaining
acceptance gate is an independent proof that CRT3's original `00` state byte
is valid for the appended five-field phase schema. Passing schema round trips
and residue-free value parsing is necessary but not sufficient for that claim.

## April client-script confirmation and opt-in test

Jedipedia's decoder was pointed at this repository's own April `.tor` files.
Its `phsPlayerPhaseDataClassMethods` decompilation shows that
`OnReplicationNodeCreate` performs the direct assignment
`$PHASE.phsActivePhaseData = Me`. With CRT3 suppressed, this global therefore
remains `None`; the client script does not construct replacement phase data.
Update and destroy handlers likewise operate on the replicated
`phsUniqueActivePhase` rather than synthesizing the missing node.

The same asset decode verifies `phsTypeEnum` value 1 is `phsTypeClass`.
Consequently CRT3's active entry is a class phase, not a generic world phase.
All five phase-data fields carry the same GOM attribute bitset 576 (`0x0240`),
so field-specific replication attributes do not explain the value/state split.

For the controlled 19:55 test, the trace launcher enabled the isolated candidate through
`SWTOR_CRT_OVERRIDE_DIRECTORY`. `CRT.Get` uses an override file only when that
exact filename exists and otherwise falls back to the untouched AreaServer CRT
directory. Thus only CRT1 and CRT3 are replaced; CRT2 and CRT4-17 remain the
captured production fixtures. CRT3 remains guarded by the existing explicit
`SWTOR_ENABLE_UNVERIFIED_CRT3=1` switch. The server builds successfully and the
offline world-entry gate passes. This creates a narrow client test: determine
whether creation of `$PHASE.phsActivePhaseData` advances world entry or causes
a schema/state rejection.

## Client rejection of the authored schema

The 19:55 test transmitted the isolated CRT1 and CRT3 overrides with their
expected SHA-256 hashes. The client immediately raised
`G::SerializationException`; the first-chance dump is
`Diagnostics/world-entry-20260924-195555-32536-first.dmp`. Read-only dump
analysis recovered the exact exception text: `Unable to read field count`.
The throw path returns through client RVA `0x1ADFA7`, inside the native schema
type-description reader, rather than the earlier exhausted-value path through
RVA `0xDC16F`/`0x1AE35A`.

At first this appeared to reject the generated 105-107 schema table. It did
**not** test the 22-byte phase-value interpretation because the client failed
while consuming CRT1, before CRT3 could establish the proposed phase object.
The exact reason for that CRT1 failure is established below and was framing,
not a demonstrated disagreement over the generated type records.

Subsequent offline inspection of that dump recovered the active schema buffer
and its bound. The client reader had `length=44001`, exactly the original CRT1
schema size, even though the candidate contained the full 44,207-byte expanded
table. CRT1 offsets `0x04..0x07` are a little-endian schema sub-reader length;
the first generator preserved the stale value `44001`. The reader therefore
stopped at the end of structure 104 and threw while attempting to read the
first appended definition. This is a verified framing defect in the rejected
candidate and supersedes the earlier inference that the native type grammar
itself rejected the appended records.

`Generate-MatchedPhaseCrtCandidate.py` now updates that bound from 44,001 to
44,207 and asserts that it equals the complete decoded schema length. The
isolated CRT1 hash is now
`A75C5DE9C0E32DC3C6602607FC79B216D687BE538601D3A5F9D581BF99E08229`;
CRT3 is unchanged from the earlier isolated candidate. This repairs only the
demonstrated framing error. Schema acceptance and phase semantics remain
unverified until a controlled parse.

The trace launcher has been returned to its safe state: both
`SWTOR_CRT_OVERRIDE_DIRECTORY` and `SWTOR_ENABLE_UNVERIFIED_CRT3` are blank.
The corrected isolated candidate remains under
`Diagnostics/GeneratedPhaseCandidate`; no production CRT was overwritten.
The next controlled client run now has one specific discriminator: whether
the correctly bounded CRT1 is accepted and CRT3 creates the phase node. Any
new rejection must be analyzed at its exact stage before changing value or
state bytes.

## Client-script loading-gate correction

Jedipedia HeroScript extracted from the repository's 1.2 assets establishes
that `chrPlayerCharacterClassMethods.Replication_Create` does not gate the
local player on `chrPlayerLoaded`, `chrIsMe`, or `chrCharacterPlayMode`. Once
the created node equals `GetPlayerCharacterNode()`, it immediately sets
`GAMESTATE_WithinArea`, requests world fade-in, fires
`onPlayerCharacterCreated`, and calls `setPlayerLoadingFinished(true)`.
`chrPlayerLoaded` is used by this script only to control rendering for a
non-local replicated player and by the trivial `IsPlayerLoaded` accessor.

The loading screen subsequently calls the player's
`CheckPhaseNeedsContinue`. `phsParticipantClassMethods` proves that this asks
the server only when `$PHASE.GetCurrentInstance()` exists and has the Hydra
hook `On Phase Needs Continue`. Otherwise it directly calls
`guiGfxLoadingScreenClassMethods:PhaseNeedsContinue(false)`, which fades in.
`GetCurrentInstance()` is merely a lookup of `phsCurrentInstanceNameID` in
`phsActiveInstances`. Therefore absent `phsActivePhaseData` alone is not a
loading-screen blocker; with no current phased instance, the explicit fallback
is to continue. This demotes CRT3/phase-data repair from the primary world-entry
hypothesis. The next diagnostic target is whether the local player's
`Replication_Create` handler executes and recognizes the node returned by
`GetPlayerCharacterNode()`.

## Jedipedia extract inventory and next offline discriminator

The additional `_JPEXTRACT` files were decoded from this repository's assets,
not substituted Jedipedia assets. `Scriptdef.listdump.csv` identifies the two
smallest supporting definitions for the decisive calls in
`Replication_Create`: `_BaseClientClassMethods` (hash `2B7E4202`, script ID
`14988256013797863880`) owns `_SetGameState`/`RequestWorldFadeIn`, while
`guiApiClassMethods` (hash `F0A0483E`, script ID `14988082534666957042`) is the
likely owner of `setPlayerLoadingFinished`. The already supplied
`guiGfxLoadingScreenClassMethods` verifies the later fade-in/phase-check path
but cannot prove that player creation reached it.

Verified: the client script contains all three completion calls only inside
the `Me == GetPlayerCharacterNode()` branch. Therefore observing one of those
calls proves both that `Replication_Create` ran and that the local-node
identity comparison succeeded. Conversely, absence of a loading-screen GOM
definition lookup does not prove the handler did not run, because definition
lookups may have been satisfied from cache before the observer was installed.

Hypothesis: the stall occurs before, or at the identity test inside,
`Replication_Create`. The safest next discriminator is a read-only trace of a
fixed native boundary reached by `_SetGameState(GAMESTATE_WithinArea)` or
`RequestWorldFadeIn`; no field mutation, synthetic phase object, or authored
CRT3 is justified. To resolve that native boundary offline, obtain the
HeroMachine or assembly view (not another HeroScript decompile) of
`chrPlayerCharacterClassMethods.Replication_Create`, plus the corresponding
method in `_BaseClientClassMethods`. Those views retain the numeric call keys
needed to correlate the bytecode with the client's native dispatcher.

## `Replication_Create` assembly discriminator

Jedipedia's assembly view supplies an exact, non-semantic discriminator for
the local-player branch. At method offset `0x10B4`, the script calls
`EF.GetPlayerCharacterNode`; at `0x10D8` it calls `HM.NodeRefCompareEQ` on the
returned node and `Me`. The test at `0x10DD` branches to the non-local path at
`0x1AFF` when false. Consequently these line markers have precise meanings:

- `HM.TrackLine(0xA2)` at `0x10C5`: the identity comparison is about to run.
- `HM.TrackLine(0xA3)` at `0x10E5`: the identity comparison succeeded.
- `HM.TrackLine(0xAD)` at `0x1213`: execution reached
  `_SetGameState(GAMESTATE_WithinArea)`.
- `HM.TrackLine(0xB0)` at `0x127A`: `_SetGameState` returned and execution is
  about to call `RequestWorldFadeIn`.

The two BaseClient calls resolve from the same system node,
`0xE00058EF1F1B3857`. Their per-script call-table slots are `0x17` for
`_SetGameState` and `0x18` for `RequestWorldFadeIn`; these are local compiled
script indices, not packet opcodes and not values suitable for fabrication.
The `_BaseClientClassMethods` HeroScript independently verifies that
`_SetGameState` invokes `OnGamestateChanging` and then writes `_GameState`.
`RequestWorldFadeIn` is absent from that script body, consistent with an
inherited/native method.

Verified offline conclusion: a trace of the `0xA2`, `0xA3`, `0xAD`, and
`0xB0` markers can distinguish handler absence, local-node identity failure,
failure within `_SetGameState`, and successful arrival at world fade-in. The
observer must first identify this compiled method (script definition
`0xD000199A7D03034B`) so that identical line numbers in unrelated scripts are
not mistaken for evidence.

## 21:02 live discriminator result

The read-only 21:02 run is preserved as
`Diagnostics/world-entry-replication-create-watch-20260924.log` and
`Diagnostics/world-entry-replication-create-watch-hook-20260924.log`. The
native area loader reached state 3 and reported its active-area transition for
Tython. The character-change pipeline then found the replicated character and
its native component, and that component's state-dispatch returned success.
The process remained responsive and continued network traffic, confirming a
stall rather than a crash.

No `ReplicationCreateWatch` checkpoint (`A2`, `A3`, `AD`, or `B0`) fired. The
first observer attempted to find Jedipedia's assembly byte sequence in an
executable client allocation. Subsequent analysis shows that representation
is not retained as literal executable machine code, so absence of those
breakpoints is not evidence that the handler body was skipped. The temporary
lookup probes captured definition ID
`0xD000199A7D03034B`, the exact `chrPlayerCharacterClassMethods` definition,
during the OnEnter/character callback sequence. At lookup RVA `0x1CA838`, EDX
was 5. `Replication_Create` is exactly the fifth method in the decoded script's
method order (after `GetNearestMedCenter`, `updateInteraction`,
`ReceivePhaseAccumulatedState`, and `GetPlayerId`). The later character-state
dispatch received a non-null method pointer from native RVA `0x1CA880` and
invoked it through the script interface at RVA `0x1BE745`.

The zero visible after RVA `0x1BE745` is the outer interface-dispatch result;
it cannot be equated with the HeroScript body's `return true`. The corrected
leading conclusion is that the callback lookup selected method 5 and therefore
very likely invoked `Replication_Create`. The next discriminator must observe
the handler's postconditions: the `_GameState` transition to
`GAMESTATE_WithinArea` and the inherited/native `RequestWorldFadeIn` call.
That remains safer and more specific than modifying player fields or restoring
CRT3.

## 21:17 `_GameState` observer result

The April `client.gom` resolves `_BaseClient._GameState` to field ID
`0x400000045A767612`, type `Enum<GameState>`. Jedipedia's enum list confirms
`GAMESTATE_WithinArea` is value 4, matching the immediate argument in the
`Replication_Create` assembly. The field ID was added to the already verified
read-only `HeroClass::getField` observer for the 21:17 run.

The hook reported `player-field trace=enabled`, but no `_GameState` access
crossed `HeroClass::getField`. Meanwhile the native Tython area transition,
character lookup, component dispatch, and component return all completed as in
the preceding run. This result is inconclusive about `_SetGameState`: compiled
local/system-node fields can use a direct VM field accessor instead of the
generic `HeroClass::getField` routine. Absence from this observer must not be
treated as proof that the call was skipped. The run is preserved in
`Diagnostics/world-entry-gamestate-watch-20260924.log` and its companion
`world-entry-gamestate-watch-hook-20260924.log`.

The next offline input is the assembly view of
`_BaseClientClassMethods._SetGameState`. It will expose the exact direct enum
field getter/setter primitive and local slot used by the compiled method.

## `_SetGameState` native field-write discriminator

Jedipedia's `_SetGameState` assembly establishes the operation order without
requiring any guessed bytecode: it calls `HM.RefNodeFieldEnum`, invokes
`OnGamestateChanging(old, new)`, and then calls `HM.SetNodeFieldEnum` with the
same field operand and the new enum value. The zero printed for that operand is
not safely interpretable as a final runtime field number. `_GameState` is the
ninth field in the supplied `_BaseClient` schema, and v5 SCPT operands are
resolved by the loader/runtime; treating the printed zero as the schema ordinal
would therefore be unsupported.

Offline disassembly found a strong generic field-write candidate at static VA
`0x004F5C90`. It accepts a class/value pair plus the same two 32-bit halves of a
64-bit field ID used by the verified `HeroClass::getField` path. It resolves
that ID through `0x004F8130`, obtains a writable field interface, and reaches an
assignment path at `0x00501F80`. This identification remains a hypothesis until
a live call is observed, but it is specific and testable.

A pass-through hook now observes `0x004F5C90` only when the resolved ID is one
of `chrIsMe`, `_GameState`, `chrCharacterPlayMode`, `chrCharacterPhaseMode`, or
`chrPlayerLoaded`. It snapshots the supplied wrapper/interface words, calls the
original function with every argument unchanged, and logs its Boolean result.
It performs no setter call of its own and fabricates no field or replication
data. The Release/Win32 hook builds cleanly; its SHA-256 is
`5A0932C17E396F84560C3EB4DF82811B9C343569ADF1A7280B242EDEBA7F6B43`.

The next live run now has a narrow purpose: determine whether
`Replication_Create` writes `_GameState` to enum value 4. If the hook sees that
write, `_SetGameState` and the local-player branch are verified and attention
should move to `RequestWorldFadeIn`. If other readiness fields are written, the
same observation also provides their actual runtime representations. If the
candidate receives no matching writes, it is evidence about this native
boundary only—not permission to fabricate CRT3 or force fields true.

## 21:31 field-write and `chrPlayerLoaded` result

The run is preserved in
`Diagnostics/world-entry-playerloaded-zero-watch-20260924.log` and
`Diagnostics/world-entry-playerloaded-zero-watch-hook-20260924.log`. The hook
startup line verifies that both the generic field-read and candidate
field-write observers were installed. No matching `PlayerFieldWriteHook` event
was recorded for `_GameState` or the four tracked character fields. This does
not prove that `0x004F5C90` is the VM's `HM.SetNodeFieldEnum` binding; it only
means that this candidate saw none of those resolved IDs during the interval.

The external storage watch did resolve `chrPlayerLoaded` in this run and
repeatedly reported `value=0`. This is the first verified runtime value among
the requested readiness fields: **`chrPlayerLoaded` is false while the Tython
load is stalled.** It was repeatedly read and was never observed changing.
The access instruction was client RVA `0x001DEB49` (static VA `0x005DEB49`).
Offline disassembly places it at the successful return of the Boolean field
accessor beginning at `0x005DEB00`: after resolving the node and field, the
routine executes `mov al, byte ptr [eax]` at `0x005DEB47` and reaches the watched
epilogue at `0x005DEB49`. Thus this is a real client Boolean read, not a value
invented by the launcher.

Verified facts from this run are limited to the false value and repeated
reads. The hypothesis now worth testing offline is that a script or native
readiness loop is waiting for `chrPlayerLoaded` to become true. It is not yet
verified which caller performs the read, what legitimate event sets the field,
or whether forcing it would be safe. No forced write is justified until that
producer/consumer relationship is mapped.

## Exact VM enum accessor bindings recovered offline

The full 19:55 dump contains the loaded `_BaseClientClassMethods` code at
`0xEB2A0150` (`_GetGameState`) and `0xEB2A01A0` (`_SetGameState`). The bytes
surrounding Jedipedia's placeholder calls are exact matches, while the loader
has patched each `E8` displacement to its live native binding. Translating the
targets by the dump's executable image base proves:

- `HM.RefNodeFieldEnum` -> static VA `0x005DED60`;
- `HM.SetNodeFieldEnum` -> static VA `0x005D9FF0`.

This invalidates the earlier `0x004F5C90` generic-setter hypothesis. That
candidate has been removed from the hook. Static disassembly of the verified
setter matches the generated call contract: it receives node, field operand,
and enum value; resolves the node and field; then passes the address of the
third argument into the typed assignment routine at `0x004D16F0`.

The replacement observer detours only the verified `0x005D9FF0` binding, logs
the natural node/field/value arguments, and forwards them unchanged. In
particular, `_SetGameState(GAMESTATE_WithinArea)` is expected to produce field
operand zero and enum value 4. This is now a precise discriminator rather than
a guessed native boundary. The hook builds successfully with zero warnings or
errors.

## 21:48 `_SetGameState` verified live

The filtered run is preserved as
`Diagnostics/world-entry-setgamestate-verified-20260924.log` and
`Diagnostics/world-entry-setgamestate-verified-hook-20260924.log`. Unlike the
preceding unfiltered run, the observer validated the unique loaded
`_BaseClientClassMethods._SetGameState` caller bytes before logging.

At 21:48:35 it recorded:

`method=_BaseClient._SetGameState fieldOperand=0 enumValue=4`

This proves that `chrPlayerCharacterClassMethods.Replication_Create` recognized
the replicated character as the local player, entered its local-player branch,
and executed `_SetGameState(GAMESTATE_WithinArea)`. The earlier hypotheses that
the callback was absent, that `Me == GetPlayerCharacterNode()` failed, or that
the stall occurred inside `_SetGameState` are rejected. `chrPlayerLoaded`
remained false and was repeatedly read afterward, but it did not gate entry
into this branch.

The client continued sending network traffic and issued the recurring
readiness operation after the verified state transition, while the loading
screen remained. The next sequential operation in the verified HeroScript is
`$BASECLIENT.RequestWorldFadeIn()`. The next discriminator is therefore its
natural call/return behavior, recovered from the already captured generated
module; no forced game-state value, CRT3, or packet response is warranted.

## Offline recovery of the loaded `Replication_Create` body

The full 19:55 dump contains exactly one generated method matching all four
Jedipedia `TrackLine` anchors at their expected relative offsets. Its runtime
base in that dump is `0xF01F0010`. The bytes establish this natural sequence:

- `+0x1213` (`AD`) precedes `_SetGameState`.
- `+0x127A` (`B0`) is reached only after `_SetGameState` returns and immediately
  precedes call-table slot `0x18`, `RequestWorldFadeIn`.
- `+0x12D2` (`B2`) is reached only after `RequestWorldFadeIn` returns.
- `+0x130A` (`B4`) proves execution continued into subsequent setup.

The compatibility launcher now has an opt-in read-only observer for these
dynamically allocated addresses. The next run therefore has a specific binary
result: no `B0` means `_SetGameState` did not return; `B0` without `B2` means
`RequestWorldFadeIn` did not return; `B2/B4` moves the investigation to the
later `setPlayerLoadingFinished(true)` path. The observer does not force game
state, create phase data, or author CRT bytes.

## `RequestWorldFadeIn` HUD gate

The recovered `sysBaseClientClassMethods` HeroScript removes an important
ambiguity. `RequestWorldFadeIn` returns without calling
`guiGfxLoadingScreenClassMethods:DoWorldFadeIn()` unless both conditions hold:

1. `GetPlayerCharacterNode()` is non-null.
2. `$HUD.guiHud2` exists and its `gfxLoaded` field is true.

The first condition is already verified by `Replication_Create` taking its
local-player branch. The second condition is not yet verified. Consequently,
reaching marker `B2` proves only that `RequestWorldFadeIn` returned; it does not
prove that the loading-screen fade-in routine was invoked. A false HUD
`gfxLoaded` value is now a concrete, testable loading-screen hypothesis and is
independent of `chrPlayerLoaded` or fabricated phase replication.

## 23:55 fade gate verified live and observer-offset correction

The validated observer armed in both generated methods. The run is preserved
as `Diagnostics/world-entry-fade-gate-verified-20260924.log` and
`Diagnostics/world-entry-fade-gate-verified-hook-20260924.log`.

The local character path produced `A2`, `A3`, and `AD`. Inside
`RequestWorldFadeIn`, line `0x332` reported `playerExists=1` and
`hudAndGfxLoaded=1`; line `0x333` was then reached, proving that
`guiGfxLoadingScreenClassMethods:DoWorldFadeIn()` was invoked.

Post-crash analysis showed that the originally configured `B0`, `B2`, and `B4`
addresses were not byte-exact instruction starts. In particular, the alleged
`B4` probe at `+0x1315` replaced the high byte of the following `HM.TrackLine`
CALL displacement with `0xCC`, producing the captured unmapped execution target
`0xBC7B20A0`. The observer caused that crash. The stack return address
`F0501326` proves execution had naturally reached the real `B4` TrackLine call;
therefore `DoWorldFadeIn` and the intervening preload call both returned.

The corrected instruction starts, verified against the dump bytes, are B0
`+0x127A`, B2 `+0x12D2`, and B4 `+0x130A`. The missing-player and unloaded-HUD
hypotheses remain rejected, but the claim that execution stalled inside
`DoWorldFadeIn` is withdrawn.

`chrPlayerLoaded=false` and missing `phsPlayerPhaseData` did not prevent the
local-player branch, `WithinArea`, the fade request, or its return. No forced
HUD flag, phase object, or packet reply is justified.

## 00:04 complete `Replication_Create` path

The corrected nine-site observer was validated offline against the reference
dump before this run. The captured client log is
`Diagnostics/world-entry-post-replication-20260925-0004.log`; the matching
server log is
`Diagnostics/world-entry-post-replication-server-20260925-0004.log`.

The live client reached A2, A3, AD, B0, B2, B4, B7, B8, and B9 in order.
Consequently, all of the following are verified:

- `_SetGameState(GAMESTATE_WithinArea)` returned.
- `RequestWorldFadeIn()` called `DoWorldFadeIn()` and returned.
- `AttachPreloadTrigger`, music-region setup, and
  `$CHARACTER.onPlayerCharacterCreated` returned.
- `$GUI_API.getApi().setPlayerLoadingFinished(true)` returned.

The externally resolved `chrPlayerLoaded` storage remained Boolean false.
This is not evidence that the local loading screen is waiting on that field:
the recovered `chrPlayerCharacterClassMethods` reads `chrPlayerLoaded` only to
control `Render` for a *non-local* replicated player, and its update handler
also explicitly excludes the local player. No client script in the recovered
set writes this field. Treat it as replicated character state whose server-side
producer remains unknown, not as the demonstrated local fade gate.

The next local gate is inside `guiGfxLoadingScreenClassMethods.DoWorldFadeIn`.
After decrementing `guiGfxLoadingFadedOut`, it reaches `CheckContinue()` only
through the string-table/repository-asset readiness branches. Those branches
inspect `guiGfxLoadingAssetLoadingTimer.timerState`,
`STBCheckForManifestLoadComplete()`, `GetRepositoryThunkRequestCount()`, and
`guiGfxLoadingStringTableTimer.timerState`. A subsequent observer must report
these actual values and whether `CheckContinue`, `PhaseNeedsContinue(false)`,
and `FadeIn` execute. It must not force them.

## Jedipedia assembly: complete loading-screen decision chain

`_JPEXTRACT/guiGfxLoadingScreenClassMethodsASSEMBLY.txt` supplies the complete
HeroMachine assembly for `DoWorldFadeIn`, `AssetLoadingTimerTick`, `FadeIn`,
`CheckContinue`, and `PhaseNeedsContinue`. The following addresses are verified
instruction starts in that export, expressed relative to each method entry.

### `DoWorldFadeIn` (`0x2D50`)

| Offset | Track line | Meaning |
| ---: | ---: | --- |
| `+0x162` | `0x135` | about to read the asset-loading timer state |
| `+0x197` | `0x136` | asset timer was state `1`; test STB manifest readiness |
| `+0x1FA` | `0x137` | STB manifest reports complete; read repository request count |
| `+0x21F` | `0x138` | repository request count is zero; call `CheckContinue` |
| `+0x25A` | `0x13A` | repository requests remain; arm the 45-second asset timer |
| `+0x3CD` | `0x143` | STB incomplete; test the string-table timer state |
| `+0x406` | `0x144` | string-table timer was state `1`; arm its 10-second wait |

The branches at generated addresses `0x2EE1`, `0x2F44`, `0x2F69`, and
`0x3150` are byte-explicit. In particular, if
`guiGfxLoadingAssetLoadingTimer.timerState != 1`, execution jumps directly to
the epilogue without calling `CheckContinue`. State `1` must not be described
as "running": elsewhere these same methods call `timer::stop` only when a
timer's state is *not* `1`, strongly identifying `1` as the stopped/off state.

### `CheckContinue` (`0x4310`)

`+0xE2` (track line `0x1DE`) is the no-player/in-conversation fallback that
calls local `PhaseNeedsContinue(false)`. `+0x11D` (track line `0x1DC`) is the
normal player path and calls `pc.CheckPhaseNeedsContinue()`.

The recovered `phsParticipantClassMethods` then does one of two things:

- if a current phase instance exists and has `On Phase Needs Continue`, it asks
  the server;
- otherwise it immediately calls local `PhaseNeedsContinue(false)`.

### `PhaseNeedsContinue` (`0x4490`)

The Boolean argument is tested at `+0x91`. False branches to `+0x2F1`
(track line `0x1E9`) and calls `FadeIn`; true reaches `+0x9A` (track line
`0x1EC`) and builds the press-space-to-continue state.

Therefore neither fabricated CRT3 nor forcing `chrPlayerLoaded` is justified.
The next read-only runtime discriminator is whether `DoWorldFadeIn` reaches
`0x136`, then `0x137`, and finally `0x138`. If it does reach `0x138`, the next
question is whether the normal `CheckContinue` path receives a phase response
or falls through locally to `FadeIn`.

### `STBLoadingTimerTick` (`0x3810`)

The appended assembly verifies that the string-table wait is bounded. Each
tick tests `STBCheckForManifestLoadComplete`; if incomplete, it compares `$NOW`
with `guiGfxLoadingAssetTimeoutAt`. Manifest completion or expiry reaches
`+0xB4` (track line `0x17A`), stops the string-table timer, and reaches `+0xE7`
(track line `0x17B`) to call `CheckContinue`. Before the deadline it returns
without changing the decision.

Thus an armed string-table timer should recover after at most ten seconds if
timer callbacks are functioning. Likewise, the recovered
`AssetLoadingTimerTick` bounds repository waiting at 45 seconds. A loading
screen that remains indefinitely points more narrowly to one of these cases:

1. `DoWorldFadeIn` exits before arming either timer;
2. a timer is armed but its callback never fires;
3. `CheckContinue` reaches the phase-request path and no response returns;
4. `FadeIn` runs but the GUI/native fade does not become visible.

## Compatibility fallback implementation

With explicit user approval, `CompatibilityLauncher.cpp` now applies one
bounded runtime compatibility patch after world travel begins. It locates the
generated `CheckContinue` method by its Jedipedia-verified prologue, verifies
the original six bytes at `CheckContinue+0x73` are exactly
`0F 84 55 00 00 00`, and replaces that conditional branch with
`E9 56 00 00 00 90`. This routes `CheckContinue` to its existing local
`PhaseNeedsContinue(false)` block and then `FadeIn`.

The patch does not bypass the preceding repository or string-table waits, does
not alter `chrPlayerLoaded`, and does not construct phase data or packets. The
trace launcher disables the now-unneeded player-field, player-loaded, and
Replication_Create breakpoint observers for this run. Offline tests pass.

## Successful Tython entry

The corrected event-path installer applied the compatibility patch live at
`CheckContinue=F0324320`, logged as:

`LoadingContinueFallback: CheckContinue=F0324320 patched to local PhaseNeedsContinue(false); asset waits preserved (event path).`

The user then confirmed successful entry into Tython. The successful logs are
preserved as:

- `Diagnostics/world-entry-success-phase-fallback-20260925.log`
- `Diagnostics/world-entry-success-phase-fallback-server-20260925.log`

This verifies that the blocking condition was on the phase-confirmation side
of the loading-screen continuation path. It also rejects `chrPlayerLoaded`,
the `WithinArea` transition, HUD `gfxLoaded`, `RequestWorldFadeIn`, and the
complete `Replication_Create` tail as causes of this particular hang. The
working compatibility solution uses the client's existing local
`PhaseNeedsContinue(false) -> FadeIn` behavior; it does not validate or decode
the incompatible captured CRT3 schema.

The successful entry run still had translation movement locked while camera
turning and the HUD worked. Its server log shows `CharacterChangeState` carried
the string `"AreaServer"`, set by an older trace-launcher experiment. The
decoded/captured packet contract and offline test use an empty string. The
trace launcher now restores `SWTOR_AREA_ENTER_STATE=`; no movement field or
packet bytes beyond that verified state-string correction are fabricated.

## Native phase-gate capture (2026-09-25)

The identified `0xE0009EBFFAA2E204` On Enter target is the Jedi Knight
`attack_of_the_flesh_raiders` story phase. Its `On Phase Needs Continue` hook
fades to black and starts the Derrin Weller ambush conversation; its `On Enter`
hook only forbids quick travel. This rules out the On Enter batch itself as a
Safe Login source and makes the absent phase-continuation path relevant to the
remaining movement lock.

One controlled run disabled `installLoadingContinueFallback`, preserving the
client's original `CheckContinue -> pc.CheckPhaseNeedsContinue` path. After
more than two minutes the hook recorded no new phase RPC. Only the established
30-second `0xF5F540F2` poll repeated. The world remained behind the loading
screen. Therefore there is no captured `CheckPhaseNeedsContinue` request from
which to infer a reply, and no response bytes are justified. The stall occurs
before RPC construction, consistent with the missing live
`phsPlayerPhaseData`/current-phase object while CRT3 is suppressed.

Evidence is preserved in `world-entry-native-phase-gate-no-rpc-20260925.log`
and `world-entry-native-phase-gate-no-rpc-server-20260925.log`. The normal
trace launcher again leaves `SWTOR_DISABLE_LOADING_CONTINUE_FALLBACK` empty,
so subsequent runs retain the verified local fade-in behavior.

## Correctly bounded phase-schema acceptance (2026-09-25)

The corrected isolated CRT1/CRT3 pair was transmitted once. The server log
records CRT1 SHA-256
`a75c5de9c0e32dc3c6602607fc79b216d687be538601d3a5f9d581bf99e08229`
and CRT3 SHA-256
`efe780d0ad25cb7bb14c110b60589a0b76e4ec86c474e910afedbc0c45f8ca7d`.
The client accepted the schema and entered the rendered Tython world without a
serialization exception. Derrin Weller and his quest marker were present.
This verifies that structures 105-107 and CRT3's original 22 value bytes plus
`00` state byte are structurally acceptable when the CRT1 bound is correct.

Translation remained locked by visible **Safe Login Immunity**, while rotation
continued to work. The server also logged that captured Safe Login Immunity
effect event 1 was suppressed, so that captured event is not the source that
creates the persistent client effect. The phase override and CRT3 opt-in were
returned to blank in the normal launcher immediately after this one-run test.

The next discriminator is precise: run the accepted phase pair with the
loading fallback disabled and observe whether the restored live phase object
allows `CheckPhaseNeedsContinue` to construct its genuine server RPC. Capture
the request only; do not invent a reply. If the request appears, its exact
method and payload provide the basis for implementing the corresponding
script-defined continuation response.
## Safe Login container lifecycle (2026-09-25)

The extracted `effContainerComponentClassMethods` establishes that replicated
effect cleanup is container-driven: `PostContainerRemove` clears cached effect
specs/tags, while `PostContainerRemoveInvalid` is the ID-only fallback. A node
destroy by itself therefore does not reproduce the normal lifecycle.

CRT2 verifies the complete relationship rather than requiring guessed data:

- node `0x1AC6F6DC0E` is the player's positive `effContainer` (CRT1 structure
  13);
- its `conContents` map is slot 1 -> `0x1AC6F6DC17` and slot 2 ->
  `0x1AC6F6DC1C`;
- `0x1AC6F6DC17` is created from Safe Login effect `/0/1`;
- `0x1AC6F6DC1C` is created from Safe Login Immunity `/0/2` and names
  `0x1AC6F6DC0E` as its parent.

CRT4 provides a captured style-8 `effContainer.conContents` replacement with
one entry, including structure number 13 and field-state byte `0x78`.
`AreaSafeLoginRemoval` reuses that exact encoding to replace the positive map
with only slot 1 and places `0x1AC6F6DC1C` in the same transaction's removed
node list. This supersedes the rejected standalone removal-list experiment.
The trace launcher enables this isolated lifecycle test with
`SWTOR_REMOVE_SAFE_LOGIN_EFFECT=1`.

## 2026-09-25 offline: what the captured stream actually transmits

`Diagnostics/Decode-Style7Replication.py` gained two read-only modes that make
the following reproducible without a client run:

```powershell
python Diagnostics\Decode-Style7Replication.py --dump-fields
python Diagnostics\Decode-Style7Replication.py --dump-objects
```

`--dump-fields` walks each transaction exactly as the existing decoder does and
stops at the replicated player record, so it never reads the tail records whose
record framing is still undecoded.  It prints every field whose state byte is
not `2`, with its CRT1-resolved name and type.  `--dump-objects` prints the node
each record creates with the class it names, and reports the offset where the
still-undecoded record flags stop the walk instead of guessing.

### Player field coverage per transaction

| Fixture | Transmitted player fields |
| --- | --- |
| CRT2 | `17 / 215` |
| CRT4 | `15 / 215` |
| CRT5-CRT11, CRT13-CRT17 | `1 / 215` (field 100, `modMetaStatComputed_Shared`) |
| CRT3 | no record for `0x4000010E218A839C` |
| CRT12 | no record for `0x4000010E218A839C` |

CRT2 transmits, in index order: `chrXpNeeded`(4), `chrScale`(11),
`chrMeleeDistance`(12), `staCharacterCoverObject`(13), `staWeaponMode`(17),
`invEquipment`(27), `chrCompanion`(30), `effContainerPositive`(31),
`chrCompanionModifiers`(103), `chrCharacterPhaseMode`(104, state 0),
`chrValor`(107), `sklPackageSpecList`(112), `tgtTargetIsTargetable`(117),
`pvpDuelingState`(118), `cbtFaction`(120), `ablUserSpellPushbackCount`(122),
`kynMsg_MoveSpeed`(126).

CRT4 transmits: `phsPhase`(25), `chrQuickTravelForbidden`(45),
`modStatComputed`(52), `statHealth`(54), `chrPlayerMoveState_EndPosition`(72),
`cbtWarzoneTeam`(94), `modMetaStatComputed_Shared`(100), `modStat_Fixed`(136),
`pvpCurrentLocationType`(141), `chrPlayerCanResurrectSelf`(154),
`chrRestXp`(170), `pvpToggleFlagTime`(186), `cbtActiveAttitudesList`(199),
`chrPlayerCharacterMovementTetherLeashLength`(200),
`chrPlayerCharacterMovementTetherAnchorPosition`(206).

### Fields that are never transmitted by any transaction

`staMobility`(9), `chrIsMe`(35), `chrCharacterPlayMode`(89),
`chrPlayerLoaded`(129), `ablUserTarget`(14), `ablUserClearCasting`(16),
`ablSkillPoints`(43), `ablUserAbilitySpecShared`(114), `ablContainer`(148),
`ablContainerAbilityRanks`(149), `ablContainerAbilityLevels`(150),
`ablPackageSpecList`(151), `ablContainerGrantedAbilityRanks`(152),
`ablContainerSkillRanks`(153), `ablUserAutoCastActive`(173),
`ablUserModalActiveSpecs`(175).

That list is the measured form of a mechanism the earlier Safe Login and
movement work had already used: a field whose state is `2` is not carried by
the replay at all, so the client keeps whatever its own constructor and scripts
supplied.  `staMobility` sits in this list, which is why the
`staMobilityFree` merge into CRT17 was required rather than optional.

### Consequence for in-world behavior

1. **Abilities are ungranted, not blocked.** CRT2 creates an `ablContainer`
   object at node `0x1AC6F6DBD7`, but no transaction ever carries any of its
   rank, level, package or grant maps.  A client whose action bar shows class
   abilities while its replicated container is empty evaluates every slot as
   unusable: greyed slot, local message, and no ability request, because the
   rejection happens before an RPC is built.  That matches the observed
   behavior and the complete absence of ability opcodes in the server's
   received-packet census.
2. **The player's phase object is absent by construction.** The launcher leaves
   `SWTOR_ENABLE_UNVERIFIED_CRT3` and `SWTOR_CRT_OVERRIDE_DIRECTORY` empty, and
   the server log records `suppressing known-incomplete CRT3`.  Therefore
   `phsPlayerPhaseData` (`0x00000017BFADF6AC`) is never created, so any
   behavior that needs the player's active-phase data - phase boundary
   transitions in particular - has nothing to evaluate.
3. **The class phase link is intact.** CRT4 creates
   `0x1AC6F6DC1F` with class `phsClassPhaseInfo`, and `phsPhase`(25) is the
   first transmitted field of CRT4 while the value region begins
   `cc 1a c6 f6 dc 1f`, the packed form of that same node.  The missing piece is
   the player phase data, not the class phase definition.
4. **CRT2 creates the surrounding subsystems but never fills them.**
   `--dump-objects 2` lists the created nodes: the `ablContainer` above, three
   `effContainer` objects (`0x1AC6F6DC0E/0F/10`, matching the positive,
   negative and other containers), `qckContainer` and eight `qckLink` nodes for
   the quickbar, `tmrContainer`, `invContainer`, `bnkContainer`,
   `eqpContainer` and `lgcAccountLegacyData`.  The structures exist; only their
   contents are missing from the replay.
5. **NPC interaction is still unexamined.** The nearby NPCs are created by
   `AreaAwarenessEntered` (`tython_blockout-4611686019869492753-1.1.aaw`,
   13488 bytes), and no decoder exists for that payload yet.
   `Diagnostics/Decode-WorldEntryPayloads.ps1` only decodes RPC blobs, so the
   NPC targetability question remains open and is the next offline target.

### Tool limitation recorded deliberately

The two new modes stop at the same record boundary the existing decoder stops
at.  CRT2 reports `walked 84/85 records` and stops at `0x19D4`, and CRT4 reports
`walked 6/11` and stops at `0x060C`, because the remaining records use a record
flag combination (metadata `0x10` together with `0x7A`) that is not decoded
yet.  Node ids and class ids printed before that offset are read from the record
header and remain valid; the tool reports the stop rather than mis-parsing the
remaining bytes.

## 2026-09-28: phase-boundary semantic run enabled

The earlier controlled client run accepted the matched reconstructed CRT1/CRT3
pair without a serialization error and rendered the world plus quest NPC. The
normal Tython trace launcher now enables that same pair through
`SWTOR_ENABLE_UNVERIFIED_CRT3=1` and
`SWTOR_CRT_OVERRIDE_DIRECTORY=Diagnostics\GeneratedPhaseCandidate`.

The loading-continuation fallback remains enabled. This run therefore tests
only whether a valid `phsPlayerPhaseData` object restores gateway/boundary and
phase-exit behavior; it does not reintroduce the already isolated final-loading
stall. Expected evidence is either a usable gateway/exit or a new phase RPC
when the player approaches or crosses the boundary. If neither occurs, the
next missing input is likely gateway/phase-instance state rather than basic
player phase-data construction.

### Result of the first semantic run

The reconstructed CRT1/CRT3 pair was emitted with the expected hashes and the
client entered the world normally. Repeated attempts to walk through the phase
door produced movement traffic only. There was no phase join, leave, continue,
or transition request for the server to answer. The collision wall beyond the
door is therefore a consequence of the client never beginning the phase-exit
transition, not the primary blocker.

The next run enables the focused `HeroClass::getField` observer for
`phsCurrentInstanceNameID`, `phsActiveInstances`, `phsActivePhaseData`,
`phsPhase`, `phsPhasedInstanceToTrigger`, `phsGatewayList`, and `phsPhases`.
This should show whether the doorway path lacks a current-instance assignment,
an active instance, or a gateway-to-trigger mapping.

The run produced no reads for those fields: like the ability modal path, these
phase scripts use compiled offsets and bypass the generic getter. The apparent
`0x852644E5` RPC occurred in the startup burst before world control was
returned, not during the later doorway attempts. Once in-world, repeated door
approaches generated movement updates only: no gateway script dispatch and no
phase-exit RPC. This localizes the failure ahead of RPC construction, most
likely to active `phsPhasedInstance`/gateway attachment or its eligibility
state. The next evidence required is the listed client script implementations
for `phsGateway`, `phsPhasedInstance`, and their phase-info dependencies.

### Concrete phased-instance proof and CRT4 candidate

The extracted scripts close that question:

- `phsGateway.TriggerEnter` resolves the doorway's stable `TriggerParam`
  through `$PHASE.GetPhasedInstanceNode`; it does nothing when that lookup has
  no active instance.
- `phsPhasedInstance.OnReplicationNodeCreate` registers
  `$PHASE.phsActiveInstances[Me.phsNameID]`, scans the already-created type-4
  triggers, and attaches `phsGateway` to the matching trigger.
- `phsClassPhasedInstance.DeterminePhaseEligibility` returns `phsCanExit` when
  the player's current phase-info points back to that instance.
- CRT4 creates phase-info node `0x1AC6F6DC1F` with parent `0x1AC688C97E`.
  Decoding CRT1's schema-bounded trailing transaction (which the earlier
  `--dump-objects` mode skipped) shows that CRT1 does create this parent—but it
  does so before Awareness 1 creates the doorway triggers. Its create handler
  therefore has no matching trigger to attach at that point.

The authoritative CRT1 record identifies the instance as
`phs.tyt_jedi_knight_masters_retreat` (`0xE000E8E230304F84`). April prototype
data confirms its exit map note, Hydra condition script, phase name ID, and
Jedi Knight class requirement. Captured structure 3 is
`phsClassPhasedInstance`; the record carries three exact
`phsPhasedInstanceToAnchor` mappings and its exact `hydRunScriptProtoId`.

`Generate-MatchedPhaseCrtCandidate.py` now produces an isolated CRT4 override
that relocates the exact 87-byte record from CRT1 to the first CRT4 record.
CRT1's trailing object count changes from 53 to 52; CRT4's changes from 11 to
12. All record bytes, including anchors, Hydra script, value sizes, and state
bits, are unchanged, and both resulting transactions walk exactly to their
ends. This placement is intentional: Awareness 1 creates the area triggers
before CRT4, while the existing phase-info child is created later in CRT4. The
next live run tests whether the reordered create handler attaches the doorway
and initiates the real exit path.

### Doorway retry result and corrected room-stream boundary

The CRT4 relocation was accepted without a serialization or script error, but
the gateway still did not fire. Repeated approaches and retreats at the phase
door produced only movement/state packets; there was no `CMsgF96DCDB0` gateway
RPC. This proves the failure remains before server-side eligibility handling.

The April Tython area data identifies the exact static engine trigger in room
`gnarls_new`: instance `4611686037462170014`, `TriggerClassType` equal to
`INSTANCE_GATEWAY`, `TriggerParam` equal to
`tyt_jedi_knight_masters_retreat`, and position
`(-63.6167984009,-6.73430013657,-126.88469696)`. Its parameter corresponds to
the active phase ID `0xFF5F184AAA9ECE77`.

Awareness 1 creates 35 `hydTriggerEntity` nodes only; it does not establish
this static gateway. Awareness 2, sent after CRT10, creates the `gnarls_new`
room object. Therefore CRT4 was still too early. The diagnostic generator now
removes the exact phase-info child from CRT4 and emits the unchanged 87-byte
phase-instance record followed by the unchanged 48-byte child record at the
front of CRT11, immediately after Awareness 2. This preserves parent-before-
child order while rerunning `OnReplicationNodeCreate` after the room gateway
has been streamed.

The subsequent out/in/out live test produced unchanged behavior and no
doorway-correlated gateway RPC. CRT11 was accepted without a script or native
exception, so replication order alone is now ruled out as a sufficient fix.
The complete checkpoint, preserved log hashes, confirmed trigger data, and
ranked next steps are in `Diagnostics/PhaseExit-Checkpoint-20260928.md`.



2026-09-30 correction: native style7 class field states are ONE bit per field; style8 TWO bits. Previous shared two-bit decoder invalidates style7 field-selection reports. Explicit style support and main/dump callers corrected. Old phase-clear style7 mask selected51 chrCurrentInteraction, not25 phsPhase. Serializer now style8, one-byte change only, opt-in. Experiment14 prepared; native regression and relevant packet tests pass, existing fade-in observer offline failure remains. Live outcome pending. See Diagnostics/PhaseFormat-20260930/FINDING.md.
