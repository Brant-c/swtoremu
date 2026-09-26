#!/usr/bin/env python3
"""List captured replication object flags using the known outer framing."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("decoder", HERE / "Decode-Style7Replication.py")
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)

for number in range(2, 18):
    data = decoder.fixture(number)
    reader = decoder.Reader(data, 8)
    try:
        transaction_flags = reader.byte()
        count = reader.packed() if transaction_flags & 1 else 0
        rows = []
        for index in range(count):
            start = reader.pos
            node = reader.packed()
            flags = reader.byte()
            class_id = reader.packed() if flags & 0x80 else 0
            template_id = reader.packed() if flags & 0x40 else 0
            parent_id = reader.packed() if flags & 0x20 else 0
            rows.append((index, start, node, flags, class_id, template_id, parent_id))
            if flags & 0x10:
                metadata_flags = reader.byte()
                if metadata_flags & 3:
                    metadata_count = int.from_bytes(data[reader.pos:reader.pos + 4], "little")
                    reader.pos += 4
                    for _ in range(metadata_count): reader.packed()
            if flags & 0x08:
                reader.byte(); style = reader.byte(); size = reader.packed()
                reader.pos += size
        interesting = [row for row in rows
                       if row[3] & 0x07 or 0x1AC6F6DC0E <= row[2] <= 0x1AC6F6DC1C]
        print(f"CRT{number}: objects={count} parsed={len(rows)} end=0x{reader.pos:X}/0x{len(data):X}")
        for index, start, node, flags, class_id, template_id, parent_id in interesting:
            print(f"  object={index} offset=0x{start:X} node=0x{node:016X} flags=0x{flags:02X} "
                  f"class=0x{class_id:016X} template=0x{template_id:016X} "
                  f"parent=0x{parent_id:016X}")
    except (EOFError, ValueError) as error:
        print(f"CRT{number}: stopped at object={len(rows)} offset=0x{reader.pos:X}: {error}")
        for index, start, node, flags, class_id, template_id, parent_id in rows:
            if 0x1AC6F6DC0E <= node <= 0x1AC6F6DC1C:
                print(f"  object={index} offset=0x{start:X} node=0x{node:016X} flags=0x{flags:02X} "
                      f"class=0x{class_id:016X} template=0x{template_id:016X} "
                      f"parent=0x{parent_id:016X}")
