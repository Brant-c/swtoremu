#!/usr/bin/env python3
"""Decode captured style-7 replication schemas and inspect value bodies.

This diagnostic is deliberately read-only.  CRT1 supplies the replication
stream's compact structure table; later CRTs refer to those structures by the
small integer at the start of each style-7 class value.

Two optional read-only modes expose the evidence behind the world-entry
findings without changing the default output:

    --dump-fields    every field the captured stream actually transmits for the
                     replicated player, with its resolved name and state byte.
                     A state of 2 means the transaction does not carry the field
                     at all, so the client keeps the value its own constructor
                     supplied.  Seeing the complete transmitted set is what
                     distinguishes "stale captured value" from "no captured
                     value", which is the difference between the Safe Login /
                     staMobility class of defect and the missing ability and
                     phase state.
    --dump-objects   the node each transaction creates, with the class named in
                     the record.

Both modes use the GomUpdateObject framing declared by
``Packets/MessageHeaders/base_gom_update.h``: a packed node id, a switched
``uint8_t`` that selects class, template, parent, metadata and value, metadata
selections that each carry their own ``uint32_t`` element count, and a value
whose byte count bounds the field data.  Every captured fixture is walked
exactly to its own end under that rule.
"""

from dataclasses import dataclass
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
CRT_DIR = ROOT / "SharpServer/bin/Debug/AreaServer/CRT"
NAMES = ROOT / "Tools/tor_tools/gom_type_names.xml"


class Reader:
    def __init__(self, data, offset=0, end=None):
        self.data = data
        self.pos = offset
        self.end = len(data) if end is None else end

    def byte(self):
        if self.pos >= self.end:
            raise EOFError(f"read past end at {self.pos}")
        value = self.data[self.pos]
        self.pos += 1
        return value

    def packed(self):
        start = self.pos
        token = self.byte()
        if token < 0xC0:
            return token
        if not 0xC8 <= token <= 0xCF:
            raise ValueError(f"invalid packed token 0x{token:02X} at {start}")
        count = token - 0xC7
        if self.pos + count > self.end:
            raise EOFError(f"truncated packed integer at {start}")
        value = int.from_bytes(self.data[self.pos:self.pos + count], "big")
        self.pos += count
        return value


class BitReader:
    """Port of the client's MSB-first reader at RVAs 0x1B0E00/0x1B0EB0."""
    def __init__(self, data, offset, size):
        self.data = data
        self.pos = offset
        self.bits_left = size * 8
        self.in_byte = 8

    def bit(self):
        if self.bits_left <= 0:
            raise EOFError("past end of bit stream")
        self.in_byte -= 1
        value = (self.data[self.pos] >> self.in_byte) & 1
        if self.in_byte == 0:
            self.pos += 1
            self.in_byte = 8
        self.bits_left -= 1
        return value

    def bits(self, count):
        value = 0
        for _ in range(count):
            value = (value << 1) | self.bit()
        return value

    def zero_run(self):
        count = 0
        while ((self.data[self.pos] >> (self.in_byte - 1)) & 1) == 0:
            self.bit()
            count += 1
        return count

    def code(self):
        width = self.zero_run() + 1
        if width == 1:
            self.bit()
            return 1
        suffix_width = self.bits(width) - 1
        return self.bits(suffix_width) | (1 << suffix_width)


def field_states(data, offset, size, count):
    bits = BitReader(data, offset, size)
    states = []
    missing_run = 0
    for field_index in range(count):
        if missing_run:
            states.append(2)
            missing_run -= 1
            continue
        code = bits.bits(2)
        if code == 0:
            states.append(2)
        elif code == 1:
            # The native decoder distinguishes state 1/3 using type metadata.
            # All scalar fields in the player schema use the normal state 1.
            states.append(1)
        elif code == 2:
            states.append(0)
        elif code == 3:
            missing_run = bits.code() + 2
            states.append(2)
        else:
            raise ValueError(f"unexpected field-state code {code} at field {field_index}, "
                             f"byte {bits.pos} bit {8-bits.in_byte}")
    return states, bits

@dataclass
class TypePart:
    kind: int
    definition: int
    structure: int


@dataclass
class Field:
    definition: int
    parts: list


@dataclass
class Structure:
    number: int
    base_class: int
    additional_classes: list
    fields: list


def fixture(number):
    return (CRT_DIR / f"tython_blockout-4611686019869492753-1.{number}.acrt").read_bytes()


def read_schema():
    data = fixture(1)
    reader = Reader(data, 8)
    structures = {}
    for _ in range(reader.packed()):
        number = reader.packed()
        base_class = reader.packed()
        additional = [reader.packed() for _ in range(reader.packed())]
        fields = []
        for _ in range(reader.packed()):
            definition = reader.packed()
            parts = []
            for _ in range(reader.packed()):
                parts.append(TypePart(reader.packed(), reader.packed(), reader.packed()))
            fields.append(Field(definition, parts))
        structures[number] = Structure(number, base_class, additional, fields)
    return structures, reader.pos, len(data)


def name_table():
    return {int(node.attrib["id"]): node.attrib.get("name", "")
            for node in ET.parse(NAMES).getroot()}


def describe_part(part, names):
    kinds = {
        1: "UInt64", 2: "Int64", 3: "Boolean", 4: "Float", 5: "Enum",
        6: "String", 7: "List", 8: "Map", 9: "EmbeddedClass",
        11: "Array", 12: "Table", 13: "Cubic", 14: "Script",
        15: "ClassRef", 17: "Timer", 18: "Vec3", 20: "TimeSpan",
        21: "Time",
    }
    text = kinds.get(part.kind, f"type{part.kind}")
    if part.definition:
        text += f"<{names.get(part.definition, f'0x{part.definition:016X}')} >"
    if part.structure:
        text += f"[structure {part.structure}]"
    return text


def main():
    names = name_table()
    structures, consumed, total = read_schema()
    print(f"CRT1 schemas={len(structures)} consumed={consumed}/{total}")
    for number in (1, 9, 22, 26):
        structure = structures.get(number)
        if structure is None:
            continue
        print(f"\nstructure {number}: base={names.get(structure.base_class, hex(structure.base_class))} "
              f"additional={len(structure.additional_classes)} fields={len(structure.fields)}")
        for index, field in enumerate(structure.fields):
            types = " -> ".join(describe_part(p, names) for p in field.parts)
            print(f"  {index:3}: {names.get(field.definition, '<unnamed>')} "
                  f"0x{field.definition:016X} {types}")

    for crt_number in range(2, 18):
      data = fixture(crt_number)
      reader = Reader(data, 8)
      transaction_flags = reader.byte()
      object_count = reader.packed() if transaction_flags & 1 else 0
      for object_index in range(object_count):
        object_start = reader.pos
        node = reader.packed()
        flags = reader.byte()
        class_id = reader.packed() if flags & 0x80 else 0
        template_id = reader.packed() if flags & 0x40 else 0
        parent_id = reader.packed() if flags & 0x20 else 0
        if flags & 0x10:
            metadata_flags = reader.byte()
            if metadata_flags & 3:
                count = int.from_bytes(data[reader.pos:reader.pos + 4], "little")
                reader.pos += 4
                for _ in range(count):
                    reader.packed()
        value = None
        if flags & 0x08:
            transport = reader.byte()
            style = reader.byte()
            outer_size = reader.packed()
            outer_start = reader.pos
            value_end = outer_start + outer_size
            structure_id = reader.packed() if style in (7, 8) else None
            inner_size = reader.packed() if style in (7, 8) else None
            body_start = reader.pos
            value = (transport, style, outer_size, structure_id, inner_size,
                     body_start, value_end)
            reader.pos = value_end
        if node == 0x4000010E218A839C:
            print(f"\nCRT{crt_number} player object={object_index} offset={object_start} "
                  f"flags=0x{flags:02X} class={names.get(class_id, hex(class_id))}")
            if value and structure_id == 26:
                    # The native constructor bounds the value payload with
                    # inner_size, then initializes its bit reader at that end.
                    # The compact field-state stream is therefore the outer
                    # value's tail, not a prefix of the values.
                    state_start = body_start + inner_size
                    states, bits = field_states(data, state_start,
                                                value_end - state_start,
                                                len(structures[26].fields))
                    print(f"    state bits end at byte={bits.pos} bit={8-bits.in_byte}; "
                          f"present={sum(s != 2 for s in states)}")
                    # High-value player-entry gates.  staMobility is the
                    # replicated source used by staCharacter_CalculateCanMove;
                    # the remaining fields control local-player identity and
                    # loading/phase behavior.
                    for wanted in (9, 35, 89, 104, 129):
                        field = structures[26].fields[wanted]
                        print(f"    state[{wanted}] {names.get(field.definition)}={states[wanted]}")
                    print("    values prefix=" + data[body_start:body_start + 64].hex(" "))
                    print("    state bytes=" + data[state_start:value_end].hex(" "))
            break

    data = fixture(3)
    reader = Reader(data, 8)
    transaction_flags = reader.byte()
    object_count = reader.packed() if transaction_flags & 1 else 0
    phase_node = reader.packed()
    phase_flags = reader.byte()
    phase_class = reader.packed() if phase_flags & 0x80 else 0
    phase_template = reader.packed() if phase_flags & 0x40 else 0
    phase_parent = reader.packed() if phase_flags & 0x20 else 0
    print(f"\nCRT3 owner: objects={object_count} node=0x{phase_node:016X} "
          f"flags=0x{phase_flags:02X} class={names.get(phase_class, hex(phase_class))} "
          f"template=0x{phase_template:016X} parent=0x{phase_parent:016X}")
    transport, style, outer_size = reader.byte(), reader.byte(), reader.packed()
    outer_start = reader.pos
    structure_id, inner_size = reader.packed(), reader.packed()
    body_start = reader.pos
    value_end = outer_start + outer_size
    state_start = body_start + inner_size
    print(f"\nCRT3 phase value: transport={transport} style={style} "
          f"structure={structure_id} valueBytes={inner_size}")
    schema_class = names.get(structures[structure_id].base_class, "<unnamed>")
    print(f"    CRT1 structure {structure_id} names {schema_class}, not "
          "phsPlayerPhaseData; phase field names are therefore not assigned")
    print("    values=" + data[body_start:state_start].hex(" "))
    print("    state bytes=" + data[state_start:value_end].hex(" "))

    # Schema-dependent interpretation only: this body is structurally exact
    # for the sorted five-field phsPlayerPhaseData schema reconstructed from
    # client.gom, but CRT1 does not contain that schema under structure 1.
    candidate = Reader(data, body_start, state_start)
    outer_count = candidate.packed()
    phase_type = candidate.packed()
    inner_count = candidate.packed()
    phase_id = candidate.packed()
    active_info_value_size = candidate.packed()
    authority_id = candidate.packed()
    if (outer_count, inner_count, active_info_value_size, candidate.pos) == (
            1, 1, 0, state_start):
        print("    schema-dependent phase candidate (not wire-authoritative):")
        print(f"      phsActivePhases[{phase_type}][{phase_id:#018x}] = "
              "phsActivePhaseInfo(empty)")
        print(f"      phsAuthorityID={authority_id:#018x}")
        print("      remaining three fields have no value bytes; exact state "
              "meaning awaits the matching schema/session")


PLAYER_NODE = 0x4000010E218A839C
PLAYER_STRUCTURE = 26

# The captured CRT fixtures begin with the packet's little-endian stream id,
# then the GOM update itself.  The awareness fixtures are payload-only and
# begin directly at the update.
CRT_UPDATE_OFFSET = 4
AWARENESS_UPDATE_OFFSET = 0


def read_gom_update(data, update_offset, label):
    """Read a GOM update header and return its reader, flags, and object count.

    The layout is the one declared by ``Packets/MessageHeaders/
    base_gom_update.h``: ``uint32_t`` contract count, then a ``uint8_t``
    switched value where ``0x01`` selects the object list and ``0x02`` the
    trailing removal list.
    """
    reader = Reader(data, update_offset)
    contract_count = int.from_bytes(data[reader.pos:reader.pos + 4], "little")
    reader.pos += 4
    if contract_count != 0:
        # No captured fixture carries contract updates, so their framing is
        # deliberately not guessed at here.
        print(f"{label}: contractCount={contract_count} (contracts are not "
              "decoded by this tool)")
        return None, 0, 0
    flags = reader.byte()
    object_count = reader.packed() if flags & 0x01 else 0
    print(f"{label}: flags=0x{flags:02X} objects={object_count} bytes={len(data)}")
    return reader, flags, object_count


def read_object_record(data, reader):
    """Parse one GomUpdateObject using the documented framing.

    ``base_gom_update.h`` declares the record as ``Packed<NodeID>`` followed by
    a switched ``uint8_t``: ``0x80`` ClassID, ``0x40`` TemplateID, ``0x20``
    ParentNodeID, ``0x10`` a metadata byte whose ``0x01`` and ``0x02`` bits each
    select an independent ``BasicVector<uint32_t, uint64_t>`` (so both lists may
    be present, each with its own ``uint32_t`` element count), and ``0x08`` the
    value: ``Packed<FieldVersion>``, ``Packed<FieldFormat>``, then
    ``BasicVector<Packed<uint64_t>, uint8_t>``.  Every captured fixture walks
    exactly to its own end under this rule.
    """
    record = {"start": reader.pos, "node": reader.packed()}
    flags = reader.byte()
    record["flags"] = flags
    record["class_id"] = reader.packed() if flags & 0x80 else 0
    record["template_id"] = reader.packed() if flags & 0x40 else 0
    record["parent_id"] = reader.packed() if flags & 0x20 else 0
    metadata_counts = []
    if flags & 0x10:
        metadata_flags = reader.byte()
        for bit in (0x01, 0x02):
            if metadata_flags & bit:
                count = int.from_bytes(data[reader.pos:reader.pos + 4], "little")
                reader.pos += 4
                metadata_counts.append(count)
                reader.pos += 8 * count
    record["metadata_counts"] = metadata_counts
    record["field_version"] = None
    record["style"] = None
    record["structure_id"] = None
    record["inner_size"] = None
    record["body_start"] = None
    record["value_end"] = None
    if flags & 0x08:
        record["field_version"] = reader.packed()
        record["style"] = reader.packed()
        field_size = reader.packed()
        # value_end bounds the whole outer value, so it is measured from the
        # outer start, before the style-7/8 structure header is consumed.
        record["outer_start"] = reader.pos
        record["value_end"] = reader.pos + field_size
        if record["style"] in (7, 8):
            record["structure_id"] = reader.packed()
            record["inner_size"] = reader.packed()
        # body_start is the first *value* byte, i.e. after the style-7/8
        # structure header.  main() already advanced past it that way; taking
        # it before the header made every dump_field_states()/Locate-CrtValue
        # state_start four bytes early and mis-reported the transmitted fields.
        record["body_start"] = reader.pos
        reader.pos = record["value_end"]
    return record


def dump_field_states(crt_numbers, names, structures):
    """Print every field the captured stream transmits for the replicated player.

    The walk uses the documented GomUpdateObject framing and stops as soon as
    the player record is decoded.
    """
    structure = structures[PLAYER_STRUCTURE]
    for crt_number in crt_numbers:
        data = fixture(crt_number)
        reader, _, object_count = read_gom_update(
            data, CRT_UPDATE_OFFSET, f"CRT{crt_number}")
        if reader is None:
            continue
        found = False
        for _ in range(object_count):
            record = read_object_record(data, reader)
            if record["node"] != PLAYER_NODE:
                continue
            found = True
            print(f"\nCRT{crt_number} player {record['node']:#018x} "
                  f"flags=0x{record['flags']:02X} "
                  f"class={names.get(record['class_id'], '<unknown>')} "
                  f"structure={record['structure_id']}")
            if record["structure_id"] == PLAYER_STRUCTURE:
                # Same boundary rule as main: the compact field-state stream is
                # the outer value's tail, not a prefix of the values.
                state_start = record["body_start"] + record["inner_size"]
                states, bits = field_states(data, state_start,
                                            record["value_end"] - state_start,
                                            len(structure.fields))
                present = [index for index in range(len(states)) if states[index] != 2]
                print(f"    transmitted={len(present)}/{len(states)}; "
                      f"state bits end at byte={bits.pos} bit={8 - bits.in_byte}")
                for index in present:
                    field = structure.fields[index]
                    types = " -> ".join(describe_part(part, names)
                                        for part in field.parts)
                    print(f"      {index:3} state={states[index]} "
                          f"{names.get(field.definition, '<unnamed>')} [{types}]")
            else:
                print("    not the player structure; field states not decoded")
            break
        if not found:
            print(f"\nCRT{crt_number}: no record for the replicated player node")


def dump_objects(crt_numbers, names):
    """Print every record of each transaction with its resolved class name.

    The walk uses the documented GomUpdateObject framing, so each fixture is
    consumed to its exact end and the optional trailing removal list is
    reported as well.
    """
    for crt_number in crt_numbers:
        data = fixture(crt_number)
        reader, update_flags, object_count = read_gom_update(
            data, CRT_UPDATE_OFFSET, f"CRT{crt_number}")
        if reader is None:
            continue
        inventory = {}
        for object_index in range(object_count):
            record = read_object_record(data, reader)
            class_name = names.get(record["class_id"], "")
            if class_name:
                inventory[class_name] = inventory.get(class_name, 0) + 1
            extras = []
            if record["template_id"]:
                extras.append("template=0x%016X" % record["template_id"])
            if record["parent_id"]:
                extras.append("parent=0x%016X" % record["parent_id"])
            if record["metadata_counts"]:
                extras.append("metadata=" + "/".join(
                    str(count) for count in record["metadata_counts"]))
            extras.append("style=%s" % record["style"])
            if record["structure_id"] is not None:
                extras.append("structure=%s" % record["structure_id"])
            tail = " ".join(extras)
            print(f"    {object_index:3} @0x{record['start']:04X} "
                  f"{record['node']:#018x} flags=0x{record['flags']:02X} "
                  f"{class_name} {tail}".rstrip())
        if update_flags & 0x02:
            removal_count = reader.packed()
            removals = [reader.packed() for _ in range(removal_count)]
            print("    removals=%d: " % removal_count
                  + ", ".join(f"{node:#018x}" for node in removals))
        if inventory:
            print("    classes: " + ", ".join(
                f"{name}x{count}" for name, count in sorted(inventory.items())))
        print(f"    end=0x{reader.pos:04X} of 0x{len(data):04X}")


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump-fields", nargs="*", type=int, metavar="CRT",
                        help="print every transmitted player field for these CRTs "
                             "(default: 2 through 17)")
    parser.add_argument("--dump-objects", nargs="*", type=int, metavar="CRT",
                        help="print every created node and class for these CRTs "
                             "(default: 2 through 17)")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_arguments()
    if arguments.dump_fields is None and arguments.dump_objects is None:
        main()
    else:
        # Both dump modes are read-only views over the same fixtures.  CRT1 is
        # parsed first because it is the only file carrying the structure table.
        dump_names = name_table()
        dump_structures, _, _ = read_schema()
        if arguments.dump_fields is not None:
            dump_field_states(arguments.dump_fields or list(range(2, 18)),
                              dump_names, dump_structures)
        if arguments.dump_objects is not None:
            dump_objects(arguments.dump_objects or list(range(2, 18)), dump_names)
