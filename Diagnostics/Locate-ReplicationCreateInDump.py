#!/usr/bin/env python3
"""Locate loaded chrPlayerCharacter.Replication_Create code by TrackLine spacing."""

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "world_dump", HERE / "Analyze-WorldEntryDump.py")
world_dump = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world_dump)
Minidump = world_dump.Minidump


def marker(value):
    # Generated HeroMachine x86: mov dword [esp], line; call HM.TrackLine.
    return b"\xC7\x04\x24" + value.to_bytes(4, "little") + b"\xE8"


def locate(path):
    dump = Minidump(path)
    try:
        modules = dump.modules()
        found = []
        # Jedipedia offsets are instruction offsets within the generated method.
        # Match the four anchors together, avoiding the many unrelated single hits.
        anchors = ((0x10C5, 0xA2), (0x10E5, 0xA3),
                   (0x1213, 0xAD), (0x127A, 0xB0))
        for start, size, file_offset in dump.memory:
            chunk = dump.m[file_offset:file_offset + size]
            cursor = 0
            first = marker(0xA2)
            while True:
                hit = chunk.find(first, cursor)
                if hit < 0:
                    break
                method = hit - anchors[0][0]
                if method >= 0 and all(
                        chunk[method + offset:method + offset + 8] == marker(value)
                        for offset, value in anchors):
                    address = (start & 0xFFFFFFFF) + method
                    found.append(address)
                cursor = hit + 1
        print(f"{path}: {len(found)} candidate(s)")
        if len(found) != 1:
            raise SystemExit(f"FAIL: expected one Replication_Create, found {len(found)}")
        for address in found:
            checkpoints = {
                0x10C5: 0xA2, 0x10E5: 0xA3, 0x1213: 0xAD,
                0x127A: 0xB0, 0x12D2: 0xB2, 0x130A: 0xB4,
                0x13C1: 0xB7, 0x13F7: 0xB8, 0x1497: 0xB9,
            }
            for offset, value in checkpoints.items():
                actual = dump.read(address + offset, len(marker(value)))
                if actual != marker(value):
                    raise SystemExit(
                        f"FAIL: marker {value:02X} at +0x{offset:X}: "
                        f"{actual.hex(' ')}")
            print("PASS: A2/A3/AD/B0/B2/B4/B7/B8/B9 are byte-exact instruction starts")
            print(f"method {address:08X} {dump.symbolize(address, modules)}")
            # Include the identity branch and the calls following _SetGameState.
            base = address + 0x10B0
            raw = dump.read(base, 0x2E0)
            for offset in range(0, len(raw), 16):
                data = raw[offset:offset + 16]
                print(f"  {base + offset:08X}: {data.hex(' ')}")
    finally:
        dump.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: Locate-ReplicationCreateInDump.py <dump>")
    locate(Path(sys.argv[1]))
