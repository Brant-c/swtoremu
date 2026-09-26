#!/usr/bin/env python3
"""Validate the generated RequestWorldFadeIn observer against a full dump."""

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

SIGNATURE = bytes.fromhex(
    "57 56 83 EC 5C C7 04 24 2E 03 00 00 E8 00 00 00 00 "
    "C6 44 24 5B 00")
MASK = bytes((1,) * 13 + (0,) * 4 + (1,) * 5)


def main(path):
    dump = Minidump(path)
    try:
        locations = []
        for start, size, file_offset in dump.memory:
            normalized_start = start & 0xFFFFFFFF
            if normalized_start >= 0xF4000000 or normalized_start + size <= 0xE0000000:
                continue
            chunk = dump.m[file_offset:file_offset + size]
            cursor = 0
            prefix = SIGNATURE[:13]
            while True:
                offset = chunk.find(prefix, cursor)
                if offset < 0:
                    break
                if offset + len(SIGNATURE) <= len(chunk) and all(
                        not MASK[index] or chunk[offset + index] == SIGNATURE[index]
                        for index in range(len(SIGNATURE))):
                    locations.append(normalized_start + offset)
                cursor = offset + 1
        if len(locations) != 1:
            raise SystemExit(
                f"FAIL: expected one RequestWorldFadeIn body, found {len(locations)}")
        method = locations[0]
        checks = {
            0x11E: bytes.fromhex("C7 04 24 32 03 00 00"),
            0x15C: bytes.fromhex("C7 04 24 33 03 00 00"),
        }
        for offset, expected in checks.items():
            actual = dump.read(method + offset, len(expected))
            if actual != expected:
                raise SystemExit(
                    f"FAIL: +0x{offset:X} expected {expected.hex(' ')}, "
                    f"found {actual.hex(' ')}")
        print(f"PASS: RequestWorldFadeIn method={method:08X}; "
              "line 332 at +0x11E and line 333 at +0x15C")
    finally:
        dump.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: Locate-HudFadeGateInDump.py <dump>")
    main(Path(sys.argv[1]))
