#!/usr/bin/env python3
"""Round-trip and inspect SWTOR compact style-7 schema tables.

This tool deliberately does not write .acrt fixtures.  Its first safety gate
is byte-exact reproduction of the schema-table prefix already present in CRT1.
Generation of new structures must remain offline until value/state encoding is
independently verified.
"""
import argparse
import importlib.util
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
decoder_spec = importlib.util.spec_from_file_location(
    "style7_decoder", HERE / "Decode-Style7Replication.py")
decoder = importlib.util.module_from_spec(decoder_spec)
decoder_spec.loader.exec_module(decoder)

gom_spec = importlib.util.spec_from_file_location(
    "gom_inspector", HERE / "Inspect-GomClass.py")
gom = importlib.util.module_from_spec(gom_spec)
gom_spec.loader.exec_module(gom)


class Writer:
    def __init__(self):
        self.data = bytearray()

    def packed(self, value):
        if not 0 <= value <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError(f"packed value is outside uint64: {value}")
        if value < 0xC0:
            self.data.append(value)
            return
        width = max(1, (value.bit_length() + 7) // 8)
        self.data.append(0xC7 + width)
        self.data.extend(value.to_bytes(width, "big"))


def encode_schema(structures):
    writer = Writer()
    writer.packed(len(structures))
    for number, structure in structures.items():
        if number != structure.number:
            raise ValueError(f"schema key {number} disagrees with record {structure.number}")
        writer.packed(structure.number)
        writer.packed(structure.base_class)
        writer.packed(len(structure.additional_classes))
        for class_id in structure.additional_classes:
            writer.packed(class_id)
        writer.packed(len(structure.fields))
        for field in structure.fields:
            writer.packed(field.definition)
            writer.packed(len(field.parts))
            for part in field.parts:
                writer.packed(part.kind)
                writer.packed(part.definition)
                writer.packed(part.structure)
    return bytes(writer.data)


def first_difference(expected, actual):
    common = min(len(expected), len(actual))
    for index in range(common):
        if expected[index] != actual[index]:
            return index
    return common if len(expected) != len(actual) else None


def parse_manifest_type(blob, position, structures_by_class):
    kind = blob[position]
    position += 1
    definition = 0
    structure = 0
    if kind in (0x05, 0x09, 0x0F):
        gom_definition = struct.unpack_from("<Q", blob, position)[0]
        position += 8
        # Captured compact schemas retain Enum and EmbeddedClass definitions,
        # but normalize ClassRef<T>'s target definition to zero.
        definition = 0 if kind == 0x0F else gom_definition
        if kind == 0x09:
            matches = structures_by_class.get(definition, [])
            structure = matches[0] if len(matches) == 1 else 0
    parts = [decoder.TypePart(kind, definition, structure)]
    if kind == 0x07:
        inner, position = parse_manifest_type(blob, position, structures_by_class)
        parts.extend(inner)
    elif kind == 0x08:
        key, position = parse_manifest_type(blob, position, structures_by_class)
        value, position = parse_manifest_type(blob, position, structures_by_class)
        parts.extend(key)
        parts.extend(value)
    return parts, position


def print_class_manifest(class_name, gom_path, names_path, structures):
    names = {int(item.attrib["id"]): item.attrib.get("name", "")
             for item in ET.parse(names_path).getroot()}
    ids_by_name = {name.lower(): type_id for type_id, name in names.items()}
    class_id = ids_by_name.get(class_name.lower())
    if class_id is None:
        raise SystemExit(f"unknown GOM name: {class_name}")
    items = {type_id: (offset, kind, blob)
             for offset, type_id, kind, blob in gom.records(gom_path.read_bytes())}
    _, class_kind, class_blob = items[class_id]
    if class_kind != 4:
        raise SystemExit(f"{class_name} is definition type {class_kind}, not a class")
    structures_by_class = {}
    for number, existing in structures.items():
        structures_by_class.setdefault(existing.base_class, []).append(number)
    count, fields_offset = struct.unpack_from("<hh", class_blob, 0x2E)
    print(f"\nGOM manifest only: {class_name} 0x{class_id:016X}, {count} direct fields")
    unresolved = []
    for index in range(count):
        field_id = struct.unpack_from("<Q", class_blob, fields_offset + index * 8)[0]
        _, field_kind, field_blob = items[field_id]
        if field_kind != 3:
            print(f"  {index}: {names.get(field_id, '<unnamed>')} definitionType={field_kind}")
            unresolved.append(field_id)
            continue
        type_offset = struct.unpack_from("<h", field_blob, 0x12)[0]
        parts, _ = parse_manifest_type(field_blob, type_offset, structures_by_class)
        description = " -> ".join(decoder.describe_part(part, names) for part in parts)
        print(f"  {index}: {names.get(field_id, '<unnamed>')} 0x{field_id:016X} {description}")
        for part in parts:
            if part.kind == 9 and not part.structure:
                unresolved.append(part.definition)
                print(f"       UNRESOLVED: embedded class {names.get(part.definition, hex(part.definition))} "
                      "has no unique structure in the captured CRT1 table")
    if unresolved:
        print("Manifest is not encodable: embedded structure references remain unresolved.")
    else:
        print("Manifest type references resolve against CRT1; value/state semantics still require verification.")


def propose_phase_schema(gom_path, names_path, structures):
    """Build an in-memory schema proposal; never emit a packet or fixture."""
    names = {int(item.attrib["id"]): item.attrib.get("name", "")
             for item in ET.parse(names_path).getroot()}
    ids_by_name = {name.lower(): type_id for type_id, name in names.items()}
    items = {type_id: (offset, kind, blob)
             for offset, type_id, kind, blob in gom.records(gom_path.read_bytes())}
    proposed = dict(structures)
    next_number = max(proposed) + 1
    assigned = {}
    order = ("phsActivePhaseInfo", "phsUniqueActivePhaseInfo", "phsPlayerPhaseData")
    for class_name in order:
        class_id = ids_by_name[class_name.lower()]
        _, kind, blob = items[class_id]
        if kind != 4:
            raise ValueError(f"{class_name} is not a GOM class")
        component_count, components_offset, field_count, fields_offset = struct.unpack_from(
            "<hhhh", blob, 0x2A)
        components = [struct.unpack_from("<Q", blob, components_offset + i * 8)[0]
                      for i in range(component_count)]
        structure_map = {}
        for number, existing in proposed.items():
            structure_map.setdefault(existing.base_class, []).append(number)
        fields = []
        for i in range(field_count):
            field_id = struct.unpack_from("<Q", blob, fields_offset + i * 8)[0]
            _, field_kind, field_blob = items[field_id]
            if field_kind != 3:
                raise ValueError(f"field 0x{field_id:016X} is definition type {field_kind}")
            type_offset = struct.unpack_from("<h", field_blob, 0x12)[0]
            parts, _ = parse_manifest_type(field_blob, type_offset, structure_map)
            unresolved = [part.definition for part in parts
                          if part.kind == 9 and not part.structure]
            if unresolved:
                raise ValueError("unresolved embedded classes: " +
                                 ", ".join(names.get(x, hex(x)) for x in unresolved))
            fields.append(decoder.Field(field_id, parts))
        # Every captured compact structure orders its selected fields by ID.
        fields.sort(key=lambda field: field.definition)
        proposed[next_number] = decoder.Structure(
            next_number, class_id, components, fields)
        assigned[class_id] = next_number
        print(f"  proposed structure {next_number}: {class_name}, "
              f"components={len(components)} fields={len(fields)}")
        next_number += 1

    encoded = encode_schema(proposed)
    decoded, consumed = decode_schema_bytes(encoded)
    if consumed != len(encoded) or encode_schema(decoded) != encoded:
        raise SystemExit("FAIL: proposed schema did not round-trip in memory")
    print(f"PASS: proposed {len(proposed)}-structure table round-trips in memory "
          f"({len(encoded)} bytes).")
    print("NOT VERIFIED FOR WIRE USE: new structure numbers are session-local proposals; "
          "no value/state bytes or .acrt file were generated.")
    return proposed, assigned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crt1", type=Path, default=decoder.CRT_DIR /
                        "tython_blockout-4611686019869492753-1.1.acrt")
    parser.add_argument("--manifest", metavar="GOM_CLASS",
                        help="print a non-encodable GOM-to-style-7 type manifest")
    parser.add_argument("--propose-phase-schema", action="store_true",
                        help="build and round-trip a phase schema in memory only")
    parser.add_argument("--gom", type=Path, default=gom.DEFAULT_GOM)
    parser.add_argument("--names", type=Path, default=gom.DEFAULT_NAMES)
    args = parser.parse_args()

    original = args.crt1.read_bytes()
    structures, consumed, total = decoder.read_schema() if args.crt1 == (
        decoder.CRT_DIR / "tython_blockout-4611686019869492753-1.1.acrt") else read_schema(args.crt1)
    encoded = encode_schema(structures)
    expected = original[8:consumed]
    difference = first_difference(expected, encoded)
    if difference is not None:
        expected_byte = expected[difference] if difference < len(expected) else None
        actual_byte = encoded[difference] if difference < len(encoded) else None
        raise SystemExit(
            f"FAIL: schema round trip differs at schema+0x{difference:X}: "
            f"expected={expected_byte!r} actual={actual_byte!r}; "
            f"expectedLength={len(expected)} actualLength={len(encoded)}")
    print(f"PASS: {len(structures)} compact structures round-trip byte-exact "
          f"({len(encoded)} bytes at CRT1 offsets 0x8..0x{consumed:X}).")
    print(f"CRT1 trailing transaction data remains untouched: {total - consumed} bytes.")
    if args.manifest:
        print_class_manifest(args.manifest, args.gom, args.names, structures)
    if args.propose_phase_schema:
        print("\nOffline phase-schema proposal:")
        propose_phase_schema(args.gom, args.names, structures)


def read_schema(path):
    data = path.read_bytes()
    reader = decoder.Reader(data, 8)
    structures = {}
    for _ in range(reader.packed()):
        number = reader.packed()
        base_class = reader.packed()
        additional = [reader.packed() for _ in range(reader.packed())]
        fields = []
        for _ in range(reader.packed()):
            definition = reader.packed()
            parts = [decoder.TypePart(reader.packed(), reader.packed(), reader.packed())
                     for _ in range(reader.packed())]
            fields.append(decoder.Field(definition, parts))
        structures[number] = decoder.Structure(number, base_class, additional, fields)
    return structures, reader.pos, len(data)


def decode_schema_bytes(data):
    reader = decoder.Reader(data)
    structures = {}
    for _ in range(reader.packed()):
        number = reader.packed()
        base_class = reader.packed()
        additional = [reader.packed() for _ in range(reader.packed())]
        fields = []
        for _ in range(reader.packed()):
            definition = reader.packed()
            parts = [decoder.TypePart(reader.packed(), reader.packed(), reader.packed())
                     for _ in range(reader.packed())]
            fields.append(decoder.Field(definition, parts))
        structures[number] = decoder.Structure(number, base_class, additional, fields)
    return structures, reader.pos


if __name__ == "__main__":
    main()
