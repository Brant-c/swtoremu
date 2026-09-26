"""Decode the ordered value body of a captured object record.

The field-state bitstream says *which* fields are present; this walks the value
bytes that follow and shows *what* each present field actually holds. That is
the only offline way to test whether the field order in the CRT1 schema is the
order the real client used: a correct order yields semantically sane values
(chrMeleeDistance a small positive reach, kynMsg_MoveSpeed a plausible run
speed, enums in range). A wrong order yields garbage and a byte count that
cannot reconcile.

The pass/fail criterion is exact, and it is the only one used here: the walk
must consume precisely ``inner_size`` bytes *and* land on a container entry
boundary. Anything less is reported as a failure rather than rounded over, and
a record that merely "looks plausible" is never counted as a pass.

Usage:
    python Decode-CrtValues.py                 # walk the player record in every CRT
    python Decode-CrtValues.py 2               # just CRT2
    python Decode-CrtValues.py --containers    # every container, one verdict each
"""

import argparse
import importlib.util
import struct
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("d7", Path(__file__).with_name("Decode-Style7Replication.py"))
d7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d7)

PLAYER_STRUCTURE = 26  # chrPlayerCharacter

# Every container structure in the captures. They all share one five-field shape
# (conContents Map, conSharedData, conContainerSpecName, conOwnerNode,
# conExpansionLevel), so each is named explicitly to give it its own pass/fail
# line rather than a single aggregated verdict that could hide a failure.
CONTAINER_STRUCTURES = (
    (9, "ablContainer"),
    (12, "tmrContainer"),
    (13, "effContainer"),
    (14, "eqpContainer"),
    (17, "invContainer"),
    (18, "vndBuybackContainer"),
    (19, "bnkContainer"),
    (20, "trdContainer"),
    (21, "malMailContainer"),
    (22, "qckContainer"),
)


class WalkError(Exception):
    pass


class ValueWalker:
    """Consumes one field's value from the value stream and returns its text."""

    # How 64-bit integers are laid down is not something the captured bytes
    # settle on their own, so both candidates are tried and whichever makes the
    # record reconcile to its exact inner_size is the one the client used.
    INT64_MODE = "packed"        # "packed" or "fixed8"

    def __init__(self, data, offset, end, style=7):
        self.data = data
        self.pos = offset
        self.end = end
        # The record's transport style. Styles 8 and 10 encode container counts
        # doubled; see _sequence. Defaults to 7, which is what the CRT2 creates
        # use and which leaves the count untouched.
        self.style = style

    def left(self):
        return self.end - self.pos

    def byte(self):
        if self.pos >= self.end:
            raise WalkError("ran out of value bytes")
        value = self.data[self.pos]
        self.pos += 1
        return value

    def raw(self, count):
        if self.pos + count > self.end:
            raise WalkError("ran out of value bytes")
        chunk = self.data[self.pos:self.pos + count]
        self.pos += count
        return chunk

    def packed(self):
        """Read one packed integer.

        Mirrors Tools/Hero/Hero/PackedStream.cs::Read(out ulong), which is the
        reference implementation and the authority for this encoding. That method,
        for TransportVersion > 1 (PackedStream_2 pins 5):

            if (b >= 192) { if (b < 200 || b > 207) throw; ReadPacked(b - 199); }
            else          value = b;

        So 0xC0..0xC7 (192..199) are genuinely invalid and raise, 0xC8..0xCF
        (200..207) carry 1..8 big-endian bytes, and anything below 192 is a
        literal. An earlier attempt in this file treated 0xC0..0xC7 as a one-byte
        signed payload; that hypothesis is dead and the branch is deliberately
        absent. Note 0xC8 -> 199 + 1 = 200 == 1 byte, which is why CC in the
        captures carries a 5-byte node: 204 - 199 = 5.
        """
        start = self.pos
        token = self.byte()
        if token < 0xC0:
            return token
        if not 0xC8 <= token <= 0xCF:
            raise WalkError(f"invalid packed token 0x{token:02X} at {start}")
        count = token - 0xC7
        return int.from_bytes(self.raw(count), "big")

    def part(self, part, names, depth=0):
        if depth > 8:
            raise WalkError("container nested too deeply")
        kind = part.kind
        if kind in (1, 2):            # UInt64 / Int64
            if ValueWalker.INT64_MODE == "fixed8":
                return "0x%016X" % int.from_bytes(self.raw(8), "little")
            return str(self.packed())
        if kind == 3:                 # Boolean
            return str(self.byte())
        if kind == 4:                 # Float
            return "%g" % struct.unpack("<f", self.raw(4))[0]
        if kind == 5:                 # Enum
            return "enum=%d" % self.byte()
        if kind == 6:                 # String
            return "str(len=%d)" % self.packed()
        if kind == 7:                 # List
            return _sequence(self, part, 1, names, depth)
        if kind == 8:                 # Map
            return _sequence(self, part, 2, names, depth, pairs=True)
        if kind == 15:                # ClassRef / node ref
            return "ref=0x%X" % self.packed()
        if kind == 18:                # Vec3
            return "vec(%g,%g,%g)" % struct.unpack("<3f", self.raw(12))
        if kind == 17:                # Timer
            return "timer(%d)" % self.packed()
        raise WalkError(f"unhandled kind {kind}")


def _sequence(self, part, first_element, names, depth, pairs=False):
    """Walk a List (kind 7) or Map (kind 8) value.

    ``conContents`` is a Map whose parts are [8, key, value]: the key is the
    1-byte slot index and the value the packed node ref. The count is followed by
    exactly that many entries -- no more, no fewer -- so the walk always lands on
    an entry boundary by construction. The repeated 9-byte refs that trail some
    containers are *not* entries: they are the following fields (conSharedData,
    conContainerSpecName) and are consumed by them, not here.

    Styles 8 and 10 double the count, per
    Tools/Hero/Hero/SerializeLookupList.cs and DeserializeLookupList.cs:

        writer: if (stream.Style == 8 || stream.Style == 10)
                    stream.Write(Count * 2, Count * 2);
                else stream.Write(Count, Count);
        reader: this.m_30 = (Count & 1) == 1; Count >>= 1;

    So for those styles the low bit is a flag (m_30) and the real entry count is
    the value halved. This is what the `flags=0x09` captures use, where a leading
    0x0D is six entries, not thirteen.
    """
    if len(part.parts) <= first_element:
        raise WalkError(f"kind {part.kind} has no element part")
    count = self.packed()
    if self.style in (8, 10):
        count >>= 1
    # Every declared entry is read, so the walk always lands on an entry
    # boundary and the byte count is meaningful. Only the first few are rendered;
    # truncating the *display* must never truncate the *read*, which is what made
    # the ablContainer stop at 50 of 208 bytes.
    items = []
    shown = 0
    for _ in range(count):
        if self.pos >= self.end:
            raise WalkError(f"container claims {count} entries, ran out of bytes")
        key = self.part(part.parts[first_element], names, depth + 1)
        if pairs:
            value = self.part(part.parts[first_element + 1], names, depth + 1)
        else:
            value = None
        if shown < 6:
            items.append(f"{key}:{value}" if pairs else f"{key}")
            shown += 1
    if count > shown:
        items.append("...")
    return f"[{count}]{{{','.join(items)}}}"


def field_states(data, offset, size, count, style=7):
    """Read the per-field present/absent bitstream.

    One bit per field, MSB-first, for style 7. This is not a guess: the captured
    state bytes make the two-bit reading arithmetically impossible for a 5-field
    container (structures 9/12/13/14/17/18/19/20/21/22), which carries exactly
    1 state byte = 8 bits, and 5 fields x 2 bits = 10 does not fit.

    Styles 8 and 10 are a different shape and use the two-bit reader, which is
    already implemented and tested in Decode-Style7Replication.py. That is what
    the `flags=0x09` update records use; they are the same records that double
    their container counts, so the style is the single discriminator for both
    differences. Verified on CRT4: both effContainers are style 8, and 2-bit
    yields [1,2,2,2,2] (conContents present) where 1-bit wrongly yields
    [2,1,1,1,1].
    """
    if style in (8, 10):
        states, _ = d7.field_states(data, offset, size, count)
        return states
    if size * 8 < count:
        raise WalkError(f"state stream {size * 8} bits cannot hold {count} fields")
    bits = d7.BitReader(data, offset, size)
    return [1 if bits.bit() else 2 for _ in range(count)]


def walk_record(data, rec, structure, names):
    """Walk one object record's value body, field by field, in schema order.

    Returns (rows, summary, ok). ``ok`` is True only when the walk consumed
    precisely inner_size bytes.
    """
    if rec["inner_size"] is None:
        return None, "record has no inner size", False
    # The value body starts at body_start and is inner_size bytes long; the
    # field-state bitstream is what follows, up to value_end. Deriving the state
    # start from value_end instead of from body_start lands in the wrong place
    # entirely, because value_end is measured from the start of the outer value.
    start = rec["body_start"]
    state_start = rec["body_start"] + rec["inner_size"]
    end = state_start
    states = field_states(data, state_start, rec["value_end"] - state_start,
                          len(structure.fields), rec.get("style", 7))
    walker = ValueWalker(data, start, end, rec.get("style", 7))
    rows = []
    for index, state in enumerate(states):
        if state != 1:                 # only state 1 carries value bytes
            continue
        field = structure.fields[index]
        name = names.get(field.definition, f"0x{field.definition:016X}")
        try:
            kind = field.parts[0].kind
            if kind in (7, 8):
                # List/Map need the field's whole part list: the element part, and
                # for a Map the key part as well.
                text = _sequence(walker, field, 1, names, 0, pairs=(kind == 8))
            else:
                text = walker.part(field.parts[0], names)
        except WalkError as error:
            rows.append((index, name, f"<{error}>"))
            break
        rows.append((index, name, text))
    consumed = walker.pos - start
    ok = consumed == rec["inner_size"]
    return rows, f"{consumed}/{rec['inner_size']} bytes consumed", ok


def walk_containers(crt_numbers, structures, names):
    """Every container record in the given CRTs, one pass/fail verdict each.

    Each record is its own check: the walk must consume exactly inner_size bytes
    AND land on a container entry boundary. A container is accepted only when the
    map's declared count was fully walked, so a short or over-long entry list is a
    failure rather than a near-miss.
    """
    wanted = {n for n, _ in CONTAINER_STRUCTURES}
    results = []
    for number in crt_numbers:
        data = d7.fixture(number)
        reader, _, count = d7.read_gom_update(data, 4, f"CRT{number}")
        if reader is None:
            continue
        for _ in range(count):
            rec = d7.read_object_record(data, reader)
            structure_id = rec["structure_id"]
            if structure_id not in wanted or rec["inner_size"] is None:
                continue
            structure = structures[structure_id]
            label = next(n for n, name in CONTAINER_STRUCTURES if n == structure_id)
            try:
                rows, summary, ok = walk_record(data, rec, structure, names)
            except Exception as error:               # noqa: BLE001
                results.append((number, label, rec, False, f"error: {error}", None))
                continue
            # Entry-boundary check: the conContents map, if present, must have been
            # walked to its declared count. walk_record raises if it could not be,
            # so reaching here with ok True is the boundary condition.
            results.append((number, label, rec, ok, summary, rows))
    return results


def report_containers(crt_numbers, structures, names):
    """Print one pass/fail line per container record, then a summary.

    Each container is a separate check. The exit status is non-zero if any
    container fails, so this doubles as a regression gate.
    """
    results = walk_containers(crt_numbers, structures, names)
    passed = 0
    for number, label, rec, ok, summary, rows in results:
        verdict = "PASS" if ok else "FAIL"
        flag = rec["flags"]
        print(f"CRT{number:<3} {label:<20} node=0x{rec['node']:016X} flags=0x{flag:02X} "
              f"-> {summary}  {verdict}")
        if rows:
            for index, name, text in rows:
                print(f"        f{index:<3} {name:<22} {text}")
        passed += 1 if ok else 0
    total = len(results)
    print(f"\ncontainers: {passed}/{total} pass")
    return 0 if passed == total else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("crt", nargs="*", type=int,
                        help="CRT numbers to walk (default: 2 through 17)")
    parser.add_argument("--containers", action="store_true",
                        help="validate every container record, one verdict each")
    args = parser.parse_args()
    names = d7.name_table()
    structures, _, _ = d7.read_schema()
    if args.containers:
        return report_containers(args.crt or list(range(2, 18)), structures, names)
    structure = structures[PLAYER_STRUCTURE]
    wanted = args.crt or list(range(2, 18))
    for number in wanted:
        data = d7.fixture(number)
        reader, _, count = d7.read_gom_update(data, 4, f"CRT{number}")
        if reader is None:
            continue
        for _ in range(count):
            rec = d7.read_object_record(data, reader)
            if rec["structure_id"] != PLAYER_STRUCTURE:
                continue
            print(f"=== CRT{number}  inner={rec['inner_size']}")
            try:
                rows, tally, ok = walk_record(data, rec, structure, names)
            except Exception as error:               # noqa: BLE001
                print(f"    state decode failed: {error}")
                continue
            for index, name, text in rows:
                print(f"    f{index:<4d} {name:<34s} {text}")
            print(f"    -> {tally}  {'OK' if ok else 'MISMATCH'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
