#!/usr/bin/env python3
"""Locate a packed byte sequence within CRT objects using captured framing."""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("decoder", HERE / "Decode-Style7Replication.py")
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: Locate-CrtValue.py <crt-number> <hex-bytes>")
    number = int(sys.argv[1], 0)
    needle = bytes.fromhex(sys.argv[2])
    data = decoder.fixture(number)
    names = decoder.name_table()
    structures, _, _ = decoder.read_schema()
    reader = decoder.Reader(data, 8)
    flags = reader.byte()
    count = reader.packed() if flags & 1 else 0
    for index in range(count):
        start = reader.pos
        node = reader.packed()
        object_flags = reader.byte()
        class_id = reader.packed() if object_flags & 0x80 else 0
        if object_flags & 0x40:
            reader.packed()
        if object_flags & 0x20:
            reader.packed()
        if object_flags & 0x10:
            metadata_flags = reader.byte()
            if metadata_flags & 3:
                metadata_count = int.from_bytes(data[reader.pos:reader.pos + 4], "little")
                reader.pos += 4
                for _ in range(metadata_count):
                    reader.packed()
        structure_id = inner_size = None
        body_start = value_end = None
        if object_flags & 0x08:
            transport, style = reader.byte(), reader.byte()
            outer_size = reader.packed()
            outer_start = reader.pos
            value_end = outer_start + outer_size
            if style in (7, 8):
                structure_id = reader.packed()
                inner_size = reader.packed()
                body_start = reader.pos
            reader.pos = value_end
        end = reader.pos
        cursor = start
        while True:
            hit = data.find(needle, cursor, end)
            if hit < 0:
                break
            structure = structures.get(structure_id)
            base = structure.base_class if structure else 0
            print(f"CRT{number} object={index} range=0x{start:X}..0x{end:X} "
                  f"hit=0x{hit:X} node=0x{node:016X} flags=0x{object_flags:02X} "
                  f"class={names.get(class_id, hex(class_id))} structure={structure_id} "
                  f"base={names.get(base, hex(base))}")
            if body_start is not None:
                lo = max(body_start, hit - 32)
                hi = min(value_end, hit + len(needle) + 32)
                print("  context=" + data[lo:hi].hex(" "))
                if structure is not None and inner_size is not None:
                    state_start = body_start + inner_size
                    states, _ = decoder.field_states(
                        data, state_start, value_end - state_start,
                        len(structure.fields))
                    present = []
                    for field_index, state in enumerate(states):
                        if state != 2:
                            definition = structure.fields[field_index].definition
                            present.append(
                                f"{field_index}:{names.get(definition, hex(definition))}=state{state}")
                    print("  present-fields=" + ", ".join(present))
            cursor = hit + 1


if __name__ == "__main__":
    main()
