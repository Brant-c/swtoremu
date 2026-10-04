#!/usr/bin/env python3
"""Find exact 64-bit identifiers in mapped memory from a preserved minidump."""

import argparse
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "world_dump", HERE / "Analyze-WorldEntryDump.py")
world_dump = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world_dump)
Minidump = world_dump.Minidump


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", type=Path)
    parser.add_argument("ids", nargs="+", help="integer or 0x-prefixed ID")
    args = parser.parse_args()
    wanted = [int(value, 0) for value in args.ids]
    dump = Minidump(args.dump)
    try:
        for value in wanted:
            needles = {
                "little": value.to_bytes(8, "little"),
                "big": value.to_bytes(8, "big"),
            }
            hits = []
            for start, size, file_offset in dump.memory:
                chunk = dump.m[file_offset:file_offset + size]
                for order, needle in needles.items():
                    cursor = 0
                    while True:
                        hit = chunk.find(needle, cursor)
                        if hit < 0:
                            break
                        hits.append((start + hit, order))
                        cursor = hit + 1
            print(f"0x{value:016X}: {len(hits)} hit(s)")
            for address, order in hits[:100]:
                print(f"  0x{address:08X} {order}")
    finally:
        dump.close()


if __name__ == "__main__":
    main()
