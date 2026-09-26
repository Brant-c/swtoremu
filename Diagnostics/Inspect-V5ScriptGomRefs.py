#!/usr/bin/env python3
"""Resolve big-endian packed GOM references in a decrypted SWTOR v5 script."""

import argparse
import importlib.util
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAMES = ROOT / "Tools/tor_tools/gom_type_names.xml"


def script_payload(path):
    data = path.read_bytes()
    if data[:4] != b"SCPT":
        return data
    scan_path = Path(__file__).resolve().with_name("Scan-ScriptRpcIds.py")
    spec = importlib.util.spec_from_file_location("scan_script_ids", scan_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.decode_v5_scpt(path)


def read_number(data, offset):
    token = data[offset]
    offset += 1
    if token < 0xC0:
        return token, offset
    if 0xC0 <= token <= 0xC7:
        size, sign = token - 0xBF, -1
    elif 0xC8 <= token <= 0xCF:
        size, sign = token - 0xC7, 1
    elif token == 0xD0:
        return -(1 << 63), offset
    else:
        raise ValueError(f"invalid packed-number token 0x{token:02X} at 0x{offset - 1:X}")
    end = offset + size
    if end > len(data):
        raise ValueError("truncated packed number")
    return sign * int.from_bytes(data[offset:end], "big"), end


def string_table(data):
    offset = 0
    count, offset = read_number(data, offset)
    result = []
    for _ in range(count):
        length, offset = read_number(data, offset)
        end = offset + length
        result.append(data[offset:end].decode("ascii", errors="replace"))
        offset = end
    return result, offset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("--names", type=Path, default=DEFAULT_NAMES)
    args = parser.parse_args()

    data = script_payload(args.script)
    strings, body_offset = string_table(data)
    names = {int(item.attrib["id"]): item.attrib.get("name", "")
             for item in ET.parse(args.names).getroot()}

    print(f"script={args.script} strings={len(strings)} body=0x{body_offset:X}")
    for index, value in enumerate(strings):
        print(f"  string[{index}]={value!r}")
    marker = bytes((0xD1, 0x03))
    cursor = body_offset
    while True:
        cursor = data.find(marker, cursor)
        if cursor < 0:
            break
        string_index = data[cursor + 2] if cursor + 2 < len(data) else -1
        label = strings[string_index] if 0 <= string_index < len(strings) else "<out-of-range>"
        print(f"function-marker=0x{cursor:X} string[{string_index}]={label!r}")
        cursor += len(marker)

    found = 0
    cursor = body_offset
    while cursor + 9 <= len(data):
        if data[cursor] == 0xCF:
            value = struct.unpack_from(">Q", data, cursor + 1)[0]
            name = names.get(value)
            if name:
                print(f"  gom=0x{cursor:X} id=0x{value:016X} name={name}")
                found += 1
                cursor += 9
                continue
        cursor += 1
    print(f"named-gom-references={found}")


if __name__ == "__main__":
    main()
