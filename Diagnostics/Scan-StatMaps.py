#!/usr/bin/env python3
"""Locate plausible modStat map values inside the captured CRT2 player body."""

import importlib.util
import math
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d7", HERE / "Decode-Style7Replication.py")
d7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d7)


def packed(data, pos, end):
    token = data[pos]
    pos += 1
    if token < 0xC0:
        return token, pos
    if not 0xC8 <= token <= 0xCF:
        raise ValueError
    size = token - 0xC7
    if pos + size > end:
        raise ValueError
    return int.from_bytes(data[pos:pos + size], "big"), pos + size


def player_record():
    data = d7.fixture(2)
    reader, _, count = d7.read_gom_update(data, 4, "CRT2")
    for _ in range(count):
        rec = d7.read_object_record(data, reader)
        if rec["structure_id"] == 26:
            return data, rec
    raise RuntimeError("CRT2 player record missing")


def simple_maps(data, start, end):
    for offset in range(start, end):
        try:
            count, pos = packed(data, offset, end)
            if not 5 <= count <= 260:
                continue
            entries = []
            previous = 0
            for _ in range(count):
                key, pos = packed(data, pos, end)
                if not previous < key <= 0x101:
                    raise ValueError
                if pos + 4 > end:
                    raise ValueError
                value = struct.unpack_from("<f", data, pos)[0]
                pos += 4
                if not math.isfinite(value) or abs(value) > 1e8:
                    raise ValueError
                entries.append((key, value))
                previous = key
            print(f"simple offset=0x{offset - start:X} count={count} bytes={pos-offset}")
            print("  " + ", ".join(f"{key:X}={value:g}" for key, value in entries))
        except (IndexError, ValueError):
            pass


def nested_maps(data, start, end):
    for offset in range(start, end):
        try:
            count, pos = packed(data, offset, end)
            if not 1 <= count <= 80:
                continue
            result = []
            previous = 0
            total_sources = 0
            for _ in range(count):
                stat, pos = packed(data, pos, end)
                if not previous < stat <= 0x101:
                    raise ValueError
                source_count, pos = packed(data, pos, end)
                if not 1 <= source_count <= 32:
                    raise ValueError
                sources = []
                for _ in range(source_count):
                    source, pos = packed(data, pos, end)
                    if pos + 4 > end:
                        raise ValueError
                    value = struct.unpack_from("<f", data, pos)[0]
                    pos += 4
                    if not math.isfinite(value) or abs(value) > 1e8:
                        raise ValueError
                    sources.append((source, value))
                result.append((stat, sources))
                total_sources += source_count
                previous = stat
            if total_sources < 2:
                continue
            print(f"nested offset=0x{offset-start:X} stats={count} sources={total_sources} bytes={pos-offset}")
            for stat, sources in result:
                print(f"  {stat:X}: " + ", ".join(
                    f"{source:016X}={value:g}" for source, value in sources))
        except (IndexError, ValueError):
            pass


def main():
    data, rec = player_record()
    start = rec["body_start"]
    end = start + rec["inner_size"]
    print(f"body=0x{start:X}..0x{end:X} ({end-start} bytes)")
    simple_maps(data, start, end)
    nested_maps(data, start, end)


if __name__ == "__main__":
    main()
