"""Generate a CRT value body, and prove it against the captured bytes.

Decode-CrtValues.py reads a record's value body. This writes one. The two are
inverses, and the proof is exact: re-encoding a decoded record must reproduce
the captured value bytes byte-for-byte, plus the identical field-state
bitstream. Anything less is a failure, not a near-miss.

That matters because the server currently patches captured fixtures at fixed
offsets (see SharpServer/NET/Packets/Server/AreaSafeLoginRemoval.cs, which
asserts e.g. captured.Length == 0x198F and throws otherwise). A generator makes
a record's length a function of its fields instead of a constant that has to be
re-derived whenever a capture is retaken.

Usage:
    python Generate-CrtValues.py --containers    # round-trip every container
    python Generate-CrtValues.py --player        # round-trip chrPlayerCharacter
"""

# Known gap. chrPlayerCharacter (structure 26) does NOT yet round-trip: 0/14.
# The container gate is the one that gates regressions. See "Player record" at
# the bottom of this file for what is known and what is not.
PLAYER_ROUNDTRIP_KNOWN_GOOD = False

import argparse
import importlib.util
import struct
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "d7", Path(__file__).with_name("Decode-Style7Replication.py"))
d7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d7)

spec2 = importlib.util.spec_from_file_location(
    "dc", Path(__file__).with_name("Decode-CrtValues.py"))
dc = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(dc)

ValueWalker = dc.ValueWalker
WalkError = dc.WalkError


class EmitError(Exception):
    pass


def pack_int(value):
    """Encode an integer the way PackedStream.Write(out ulong) does.

    Inverse of ValueWalker.packed. Below 0xC0 is a literal single byte; above
    that, 0xC8..0xCF carry 1..8 big-endian bytes. The shortest encoding wins,
    matching the reference writer in Tools/Hero/Hero/PackedStream.cs.
    """
    if value < 0:
        raise EmitError(f"negative value {value} has no packed form")
    if value < 0xC0:
        return bytes([value])
    for count in range(1, 9):
        if value < (1 << (8 * count)):
            return bytes([0xC7 + count]) + value.to_bytes(count, "big")
    raise EmitError(f"{value} does not fit in 8 packed bytes")


class Part:
    """A schema part plus the decoded value it should emit.

    The decoder walks a `structure.fields[i].parts[0]` chain; this carries the
    parsed value alongside it so emit does not have to re-derive the mapping.
    """

    __slots__ = ("kind", "value", "count", "children", "flag", "double")

    def __init__(self, kind, value=None, count=0, children=None):
        self.kind = kind
        self.value = value
        self.count = count
        self.children = children if children is not None else []
        self.flag = 0
        self.double = False


def _doubles(part, style):
    """Styles 8 and 10 store container counts doubled; style 7 does not.

    This is the same discriminator Decode-CrtValues.field_states applies, and
    CRT4 is the reference case (style 8, two effContainer maps).
    """
    return style in (8, 10)


def emit_part(out, part):
    """Append one part's value bytes. Inverse of ValueWalker.part."""
    kind = part.kind
    if kind in (1, 2):                      # UInt64 / Int64
        out += pack_int(part.value)
    elif kind == 3:                          # Boolean
        out += bytes([1 if part.value else 0])
    elif kind == 4:                          # Float
        out += struct.pack("<f", part.value)
    elif kind == 5:                          # Enum
        out += bytes([part.value & 0xFF])
    elif kind == 6:                          # String
        raw = part.value.encode("utf-8") if isinstance(part.value, str) else part.value
        out += pack_int(len(raw)) + raw
    elif kind == 15:                         # NodeRef
        out += pack_int(part.value)
    elif kind == 9:                          # Class (HeroTypes.Class)
        out += pack_int(part.value)
    elif kind == 18:                         # Vec3
        out += struct.pack("<3f", *part.value)
    elif kind == 17:                         # Timer
        out += pack_int(part.value)
    elif kind in (7, 8):                     # List / Map
        # Styles 8/10 store Count*2 with the low bit as a separate flag
        # (SerializeLookupList.cs writes Count*2, Count*2). parse_container
        # stored the already-halved entry count plus the low bit in .flag, so
        # re-doubling restores the captured byte exactly -- 0x0D for six
        # entries with the flag set, not thirteen.
        count = part.count << 1 if part.double else part.count
        if part.double and part.flag:
            count |= 1
        out += pack_int(count)
        # parse_container stored children in wire order: for a Map that is
        # key, value, key, value -- so no key re-emission here.
        for child in part.children:
            emit_part(out, child)
    else:
        raise EmitError(f"cannot emit kind {kind}")


class _Holder:
    """Adapts a TypePart list to the Field interface parse_container expects.

    parse_container treats field.parts[0] as the container spec and the rest as
    entry parts, so a nested container needs a synthetic holder that puts its own
    spec first and the parent's remaining parts after it.
    """

    __slots__ = ("kind", "parts")

    def __init__(self, spec_part, rest=None):
        self.kind = spec_part.kind
        self.parts = [spec_part] + list(rest or [])


def parse_part(walker, container, index, style):
    """Read one part of a List/Map into a Part ready for emit_part.

    ``container`` is the TypePart holding child parts; ``index`` selects within
    it. For a Map, parts are [8, key, value], so the key is index 0 and the
    value index 1. Styles 8/10 store the count doubled, matching
    SerializeLookupList/DeserializeLookupList, so it is halved on read and
    re-doubled on write.
    """
    if index >= len(container.parts):
        raise WalkError(f"kind {container.kind} has no element part at {index}")
    spec_part = container.parts[index]
    kind = spec_part.kind
    if kind in (1, 2):
        if ValueWalker.INT64_MODE == "fixed8":
            return Part(kind, int.from_bytes(walker.raw(8), "little"))
        return Part(kind, walker.packed())
    if kind == 3:
        return Part(kind, walker.byte())
    if kind == 4:
        return Part(kind, struct.unpack("<f", walker.raw(4))[0])
    if kind == 5:
        return Part(kind, walker.byte())
    if kind == 6:
        return Part(kind, walker.raw(walker.packed()).decode("utf-8", "replace"))
    if kind == 15:
        return Part(kind, walker.packed())
    if kind == 9:
        # HeroTypes.Class. DeserializeClass.cs reads a single packed value when
        # the stream does not set Flags[4] (styles 7/8 use that path); the
        # Flags[4] branch is NotImplementedException in the reference and is not
        # reachable here. The player record has several of these -- socSocial
        # Component and others -- and the walker previously had no rule for them,
        # which is what desynchronised the value stream and produced the
        # spurious "invalid packed token" failures downstream.
        return Part(kind, walker.packed())
    if kind == 18:
        return Part(kind, struct.unpack("<3f", walker.raw(12)))
    if kind == 17:
        return Part(kind, walker.packed())
    if kind in (7, 8):
        # A container nested as a Map value or List element. It carries its own
        # count, so it needs a synthetic Field whose parts start at this spec.
        # parse_container reads field.parts[0] as the container kind and treats
        # the rest as entry parts, so the synthetic holder puts the spec first
        # and the element parts after it.
        holder = _Holder(spec_part, container.parts[index + 1:])
        return parse_container(walker, holder, style)
    raise WalkError(f"unhandled kind {kind}")


def parse_container(walker, field, style):
    """Read a whole List (kind 7) or Map (kind 8) field value.

    The Field's parts are [container-spec, key, value] for a Map and
    [list-spec, element] for a List. parts[0] is the container kind itself, not
    an element, so entry parts start at index 1. This mirrors how
    Decode-CrtValues._sequence walks from first_element=1.

    A part that is itself a container (a LookupList nested as a Map value, which
    is what f100 modMetaStatComputed_Shared has: parts [8, 2, 8, 5, 4]) is read
    as its own counted sub-container, per DeserializeLookupList, which reads
    m_0C and Count for every level rather than sharing the parent's count.

    Styles 8 and 10 store the count doubled with the low bit as a flag
    (SerializeLookupList.cs writes Count*2), so the real entry count is the
    value halved. That is why a leading 0x0D means six entries, not thirteen.
    """
    spec = field.parts[0]
    raw = walker.packed()
    part = Part(spec.kind, count=raw)
    part.double = style in (8, 10)
    if part.double:
        # DeserializeLookupList.cs: m_30 = (Count & 1) == 1; Count >>= 1.
        # Store the halved ENTRY count plus the flag, so emit_part can restore
        # the exact captured byte -- 0x0D is six entries with the flag set.
        part.flag = raw & 1
        part.count = raw >> 1
    entries = part.count
    entry_parts = len(field.parts) - 1          # 2 for a Map, 1 for a List
    for _ in range(entries):
        for offset in range(entry_parts):
            part.children.append(parse_part(walker, field, offset + 1, style))
    return part


def _gamma_encode(value):
    """Inverse of BitReader.code() -- the run-length escape payload.

    code() is:
        width = zero_run() + 1          # count leading 0 bits, +1
        if width == 1: bit(); return 1  # a bare 1 bit means the value 1
        suffix_width = bits(width) - 1
        return bits(suffix_width) | (1 << suffix_width)

    The captured CRT4 effContainer state byte 0x78 = 0b01111000 confirms
    the short case: 0b01 present, 0b11 escape, then "1" -> code() returns 1
    -> missing_run = 1 + 2 = 3, which with the present field is exactly
    [1, 2, 2, 2, 2] for a five-field container. The trailing 0b000 is the
    stream byte's own padding.
    """
    if value < 1:
        raise EmitError(f"escape value {value} is below 1")
    if value == 1:
        return "1"
    width = value.bit_length()
    # (width-1) zero bits, the terminating 1, then the low width-1 bits.
    return "0" * (width - 1) + "1" + format(value, f"0{width}b")[1:]



def _encode_states_runlength(states):
    """Invert the two-bit field-state grammar, which is a bit-level run format.

    Decoding is Decode-Style7Replication.field_states plus BitReader: two bits
    per field, where 0b00 is absent (state 2), 0b01 is present (state 1), 0b10
    is state 0, and 0b11 is an escape whose length comes from BitReader.zero_run
    -- a count of leading ZERO BITS terminated by a single 1 bit. So this is a
    bit format, not a byte one, and it is written a bit at a time.

    The captured CRT4 effContainer state byte is 0x78 = 0b01111000, and that
    single byte decodes to exactly [1, 2, 2, 2, 2] for a five-field container:
    0b01 present, then 0b11 escape, then the zero-run terminated by the 1 bit
    in position 6. The round-trip gate is what proves this inversion.
    """
    out = bytearray()
    accumulator = 0
    used = 0

    def push(bit):
        nonlocal accumulator, used
        accumulator = (accumulator << 1) | (1 if bit else 0)
        used += 1
        if used == 8:
            out.append(accumulator)
            accumulator = 0
            used = 0

    def push_bits(value, count):
        for shift in range(count - 1, -1, -1):
            push((value >> shift) & 1)

    index = 0
    total = len(states)
    while index < total:
        if states[index] == 1:
            push_bits(0b01, 2)                 # present
            index += 1
            continue
        if states[index] == 0:
            push_bits(0b10, 2)                 # state 0
            index += 1
            continue
        run = 1                                 # states[index] is 2 (absent)
        while index + run < total and states[index + run] == 2:
            run += 1
        if run <= 1:
            push_bits(0b00, 2)                 # absent, too short to escape
            index += run
            continue
        # Escape: 0b11, then BitReader.code(), an Elias-gamma style integer --
        # a zero_run of (w-1) zeros terminated by a 1 bit, then w bits holding
        # the value with its leading 1 elided. The captured CRT4 effContainer
        # state byte 0x78 = 0b01111000 is exactly this for a run of 4 absent
        # fields: 0b01 present, 0b11 escape, then gamma(4) = 0b00111.
        push_bits(0b11, 2)
        for char in _gamma_encode(run - 3):
            push(char == "1")
        index += run
    if used:
        out.append(accumulator << (8 - used))
    return bytes(out)


def encode_states(states, style=7):
    """Inverse of field_states: build the present/absent bitstream.

    Style 7 is one bit per field, MSB first, state 1 = present. Styles 8 and 10
    use two bits per field, which the reader implements in
    Decode-Style7Replication.field_states. This must produce the identical
    byte layout or the round-trip fails.
    """
    if style in (8, 10):
        # Two bits per field, but the grammar is not a flat table: code 3 is a
        # run-length escape. Decoded by Decode-Style7Replication.field_states:
        #   0 -> state 2      1 -> state 1      2 -> state 0
        #   3 -> read a byte n, then n+2 further fields are all state 2
        # Encoding has to invert that, which means deciding when a run is worth
        # escaping. The captured style-8 records are 5-field containers, so
        # this walks the observed states and emits the shortest legal form.
        return _encode_states_runlength(states)
    out = bytearray((len(states) + 7) // 8)
    for index, state in enumerate(states):
        if state == 1:
            out[index // 8] |= 0x80 >> (index % 8)
    return bytes(out)


def roundtrip_record(data, rec, structure, names):
    """Re-encode one record and compare against the captured bytes.

    Returns (ok, detail). ``ok`` requires two exact matches: the value body and
    the field-state bitstream. A near-miss is reported as a failure.
    """
    if rec["inner_size"] is None:
        return False, "record has no inner size"
    start = rec["body_start"]
    state_start = start + rec["inner_size"]
    style = rec.get("style", 7)

    states = dc.field_states(data, state_start, rec["value_end"] - state_start,
                             len(structure.fields), style)
    captured_states = data[state_start:rec["value_end"]]

    walker = ValueWalker(data, start, state_start, style)
    out = bytearray()
    names_d = names
    for index, state in enumerate(states):
        if state != 1:
            continue
        field = structure.fields[index]
        label = names_d.get(field.definition, hex(field.definition))
        try:
            if field.parts[0].kind in (7, 8):
                emit_part(out, parse_container(walker, field, style))
            else:
                emit_part(out, parse_part(walker, field, 0, style))
        except (WalkError, EmitError) as error:
            return (False, f"at f{index} {label} (kind "
                    f"{field.parts[0].kind}) offset {walker.pos - start}: {error}")

    encoded_states = encode_states(states, style)
    problems = []
    if bytes(out) != data[start:state_start]:
        built_hex = bytes(out).hex().upper()
        want_hex = data[start:state_start].hex().upper()
        first = next((i for i in range(min(len(built_hex), len(want_hex)))
                      if built_hex[i] != want_hex[i]), 0)
        problems.append(f"value body differs at byte {first // 2}: "
                        f"built {built_hex[first:][:24]} want {want_hex[first:][:24]}")
    if encoded_states != captured_states:
        problems.append(f"state stream differs (built "
                        f"{encoded_states.hex().upper()}, captured "
                        f"{captured_states.hex().upper()})")
    if problems:
        return False, "; ".join(problems)
    return True, (f"{len(out)} value + {len(encoded_states)} state bytes exact")


def roundtrip_containers(crt_numbers, structures, names):
    """Round-trip every container record, one verdict each."""
    wanted = {n for n, _ in dc.CONTAINER_STRUCTURES}
    results = []
    for number in crt_numbers:
        data = d7.fixture(number)
        reader, _, count = d7.read_gom_update(data, 4, f"CRT{number}")
        if reader is None:
            continue
        for _ in range(count):
            rec = d7.read_object_record(data, reader)
            if rec["structure_id"] not in wanted or rec["inner_size"] is None:
                continue
            label = next(n for n, name in dc.CONTAINER_STRUCTURES
                         if n == rec["structure_id"])
            try:
                ok, detail = roundtrip_record(data, rec,
                                              structures[rec["structure_id"]], names)
            except Exception as error:               # noqa: BLE001
                results.append((number, label, False, f"error: {error}"))
                continue
            results.append((number, label, ok, detail))
    return results


def roundtrip_player(crt_numbers, structures, names):
    """Round-trip every chrPlayerCharacter (structure 26) record, one verdict each.

    This is the record the world-entry work actually depends on: it carries
    staMobility, chrPlayerLoaded and the stat map. Unlike the containers it has
    215 fields and is style 7, so it exercises the one-bit state stream and the
    full scalar-kind dispatch rather than the two-bit run format.
    """
    structure = structures[dc.PLAYER_STRUCTURE]
    results = []
    for number in crt_numbers:
        data = d7.fixture(number)
        reader, _, count = d7.read_gom_update(data, 4, f"CRT{number}")
        if reader is None:
            continue
        for _ in range(count):
            rec = d7.read_object_record(data, reader)
            if rec["structure_id"] != dc.PLAYER_STRUCTURE:
                continue
            if rec["inner_size"] is None:
                continue
            try:
                ok, detail = roundtrip_record(data, rec, structure, names)
            except Exception as error:               # noqa: BLE001
                results.append((number, ok, f"error: {error}"))
                continue
            results.append((number, ok, detail))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("crt", nargs="*", type=int,
                        help="CRT numbers (default: 2 through 17)")
    parser.add_argument("--containers", action="store_true",
                        help="round-trip every container record")
    parser.add_argument("--player", action="store_true",
                        help="round-trip every chrPlayerCharacter record")
    args = parser.parse_args()
    if not args.containers and not args.player:
        parser.print_help()
        return 0
    names = d7.name_table()
    structures, _, _ = d7.read_schema()
    wanted = args.crt or list(range(2, 18))
    failed = False

    if args.containers:
        results = roundtrip_containers(wanted, structures, names)
        passed = 0
        for number, label, ok, detail in results:
            print(f"CRT{number:<3} {label:<20} {'PASS' if ok else 'FAIL'}  {detail}")
            passed += 1 if ok else 0
        total = len(results)
        print(f"\nroundtrip: {passed}/{total} exact")
        failed = failed or passed != total

    if args.player:
        results = roundtrip_player(wanted, structures, names)
        passed = 0
        for number, ok, detail in results:
            label = "chrPlayerCharacter"
            print(f"CRT{number:<3} {label:<20} {'PASS' if ok else 'FAIL'}  {detail}")
            passed += 1 if ok else 0
        total = len(results)
        print(f"\nplayer: {passed}/{total} exact")
        failed = failed or passed != total

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------
# Player record (structure 26) -- round-trip NOT yet working: 0/14.
#
# This is the record the world-entry work depends on, because it carries
# staMobility (field 9) and chrPlayerLoaded (field 129). It is harder than the
# containers for three reasons that are now established, not guessed:
#
# 1. Style varies by capture. Only CRT2 is style 7 (one-bit states, 27 state
#    bytes for 215 fields). The other 13 are style 8 (two-bit, run-length
#    escaped, 4 state bytes), so the 1-bit path is the exception, not the rule.
#
# 2. Kind 9 is HeroTypes.Class, not a scalar. Tools/Hero/Hero/HeroTypes.cs
#    lists Class = 9, and DeserializeClass.cs reads a single packed value when
#    the stream does not set Flags[4]. Handling that was necessary; without it
#    the value stream desynchronised and produced bogus "invalid packed token"
#    failures far downstream of the real cause.
#
# 3. f100 modMetaStatComputed_Shared is a LookupList whose parts are
#    [8, 2, 8, 5, 4] -- a LookupList nested as the map value. Per
#    DeserializeLookupList's constructor, EVERY level reads its own m_0C and
#    Count (unconditionally, before the per-entry loop), so a nested map is a
#    counted sub-container, not a share of the parent's count. parse_container
#    now does that via a synthetic _Holder.
#
#    Two things that are NOT part of the wire format and were briefly mistaken
#    for it:
#      - ReadVariableId() is a no-op at TransportVersion 5. SerializeStateBase
#        guards it on Flags[1] && TransportVersion < 5, so no extra dword is
#        consumed after a key. It is not a missing read.
#      - Styles 8/10 double the container count with the low bit as a separate
#        flag, so a leading 0x0D is six entries, not thirteen.
#
#    The unresolved part is the record framing above the value stream, not the
#    value grammar: read_object_record's style-8 header appears to place
#    body_start incorrectly (CRT16 shows a 9-byte prefix
#    "09 05 08 C9 02 54 1A C9 02 4C" whose trailing 0x4C is the low byte of the
#    588-byte inner_size 0x24C). If body_start is off, every field after it is
#    misaligned, which matches the failures appearing at wildly varying offsets
#    across captures. That is the next thing to check, in
#    Decode-Style7Replication.py.
#
# 4. Enum width is the ONE remaining unverified suspect.
#
#    Three hypotheses were raised and tested; two were wrong, and the eliminations
#    matter as much as the survivor:
#
#      - Float (kind 4) is 4 RAW little-endian bytes, not packed. PackedStream.cs
#        line 198 does Read(float) = BitConverter.ToSingle(GetBytes(ReadUInt())),
#        and Frame.ReadUInt is a straight 4-byte read with pos += 4. Our
#        raw(4) was already correct.
#      - Vec3 (kind 18) is 12 raw bytes, not 3x packed. Measured directly on
#        f1 character_position in CRT2: read as raw float32 it yields
#        (-64.874, -6.906, -127.671) and puts f2 at a plausible vec(0,-90,0);
#        read as three packed integers it yields (138,191,129) and puts f2 at
#        vec(-5.8e17, -2.9e38, 2.7e-43). The raw reading is the real one.
#        Our raw(12) was already correct.
#      - Enum (kind 5) is UNVERIFIED. HeroEnum.Deserialize calls
#        stream.Read(out Value), which is packed at TransportVersion 5, while we
#        read a single byte. f9's token is 0x02 -- a valid literal either way --
#        so it decodes correctly by coincidence. A value >= 0xC0 would be
#        misread as a multi-byte token.
#
#    IMPORTANT: the Tools/Hero library is authoritative for asset and Omega-DOM
#    encodings, NOT for CRT replication records. PackedStream_2 pins
#    TransportVersion = 5, so the library predicts packed Vec3, and that
#    prediction is demonstrably wrong for these captures. Do not use the library
#    to settle CRT value grammar -- measure against the bytes. It remains correct
#    for the packed-integer token rules and the doubled container count, which
#    were confirmed independently.
#
#    Observed failure: the walk is correct through f15 and dies at f16
#    ablUserClearCasting on token 0xC0 at offset 39. If the enum hypothesis holds,
#    the desync actually begins at f9 and the intervening bytes merely happen to
#    parse as scalars. Next experiment: re-walk from f9 with enums read as packed
#    and check whether all 2773 bytes reconcile. The container gate cannot
#    detect this -- the 10 container structures use only kinds 1, 2, 8 and 15,
#    so it returns 16/16 whatever happens to kinds 4, 5 and 18.
#
# The failure offsets moved substantially once (1) and (2) were fixed, which
# confirms they were real, but (3) is unresolved. Do not treat the player gate
# as a regression check yet -- it will report FAIL for every capture.
# ---------------------------------------------------------------------------
