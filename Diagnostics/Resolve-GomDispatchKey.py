#!/usr/bin/env python3
"""Resolve an eight-byte client VM dispatch key to its client.gom definition."""

import argparse
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOM = ROOT / "Diagnostics/Extracted2012/resources/systemgenerated/client.gom"
DEFAULT_NAMES = ROOT / "Tools/tor_tools/gom_type_names.xml"


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
        yield offset, length, type_id, (flags >> 3) & 7, data[offset:offset + length]
        offset += length + ((8 - (length & 7)) & 7)


def parse_key(text):
    value = int(text, 0)
    if not 0 <= value <= 0xFFFFFFFFFFFFFFFF:
        raise argparse.ArgumentTypeError("key must fit in 64 bits")
    # Trace output prints the high and low dwords together. The GOM stores the
    # low dword first, so pack the numeric value little-endian.
    return value, struct.pack("<Q", value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("key", type=parse_key)
    parser.add_argument("--gom", type=Path, default=DEFAULT_GOM)
    parser.add_argument("--names", type=Path, default=DEFAULT_NAMES)
    args = parser.parse_args()

    names = {int(item.attrib["id"]): item.attrib.get("name", "")
             for item in ET.parse(args.names).getroot()}
    value, needle = args.key
    found = 0
    for offset, length, type_id, definition_type, blob in records(args.gom.read_bytes()):
        positions = []
        cursor = 0
        while True:
            cursor = blob.find(needle, cursor)
            if cursor < 0:
                break
            positions.append(cursor)
            cursor += 1
        if positions:
            found += 1
            print(f"0x{value:016X} -> {names.get(type_id, '<unnamed>')} "
                  f"typeId=0x{type_id:016X} definitionType={definition_type} "
                  f"record=0x{offset:X} offsets=" +
                  ",".join(f"0x{position:X}" for position in positions))
    if not found:
        print(f"0x{value:016X}: no client.gom definition contains this key")


if __name__ == "__main__":
    main()
