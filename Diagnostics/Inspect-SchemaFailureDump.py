#!/usr/bin/env python3
"""Locate the bounded schema reader in the saved candidate-CRT failure dump.

This is deliberately build- and dump-specific.  It follows the saved x86 EBP
chain, identifies the frame returning into the native type-description reader,
and reports bounded reader-shaped arguments without executing client code.
"""
import importlib.util
import struct
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "world_dump", HERE / "Analyze-WorldEntryDump.py")
world_dump = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world_dump)


def frames(dump):
    rva, _ = dump.streams[6][0]
    _, context = world_dump.u("II", dump.m, rva + 160)
    dump.exception()  # validates the x86 context layout
    bp = world_dump.u("I", dump.m, context + 180)[0]
    for depth in range(64):
        raw = dump.read(bp, 40)
        if len(raw) != 40:
            return
        words = struct.unpack("<10I", raw)
        yield depth, bp, words
        next_bp = words[0]
        if next_bp <= bp or next_bp - bp > 0x10000 or next_bp % 4:
            return
        bp = next_bp


def reader(dump, address):
    raw = dump.read(address, 40)
    if len(raw) != 40:
        return None
    words = struct.unpack("<10I", raw)
    style, cursor, length, capacity, pointer = (
        words[0], words[6], words[7], words[8], words[9])
    if style not in range(1, 11):
        return None
    if not (0 < length <= capacity <= 4 * 1024 * 1024 and cursor <= length):
        return None
    blob = dump.read(pointer, length)
    if len(blob) != length:
        return None
    return style, cursor, length, capacity, pointer, blob


def memory_hits(dump, needle):
    for start, size, _ in dump.memory:
        address = start & 0xFFFFFFFF
        blob = dump.read(address, size)
        cursor = 0
        while True:
            offset = blob.find(needle, cursor)
            if offset < 0:
                break
            yield address + offset
            cursor = offset + 1


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: Inspect-SchemaFailureDump.py <dump> [candidate-crt1]")
    dump = world_dump.Minidump(Path(sys.argv[1]))
    try:
        modules = dump.modules()
        for depth, bp, words in frames(dump):
            ret = words[1]
            symbol = dump.symbolize(ret, modules)
            print(f"frame[{depth}] ebp={bp:08X} ret={symbol}")
            seen = set()
            for slot, value in enumerate(words[2:], 2):
                if value in seen:
                    continue
                seen.add(value)
                candidate = reader(dump, value)
                if candidate is None:
                    continue
                style, cursor, length, capacity, pointer, blob = candidate
                lo = max(0, cursor - 24)
                hi = min(length, cursor + 24)
                print(f"  +{slot * 4:02X} reader={value:08X} style={style} "
                      f"cursor={cursor} length={length} capacity={capacity} "
                      f"buffer={pointer:08X}")
                print(f"    bytes[{lo}:{hi}]={blob[lo:hi].hex(' ')}")
        if len(sys.argv) == 3:
            candidate = Path(sys.argv[2]).read_bytes()
            whole_hits = list(memory_hits(dump, candidate))
            print(f"candidate whole-file hits: {[f'{x:08X}' for x in whole_hits]}")
            for hit in whole_hits:
                for delta in (0, 8, len(candidate), len(candidate) - 256):
                    refs = list(memory_hits(dump, struct.pack('<I', hit + delta)))
                    print(f"  file+{delta} pointer refs: "
                          f"{[f'{x:08X}' for x in refs[:32]]}")
            # The generated phase definitions are at the end of CRT1's style-7
            # value.  A long suffix is unique enough to find the active copy.
            needle = candidate[-256:]
            hits = list(memory_hits(dump, needle))
            print(f"candidate final-256-byte hits: {[f'{x:08X}' for x in hits]}")
            for hit in hits:
                buffer_end = hit + len(needle)
                pointer_needles = (struct.pack('<I', hit),
                                   struct.pack('<I', buffer_end))
                for label, pointer_needle in zip(("suffix", "end"), pointer_needles):
                    refs = list(memory_hits(dump, pointer_needle))
                    print(f"  {label} pointer refs: {[f'{x:08X}' for x in refs[:32]]}")
    finally:
        dump.close()


if __name__ == "__main__":
    main()
