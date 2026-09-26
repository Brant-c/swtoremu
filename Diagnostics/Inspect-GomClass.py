#!/usr/bin/env python3
"""Print a client.gom class definition and the types of its direct fields."""

import argparse
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOM = ROOT / "Diagnostics/Extracted2012/resources/systemgenerated/client.gom"
DEFAULT_NAMES = ROOT / "Tools/tor_tools/gom_type_names.xml"

TYPE_NAMES = {
    0x01: "UInt64", 0x02: "Int64", 0x03: "Boolean", 0x04: "Float",
    0x05: "Enum", 0x06: "String", 0x07: "List", 0x08: "Map",
    0x09: "EmbeddedClass", 0x0B: "Array", 0x0C: "Table",
    0x0D: "Cubic", 0x0E: "Script", 0x0F: "ClassRef", 0x11: "Timer",
    0x12: "Vec3", 0x14: "TimeSpan", 0x15: "Time",
}


def parse_gom_type(blob, position, names):
    type_byte = blob[position]
    position += 1
    result = TYPE_NAMES.get(type_byte, f"unknown(0x{type_byte:02X})")
    if type_byte in (0x05, 0x09, 0x0F):
        ref = struct.unpack_from("<Q", blob, position)[0]
        return f"{result}<{names.get(ref, f'0x{ref:016X}') }>", position + 8
    if type_byte == 0x07:
        inner, position = parse_gom_type(blob, position, names)
        return f"List<{inner}>", position
    if type_byte == 0x08:
        key, position = parse_gom_type(blob, position, names)
        value, position = parse_gom_type(blob, position, names)
        return f"Map<{key}, {value}>", position
    return result, position


def records(data):
    if data[:4] != b"DBLB":
        raise ValueError("client.gom does not begin with DBLB")
    offset = 8
    while offset + 18 <= len(data):
        length = struct.unpack_from("<I", data, offset)[0]
        if not length:
            return
        if length < 18 or offset + length > len(data):
            raise ValueError(f"invalid definition length at 0x{offset:X}")
        type_id = struct.unpack_from("<Q", data, offset + 8)[0]
        flags = struct.unpack_from("<H", data, offset + 16)[0]
        blob = bytearray(data[offset:offset + length])
        # GomLib reconstructs each record with its 18-byte header zeroed.
        blob[:18] = b"\0" * 18
        yield offset, type_id, (flags >> 3) & 7, bytes(blob)
        offset += length + ((8 - (length & 7)) & 7)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("class_name")
    parser.add_argument("--gom", type=Path, default=DEFAULT_GOM)
    parser.add_argument("--names", type=Path, default=DEFAULT_NAMES)
    args = parser.parse_args()

    names = {int(item.attrib["id"]): item.attrib.get("name", "")
             for item in ET.parse(args.names).getroot()}
    ids_by_name = {name.lower(): type_id for type_id, name in names.items()}
    class_id = ids_by_name.get(args.class_name.lower())
    if class_id is None:
        raise SystemExit(f"unknown GOM name: {args.class_name}")

    items = {type_id: (offset, kind, blob)
             for offset, type_id, kind, blob in records(args.gom.read_bytes())}
    offset, kind, blob = items[class_id]
    if kind != 4:
        raise SystemExit(f"{args.class_name} is definition type {kind}, not a class")
    count, fields_offset = struct.unpack_from("<hh", blob, 0x2E)
    print(f"{args.class_name} id=0x{class_id:016X} record=0x{offset:X} fields={count}")
    for index in range(count):
        field_id = struct.unpack_from("<Q", blob, fields_offset + index * 8)[0]
        field_offset, field_kind, field_blob = items[field_id]
        if field_kind != 3:
            field_type = f"definitionType={field_kind}"
        else:
            type_offset = struct.unpack_from("<h", field_blob, 0x12)[0]
            field_type, _ = parse_gom_type(field_blob, type_offset, names)
        print(f"  {index:2}: {names.get(field_id, '<unnamed>')} "
              f"id=0x{field_id:016X} type={field_type} record=0x{field_offset:X}")


if __name__ == "__main__":
    main()
