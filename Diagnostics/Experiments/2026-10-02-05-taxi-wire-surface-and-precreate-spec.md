# Taxi record: definitive finding — the payload was never the problem

Date: 2026-10-02. Confidence: **Client-derived** (read from the April native
client's own `Replication_PreCreate` handler plus the shipped GOM schema).

## The taxi's entire replicated surface is TWO fields

Cross-checking every field the authored node
`_JPEXTRACT/npc.location.tython.taxi.jediretreat_pad1 (hex).json` sets against
the struct-66 wire schema from CRT1:

    IN WIRE SCHEMA: 2 of 23 authored fields
      idx32  taxTerminalSpec   0xE000DC42A2436F58
      idx69  brkResourceName   0xE000AC918E7EA883  (cnv.misc.vendor.droid_taxi_military_rep)

    NOT REPLICATED (21) — client resolves these from the template:
      npcFaction, npcClassPackage, npcVisualDataList, npcAppearanceOverride,
      chrNonPlayerCharacterSpec, npcParentSpecId, locTextRetrieverMap,
      chrNPCGenderComplete, the behaviour packages, and the hydra-script ref
      0xE00027A1D57DB33F (hyd.location.tython.taxi.inst_jedi_retreat_taxi_unlock).

Our record already sends BOTH wire fields with authored-exact values, and
`template_id = 0xE0008B8CC0FAEA1D` is also correct. **No field edit can change
the outcome.** This retires the whole record-tuning line of attack.

## Where the character spec actually comes from

`_JPEXTRACT/Replication_PreCreate_ASSEMBLY.txt` (script 14988055391397265151,
line 334 — the exact line in the `Char spec missing` traceback):

    if ( HM.TrackLine(327), HM.IsKindOf(Me, 0xDFFE8888) )   // visible_character
    {
      NodeRef node = HM.ConstructNodeRef(8);
      Id id1 = HM.GetNodeRefID(Me);
      &vec  = HM.RefNodeFieldVector3(Me, 5);               // position
      &vec2 = HM.RefNodeFieldVector3(Me, 6);               // rotation
      &node = EF.CreateReplicatedCharacter(CurrentInterface, id1, vec, vec2);

      Integer int1 = HM.RefGlobalConstantInt(4);
      if ( HM.IsKindOf(Me, 4611686018433070017uLL) )       // chrPlayerCharacter
        int1 = HM.RefGlobalConstantInt(5);

      HM.TrackLine(334);
      NodeRef  node2  = HM.CopyConstructNodeRef(27, Me);
      String   str    = HM.ConstructString();
      Integer  int2   = HM.RefNodeFieldInt(Me, 7);          // <-- field index 7
      String   str2   = HM.ConvertToStringInt(int2);
      &str    = chrSpecToString(str2);                     // script 14988055391397265151
      EF.SetCharacterSpec(CurrentInterface, node2, str, int1);
    }

The spec is built from **field index 7** (`staCurrentBrain` in the struct-66
field table) run through a `ConvertToStringInt` + script lookup, then handed to
`EF.SetCharacterSpec` as a STRING. It is not an ID, and it is not
`chrNonPlayerCharacterSpec`. `Unknown spec(0)` therefore means field 7 resolved
to 0 (or to an unmapped int) on the client — a content-table lookup, not a
missing value in our packet.

## What is still missing, precisely

`EF.CreateReplicatedCharacter` is called with a NODE REF that the server did not
create, and `chrSpecToString` maps an int to a spec STRING. Both are client-side
resolutions. Our record carries field 7 = `staCurrentBrain` = **0** (absent).

# ROOT CAUSE of the value-walk desync: field 33 tmrContainer, a 1-byte ClassRef

2026-10-02. This is the defect that made every character record (vendor struct
64 and taxi struct 66) fail `walk_record`, and it is NOT the LookupList encoding.

## The walk, field by field, on the captured VENDOR (known-good production data)

     0 character_position   kinds=[18]  +12  -> body+0    vec(-59.79,-6.90,-128.x)
     1 character_rotation   kinds=[18]  +12  -> body+12
     9 chrScale             kinds=[4]   +4   -> body+24   1
    10 chrMeleeDistance     kinds=[4]   +4   -> body+28   0.1
    13 staWeaponState       kinds=[5]   +1   -> body+32   enum=2
    22 phsPhase             kinds=[1]   +1   -> body+33   1
    23 eqpEquipment         kinds=[15]  +6   -> body+34   ref=0x1AC68957ED
    24 effContainerPositive kinds=[15]  +6   -> body+40   ref=0x1AC68957EF
    25 effContainerNegative kinds=[15]  +6   -> body+46   ref=0x1AC68957F0
    26 effContainerOther    kinds=[15]  +6   -> body+52   ref=0x1AC68957F1
    27 spnParentAnchorId    kinds=[1]   +9   -> body+58   4611686101695870302
    30 vndVendorCanRepair   kinds=[3]   +1   -> body+67   204
    33 tmrContainer         kinds=[15]  +1   -> body+68   ref=0x1A     <-- WRONG

Raw bytes at body+67:  `1a c6 88 d5 42 aa cf 40 00 00 03 98 6e`

## Diagnosis

`tmrContainer` is kind 15 (ClassRef), the same kind as fields 23-26, all of which
decode as 6-byte packed tokens. But at body+67 the walker reads `0x1A`, treats it
as a literal packed integer (< 0xC0) and consumes ONE byte, leaving the stream
one byte short from that point onward.

The real layout is almost certainly:

    body+67  c6 88 d5 42 aa cf   -> 5-byte token, value 0x88D542AACF
    body+72  40 00 00 03         -> next field

after which field 34 begins at body+73 and the 9-byte token
`c6 89 57 ec 3e 02 00 00 00` reads as a coherent value rather than noise.

So the desync is ONE byte at ONE field, not the modStatComputed map encoding. A
brute-force over (count mode x entry size) for that map correctly found no
solution, because the map was never the problem — the walk was already lost
before reaching it.

## Why this matters

- Both the vendor and our taxi fail at the SAME field for the SAME reason. That
  is why no character record ever reconciled, and why every byte span read out
  of one was untrustworthy — including the `_characterSpecification = 154` and
  the "5 NPCs send 0" readings, both since retracted.
- The likely culprit is `packed()` treating 0xC0..0xC7 as literal. It is
  documented that only 0xC0..0xC7 are invalid and 0xC8..0xCF carry 1..8 bytes,
  and `Decode-CrtValues.packed()` already implements that correctly. So the bug
  is probably in how `part()`/`_sequence()` is called for this field, or in a
  second, inconsistent packed reader. Check `d.Reader.packed()` in
  Decode-Style7Replication.py -- it has a DIFFERENT token table from
  Decode-CrtValues.ValueWalker.packed():

      Decode-Style7Replication.Reader.packed:  0xC8..0xCF -> (token - 0xC7) bytes
      Decode-CrtValues.ValueWalker.packed:      0xC8..0xCF -> (token - 0xC7) bytes
      ...but 0xC0..0xC7 raise in both. `0xC6` is INVALID as a leading token.

  A leading `0xC6` cannot be a valid packed token, which means field 33 does NOT
  start at body+67 either. The preceding field (30 vndVendorCanRepair, kind 3
  Boolean) is consuming the wrong number of bytes, and the true field-33 start is
  further along. Booleans may not be a plain 1 byte in this encoding.

## Next step, precisely

Resolve the kind-3 (Boolean) and kind-15 (ClassRef) widths by locating the field
boundaries empirically: for each present field, try all plausible widths and pick
the assignment under which the ENTIRE record walks to exactly inner_size. That is
the same reconciliation oracle used above, applied across all fields rather than
just the map. This is tractable offline and needs no client run.

Consequence for the taxi: until this is fixed, no statement about any value in a
character record is admissible, and no fixture edit is safe.

---

# Static disassembly of EF.SetCharacterSpec is not possible from the exe — and why

2026-10-02. Toolchain verified working; the blocker is structural, not tooling.

## What works

    exe    : nexusclient/nexusclient/swtor-emu.exe   (17 MB, dated 2012-04-12)
    image  : base 0x00400000
    pefile 2024.8.26 + capstone installed
    Diagnostics/Disasm-Range.py is functional against this exact binary

So the April client binary IS on disk and IS analysable. The earlier assumption
that "no disassembly is available" was wrong.

## What the search found

Searching for the engine builtin names, both ASCII and UTF-16, over all
17,862,496 bytes:

    SetCharacterSpec            ascii=0  utf16=0
    CreateReplicatedCharacter   ascii=0  utf16=0
    AddCharacterSpec            ascii=0  utf16=0
    chrSpecToString             ascii=0  utf16=0
    _Room_Activate              ascii=0  utf16=1   at file 0x0cbd148   <-- found

Method validated by the positive control (`_Room_Activate` was located by the
earlier PhaseLifecycle session at exactly this offset).

## Why the EF.* builtins are not in the exe

The addresses in `_JPEXTRACT/Replication_PreCreate_ASSEMBLY.txt` (0x2760..0x29F8)
are offsets inside a **compiled HeroMachine script blob**, not exe virtual
addresses. The calls look like:

    00002953  E8 FC FF FF FF  CALL 0x00002954  !EF.SetCharacterSpec(...)

`E8 FC FF FF FF` is call-to-next-instruction — a placeholder immediate, not a
real target. The Jedipedia decompiler emits it to mark an unresolved engine
builtin. The actual destination is bound at runtime from a builtin registry that
is not stored as plain strings in the exe.

Consequences:

- Static xref of `EF.SetCharacterSpec` inside swtor-emu.exe is not possible.
- Resolving it requires either (a) the compiled script blob's builtin fixup
  table from `client.gom` (526 KB, present at `_JPEXTRACT/Client.gom/client.gom`),
  or (b) a runtime hook — and the repo already has a client hook project
  (`Client/Hook/Src/ToR.cpp`, `MemoryMan.pdb`) capable of intercepting the call.

## Recommendation

The hook route (b) is the realistic one: intercept the `EF.SetCharacterSpec`
call site at runtime and log the `a2` spec string the client computes for the
taxi node. That answers "what spec string does the client derive for our node"
directly and empirically, which is the one question the taxi investigation has
been unable to answer from static content.

Do NOT attempt further static string searches for EF.* names — that avenue is
exhausted and returns zero by construction.

2026-10-02. Source: `_JPEXTRACT/Automaton.txt`, which is the missing link.

## The two paths are different

`GetPlayerInfo` (line 470-474) — the PLAYER path:

    if ( pc2 is kindof 0xDFFE8888 )                      // visible_character
      chrSpecToString(str117, pc2._characterSpecification)
      str = str + ";specification:" + str117

`GetNPCInfo` (line 540-556) — the NPC path:

    if ( node2 is kindof chrNonPlayerCharacter )
      var id3   = node2.chrNonPlayerCharacterSpec        // <-- different field
      var str51 = utlFQN:fromID(id3)
      str = str + ";npcspec:" + str51

**`chrSpecToString` is never called on an NPC.** It is called only for
`visible_character` in the player-info diagnostic, where the argument is a
decimal string from a small int against a table keyed by 64-bit ids — so it
always yields `Unknown spec(N)`. That is a broken debug/diagnostic string in the
April client, and it is emitted while formatting `/automaton getplayerinfo`.

## Consequences for the taxi investigation

1. The three log lines `Char spec missing: Unknown spec(0)`,
   `Mag node doesn't have a valid asset spec`, and
   `Node is not a MAG node ...` are NOT explained by the taxi's spec field, and
   are NOT cleared by changing it. Every hypothesis in this experiment that
   treated them as a payload symptom is void.
2. `_characterSpecification` (struct 66 idx 77) is a player/visible-character
   diagnostic field. It is not how an NPC acquires a model.
3. An NPC's model identity comes from `chrNonPlayerCharacterSpec` — the field
   that **is not replicated** (confirmed against the CRT1 struct-66 schema: it
   is absent from every loaded schema, so it cannot be sent). The client must
   resolve it from the node's `template_id`.

## Honest status of the session

The taxi NPC still does not render. What is now established:

- Our record's two replicated fields are authored-exact and verified present:
  `taxTerminalSpec` = 0xE000DC42A2436F58 (body+59),
  `brkResourceName` = 0xE000AC918E7EA883 (body+354).
- Struct 66 is chrNonPlayerCharacter + aiCharacterAgentOverride + spnSpawned +
  brkOwner + taxTerminalComponent; the only delta from the rendering vendor
  (struct 64) is the taxTerminalComponent glom.
- The remaining unresolved item is whether the client resolves
  `chrNonPlayerCharacterSpec` from `template_id` correctly for this node. That
  is a client prototype-resolution question, not a payload question, and it
  cannot be answered by editing the record.

**No fixture change was made.** TaxiNpc.bin and TaxiRecord1.bin are unchanged;
TaxiRecord2.bin was never created. Every proposed edit was withheld because the
guard in the generator failed or the supporting evidence was retracted.

## Do not resume

- Field-editing struct 66 to fix the script errors (void: player-side diagnostic).
- `chrNonPlayerCharacterSpec` as a sendable field (not in the wire schema).
- Re-sending awareness/CRT batches as room streaming (already a proven dead end).

The correct next investigation is template/prototype resolution client-side:
does `getPrototypeByID(0xE0008B8CC0FAEA1D)` resolve on the April client? That is
`EF.CreateReplicatedCharacter` / `SetCharacterSpec` disassembly, which requires
the native binary rather than Jedipedia script extracts.

---

# SUPERSEDED (kept for history): earlier notes in this file

The sections below predate the Automaton finding. Their central claim — that
`chrSpecToString` failing explains the taxi's invisibility — is **incorrect**.
They are retained only so the reasoning is not silently repeated.

2026-10-02, from `_JPEXTRACT/chrSpecPrototype.json` (id 16140950676526056934 =
0xE0002D1F336FC5E6), field `4611686086145961602` = `chrSpecs`.

## The table

    chrSpecs: 74 entries
    smallest key : 315573855060758291  (0x046124BFCB4C0F13)
    largest  key : 18222809182691790341 (0xFD0A...)
    ALL keys are 64-bit values > 1e17. None is a small integer.

    sample entry 315573855060758291:
      chrSpecPath            \art\dynamic\spec\
      chrSpecString          ithorian
      chrSpecMeleeDistance   0.10
      chrSpecAbilityPackage  16140956447857218754

So `chrSpecs` is keyed by the same 64-bit node-id space as every other authored
reference, and `chrSpecString` holds the model suffix (`ithorian`, i.e. the
`.dat` basename used by `_PreloadAllCharacterSpecs`).

## Consequence: the taxi error is unavoidable on this path

`_JPEXTRACT/chrOracleClassMethods.txt`:

    public function chrSpecToString(a1 as String) as String
      var lookup = $STATIC.chrSpecPrototype.chrSpecs
      if lookup has a1
        return lookup[a1].chrSpecString
      else
        return "Unknown spec(" + a1 + ")"
      .

`_JPEXTRACT/Replication_PreCreate_ASSEMBLY.txt` (line 334) calls it as:

    String str2 = HM.ConvertToStringInt(int2);   // int2 = RefNodeFieldInt(Me, 7)
    &str = chrSpecToString(str2);

The argument is a decimal STRING built from a small int. The table is keyed by
64-bit ids. **No int can produce a matching string key.** Neither `0` nor `154`
nor any other small value can ever hit, because the keys are all > 1e17.

Therefore `Char spec missing: Unknown spec(N)` is emitted for EVERY character
that enters `Replication_PreCreate`, regardless of what the server sends. It is
not a symptom of our payload, and no value of any replicated field can clear it.

## Why the taxi is invisible while the vendor renders

Working NPCs resolve their model through the template/`brkResourceName` path and
never depend on the `chrSpecToString` result. The taxi DOES enter
`Replication_PreCreate`'s branch, hits the broken fallback, and receives a
literal error string in place of a spec — hence:

    Char spec missing: Unknown spec(N)
    Mag node doesn't have a valid asset spec   <- no spec -> no model
    Node is not a MAG node ...                  <- no model -> no animation

One cause, three errors, in order. `AddCharacterSpec` was never called with a
real path for this node, so nothing was ever registered in the client's model
table.

## What this closes

- `_characterSpecification` (struct 66 idx 77): present and correct in kind. Its
  value cannot be validated as a `chrSpecs` key because the script path that
  reads it stringifies first. Do not edit it on the assumption it is a small int.
- Every prior rung in this experiment was chasing a payload field. The fault is
  in a client script fallback that is unreachable-by-design for any value.

## Next step (if any)

The only remaining avenue is to keep the taxi OUT of the `visible_character`
`Replication_PreCreate` branch, or to make the client take the working path. The
gate is:

    if ( HM.IsKindOf(Me, 0xDFFE8888) )   // visible_character

`_characterSpecification` is itself a member of `visible_character`. If the taxi
node were classified as `chrNonPlayerCharacter` WITHOUT that interface, the
broken branch would not run. That is a class/interface question, not a field
question, and it is the only untested hypothesis remaining.

Supporting detail now available: struct 66 = chrNonPlayerCharacter +
aiCharacterAgentOverride + spnSpawned + brkOwner + taxTerminal. Struct 64 (the
vendor, which renders) = chrNonPlayerCharacter + aiCharacterAgentOverride +
spnSpawned + brkOwner + vndVendor. The glom sets are otherwise identical, so if
`visible_character` is reached through one of them specifically, that is where to
look.

The section immediately below reports that five rendering NPCs in captured
awareness set 1 carry `staMobility = 0` / `_characterSpecification` absent, and
uses that to retire the `staMobility` theory. **That reading came from the same
value walk that does not reconcile, so it was not evidence. It is retracted.**

Calibration of `Diagnostics/Decode-CrtValues.py::walk_record` over all 77 records
of captured set 1:

    struct 41 (hydTriggerEntity, 2 fields)   -> reconciles, 26x
    struct 13 / 11 / 14 / 15 (containers)     -> reconciles, ~40x
    struct 42 (chrNonPlayerCharacter, 92 f)   -> FAILS
    struct 64 (chrNonPlayerCharacter, 96 f)   -> FAILS
    struct 65 (plcPlaceable, 20 f)            -> FAILS (33/148 consumed)
    struct 48 (dynPlaceable, 24 f)            -> FAILS (kind 9 unhandled)

The split is exactly "small schemas reconcile, character-sized schemas do not".
That is a decoder limitation, not a property of the captures. Consequences:

1. `staMobility` is **NOT** retired — it is unevaluated. Re-open it.
2. `_characterSpecification` **is present** in all five rendering NPCs
   (struct 42/64) as well as in our taxi (struct 66). Only the VALUES are unread.
3. The taxi's `_characterSpecification = 154` came from a walk that consumed only
   283 of 388 value bytes, so that number is provisional too.

What is NOT affected: the field identification. `_characterSpecification` is
declared in client.gom, is a member of `visible_character`, is typed Int, is
described as "Character specification (bmn, bfn, etc.)", and is shared with the
server DOM. It exists in schemas 42 (idx 74), 64 (idx 78) and 66 (idx 77).

## Gate before any further fixture edit

The value walk must reconcile to `inner_size` on at least one struct-42/64
record. Until then no byte span inside a character record can be trusted and any
splice is unsafe. `walk_record`'s own criterion (consume exactly `inner_size`)
is the correct gate. Open items: the LookupList entry-count encoding for
`modStatComputed` / `modStatBase` under styles 8/10, the entry size for
`chrCreatureTypeList`, and kind 9 (EmbeddedClass) support.

---

# Corrected negative result: the spec table IS present and 0 is a VALID key

Appended 2026-10-02. This **supersedes** the `staMobility` hypothesis recorded
above and is the most important finding in this experiment.

## `chrSpecPrototype` — the table is real and populated

    _JPEXTRACT/chrSpecPrototype.txt   class chrSpecPrototype (4611686061654031191)
      4611686086145961602  chrSpecs   LookupList indexed by Int of ClassView chrSpec
      4611686086145961603  chrSpecString   String
      4611686061654031194  chrSpecPath     String
      ...

    _JPEXTRACT/chrSpec.txt   chrSpec, "Stored in: chrSpecPrototype.chrSpecs",
      "Stored as: nested", client.gom present, Shared with server DOM: yes.

    utlStaticDefinitionsClass.txt:47
      Me.chrSpecPrototype = getPrototypeByID(16140950676526056934)  // 0xE0002D1F336FC5E6

So the chain `STATIC -> chrSpecPrototype -> chrSpecs[int] -> chrSpecString` is
fully populated client-side content. The lookup is real.

## `0` is a VALID key — the taxi hypothesis is DEAD

Scanning every struct-42 / struct-64 record in captured awareness set 1 (the
records that actually render: vendor, authored speeders) for a present
`staMobility`:

    rec3   struct=42  tmpl=0xE00099CA181601BE  staMobility=enum=0
    rec16  struct=64  tmpl=0xE0005CB11264F32D  staMobility=enum=0
    rec31  struct=42  tmpl=0xE0001A7B981EC3F0  staMobility=enum=0
    rec48  struct=42  tmpl=0xE00076056EC36C2C  staMobility=enum=0
    rec56  struct=42  tmpl=0xE0003CFE9836B25A  staMobility=enum=0

**All five rendering NPCs send `staMobility = 0` and resolve their character
spec successfully.** `LookupListHasInt(chrSpecs, 0)` is therefore TRUE.

Consequences:

1. `Unknown spec(0)` is NOT caused by our omitting `staMobility`, and NOT by the
   value being 0. Setting it to 0 — or to any value we could guess — cannot fix
   anything. The earlier suggestion "`staMobility = 10`" was wrong and is retired.
2. Since the string produced is `"Unknown spec(0)"`, the string arriving at
   `chrSpecToString` is the literal two-character text `0`, not the integer 0.
   `ConvertFromStringInt("0")` is what feeds `LookupListHasInt`. The failing
   input is the STRING.
3. Therefore the error originates in whichever code produced the string
   `str2` in `Replication_PreCreate` — i.e. **upstream of `chrSpecToString`**,
   inside `EF.CreateReplicatedCharacter` or the server-side creation payload
   that feeds it. Our replication record does not supply it at all.

## Where this leaves the taxi

The taxi's failure is not in any field we send. The two wire fields
(`taxTerminalSpec`, `brkResourceName`) are authored-exact, `template_id` is
correct, and the spec table is populated. The remaining suspect is the
**creation/replication handshake** (`EF.CreateReplicatedCharacter`,
`EF.SetCharacterSpec`) rather than the update payload — consistent with the
project's earlier, independent finding that `_Room_Activate` and the native
room lifecycle were never replicated.

Next step, if continuing: disassembly of `EF.CreateReplicatedCharacter` and of
`chrOracleClassMethods.IsValidCharacterSpec` (listed in chrSpecPrototype.txt as
a caller) to establish what the string must contain. Do NOT resume field-editing
the struct-66 record; that avenue is closed by the wire-surface result above.

- `_characterSpecification` (idx 77) is NOT the spec the client reads. Rung 1 was
  built on that assumption; correctly executed, correctly negative.
- `chrNonPlayerCharacterSpec` is NOT a struct-66 field; it cannot be sent.
- `taxTerminalSpec` pointing at the route record `tax.tython.poi_jedi_retreat_pathone`
  is CORRECT by design, not a bug. The hydra `inst_jedi_retreat_taxi_unlock`
  writes those same route ids into `taxKnownTerminals`, which is exactly what
  `AreaTaxiInteraction` already sends.
- `chrAppearanceNppOverride` / `spnSpawnedSpec`: authored-absent and wire-present
  only in our synthesized record. Removing them is authored-exact but cannot
  affect a failure whose cause is upstream of the payload.

# RESOLVED: the field widths — every character record now walks to inner_size

2026-10-02. Confidence: **Behavior-verified** (the walk consumes exactly
`inner_size` for 75/77 records in the captured set, including the vendor and
every struct-42 NPC). The prior blocker — "no statement about any value in a
character record is admissible" — is retired.

## The grammar, verified against the captured vendor

Oracle is unchanged: the walk must consume exactly `inner_size`. The vendor
(node `0x1AC68957EB`, struct 64, style **8**, inner_size **380**) now consumes
**380/380**, and its tail matches `Decode-AppearanceTail.py`'s independent split
byte-for-byte.

    kind 3  Boolean   present carries ZERO value bytes (the 2-bit state is the
                      value).  This is why the old walker read 0xCC as
                      vndVendorCanRepair and mis-placed tmrContainer.
    kind 5  Enum      PACKED integer, variable width, not a fixed byte. Map keys
                      232/233/254/255 are the 0xC8+1 form.
    kind 1  UInt64    packed.
    kind 2  Int64     signed packed (0xC0..0xC7 = negative, 8-byte payload).
    kind 15 ClassRef  packed (0xCC + 5 bytes = a 6-byte node ref).
    kind 17 Timer     packed.
    kind 6  String    packed length + that many bytes.
    kind 4  Float     4 raw little-endian bytes.
    kind 18 Vec3      12 raw little-endian bytes.
    kind 8  Map       style 8/10 only: count = packed value HALVED, then
                      count x (key + value). Style 7: count is literal.
    kind 7  List      style 8/10: optional leading packed spec id (only when the
                      next byte is 0xCF), then the packed count HALVED, then
                      count x (packed entry index + element).

## How each wrong guess was eliminated

  * Boolean width. With 1 byte, f30 `vndVendorCanRepair` ate the 0xCC that
    begins f33's ref and f33 `tmrContainer` decoded as `0x1A`. With 0 bytes,
    f33 starts one byte earlier and reads `cc 1a c6 89 57 ec` = node
    `0x1AC68957EC`, and the record stays aligned.
  * Enum width. `modStatComputed` (Map<Enum,Float>) has keys 232/233/254/255
    written as `c8 e8`/`c8 e9`/`c8 fe`/`c8 ff`. A fixed 1-byte enum desyncs
    there; a packed enum lands exactly on the next count byte.
  * Count halving. `modStatComputed`'s count token is `0x3E`; 0x3E>>1 = 31
    entries and the last entry ends precisely on `0x1E`, which is
    `modStatBase`'s count. Literal 62 entries runs off the field.
  * List shape. `chrCreatureTypeList` (struct64 idx 62, `List of Enum
    npcCreatureType`) is exactly 12 bytes:
    `cf e0 00 5c b1 12 64 f3 2d 02 01 01` = spec id 0xE0005CB11264F32D, count
    0x02 (->1), entry index 0x01, enum 0x01. Treating the 0xCF as a count
    produces an absurd 0xE0005CB11264F32D and fails.

## Evidence and tooling

  * `Diagnostics/TaxiDevelopment-20261001/Solve-CharacterWalk.py` — global
    grammar search; scores every assignment against all 77 records.
  * `Diagnostics/TaxiDevelopment-20261001/Solve-TailWidths.py` — per-field
    width DFS with the resolved grammar as `ref_walk`; `report_reference()`
    scores the four List variants (A/B/C/D) and B wins at 75/77.
  * `Diagnostics/TaxiDevelopment-20261001/Crosscheck-Weller.py` — independent
    cross-check on `tython_blockout-...-1.2.aaw`.
  * `Diagnostics/TaxiDevelopment-20261001/weller-crosscheck.txt`,
    `characterwalk-solutions.txt`, `tailwidth-solutions.txt`.

## What this does and does not establish

  * The vendor's decoded tail is confirmed sane: `cbtFaction` =
    -878620586690540766 (the taxi prototype's `npcFaction`), `chrLevel` = 10,
    `brkResourceName`/`chrClass` are 0xE0.. ids. The earlier independent
    `Decode-AppearanceTail.py` split is corroborated.
  * NOT established: a rendering cause. The grammar says our two wire fields and
    the surrounding record parse correctly; it says nothing about why the client
    does not draw the droid. No fixture was edited.

## Still open (deliberately not chased here)

  * The two struct-48 `dyn`/`dynPlaceable` records do not reconcile (under by
    3481 bytes). They are not character records. Their failure is now named:
    the body contains a String list of asset names - the literal ASCII
    `..._collision_forward_wingsup.gr2` is read as a length-prefixed string the
    current walker skips, so everything after it collapses. Separately from the
    List rule above, this needs its own pass over `dynVisualList` /
    `dynCollision*`.
  * Weller's struct-62 record walks correctly to +349/429 and stops on a `0xD2`
    token. `DeserializeLookupList.GetKeyString` documents 210 (0xD2) as a
    string-key marker, so a String-keyed LookupList such as
    `cnvAlienConversationsRequiredLookup` needs its own rule. This is an
    encoding detail of a *different* field family, not a character-field width.
  * The shared `Decode-CrtValues.py` walker was intentionally NOT modified.
    Its Boolean/Enum handling is style-agnostic and style-7 records still
    require the one-byte Boolean, so changing it risks the 16/16 container gate
    (verified 16/16 before and after this session). The resolved grammar lives
    in the self-contained walker above.
