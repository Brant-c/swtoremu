#!/usr/bin/env python3
"""Locate and inspect the recurring world-entry VM method in full minidumps."""

import importlib.util
import struct
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "world_dump", HERE / "Analyze-WorldEntryDump.py")
world_dump = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world_dump)
Minidump = world_dump.Minidump

METHOD = bytes.fromhex("4B 03 03 7D 9A 19 00 D0")
NAMES = (b"chrPlayerCharacter", b"chrAttributeComponent", b"not_found")
OPERATIONS = {
    "readiness": bytes.fromhex("F2 40 F5 F5"),
    "rpc-target": bytes.fromhex("71 C3 79 12"),
}


def dwords(data):
    return struct.unpack("<" + "I" * (len(data) // 4), data[: len(data) // 4 * 4])


def mapped(dump, address, size=64):
    data = dump.read(address, size)
    return data if len(data) == size else None


def inspect(path):
    dump = Minidump(path)
    try:
        modules = dump.modules()
        print(f"=== {path} ===")
        hits = []
        for start, size, file_offset in dump.memory:
            chunk = dump.m[file_offset:file_offset + size]
            cursor = 0
            while True:
                offset = chunk.find(METHOD, cursor)
                if offset < 0:
                    break
                address = (start & 0xFFFFFFFF) + offset
                hits.append(address)
                cursor = offset + 1
        print(f"method-pair hits: {len(hits)}")
        for address in hits[:200]:
            print(f"  {address:08X} {dump.symbolize(address, modules)}")
            base = max(0, address - 32)
            raw = dump.read(base, 128)
            print(f"    around: {raw.hex(' ')}")
            for index, value in enumerate(dwords(raw)):
                child = mapped(dump, value)
                if not child:
                    continue
                ascii_text = ''.join(chr(c) if 32 <= c < 127 else '.' for c in child)
                print(f"    ptr +{index * 4:02X} -> {value:08X}: "
                      f"{child.hex(' ')} |{ascii_text}|")
        if len(hits) > 200:
            print("  output capped at 200 hits")

        for label, needle in OPERATIONS.items():
            locations = []
            for start, size, file_offset in dump.memory:
                chunk = dump.m[file_offset:file_offset + size]
                cursor = 0
                while True:
                    offset = chunk.find(needle, cursor)
                    if offset < 0:
                        break
                    locations.append((start & 0xFFFFFFFF) + offset)
                    cursor = offset + 1
            print(f"{label} 0x{int.from_bytes(needle, 'little'):08X} hits: {len(locations)}")
            for location in locations[:64]:
                raw = dump.read(max(0, location - 48), 144)
                ascii_text = ''.join(chr(c) if 32 <= c < 127 else '.' for c in raw)
                print(f"  {location:08X}: {raw.hex(' ')} |{ascii_text}|")

        for needle in NAMES:
            locations = []
            for start, size, file_offset in dump.memory:
                chunk = dump.m[file_offset:file_offset + size]
                cursor = 0
                while True:
                    offset = chunk.find(needle, cursor)
                    if offset < 0:
                        break
                    locations.append((start & 0xFFFFFFFF) + offset)
                    cursor = offset + 1
            print(f"{needle.decode()} locations: " +
                  ", ".join(f"{value:08X}" for value in locations[:32]))
            for location in locations[:32]:
                encoded = struct.pack("<I", location)
                refs = []
                for start, size, file_offset in dump.memory:
                    chunk = dump.m[file_offset:file_offset + size]
                    cursor = 0
                    while True:
                        offset = chunk.find(encoded, cursor)
                        if offset < 0:
                            break
                        refs.append((start & 0xFFFFFFFF) + offset)
                        cursor = offset + 1
                print(f"  refs to {location:08X}: " +
                      ", ".join(f"{value:08X}" for value in refs[:64]))
                for ref in refs[:8]:
                    raw = dump.read(max(0, ref - 32), 96)
                    print(f"    {ref:08X}: {raw.hex(' ')}")
    finally:
        dump.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: Inspect-ReadinessVmDump.py <dump> [dump ...]")
    for name in sys.argv[1:]:
        inspect(Path(name))
