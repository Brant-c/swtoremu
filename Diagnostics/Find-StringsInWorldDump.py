#!/usr/bin/env python3
"""Read-only string search over mapped memory from a preserved minidump.

Used to answer whether specific static area data (room names and trigger
parameters) is resident in the client at all. This is evidence gathering only:
it never invokes client code and never writes to the dump.

Searches for each needle as ASCII and as UTF-16LE, case-insensitively for
ASCII, and reports the mapped address of every hit.
"""

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
    parser.add_argument("needles", nargs="+", help="substring to locate")
    parser.add_argument("--max-hits", type=int, default=20,
                        help="stop reporting after this many hits per needle")
    args = parser.parse_args()

    dump = Minidump(args.dump)
    try:
        for text in args.needles:
            variants = {
                "ascii": text.encode("ascii"),
                "utf16": text.encode("utf-16-le"),
            }
            hits = {name: [] for name in variants}
            for start, size, file_offset in dump.memory:
                chunk = dump.m[file_offset:file_offset + size]
                lowered = chunk.lower()
                for name, needle in variants.items():
                    if name == "utf16":
                        probe = needle
                        haystack = chunk
                    else:
                        probe = needle.lower()
                        haystack = lowered
                    cursor = 0
                    while len(hits[name]) < args.max_hits:
                        hit = haystack.find(probe, cursor)
                        if hit < 0:
                            break
                        hits[name].append(start + hit)
                        cursor = hit + 1
            print(f"=== {text!r} ===")
            for name in variants:
                locations = hits[name]
                print(f"  {name}: {len(locations)} (capped) hit(s)")
                for address in locations:
                    print(f"    0x{address:08X}")
    finally:
        dump.close()


if __name__ == "__main__":
    main()
