#!/usr/bin/env python3
"""Locate PE32 MSVC RTTI vtables for an exact decorated type name."""
from pathlib import Path
import struct
import sys


data = Path(sys.argv[1]).read_bytes()
runtime_base = int(sys.argv[2], 0)
type_name = sys.argv[3].encode("ascii")
u16 = lambda off: struct.unpack_from("<H", data, off)[0]
u32 = lambda off: struct.unpack_from("<I", data, off)[0]
pe = u32(0x3C)
count, opt_size = u16(pe + 6), u16(pe + 20)
opt = pe + 24
image_base = u32(opt + 28)
table = opt + opt_size
sections = []
for i in range(count):
    off = table + i * 40
    name = data[off:off+8].rstrip(b"\0").decode("ascii", "replace")
    virtual_size, rva, raw_size, raw = struct.unpack_from("<IIII", data, off + 8)
    sections.append((name, rva, max(virtual_size, raw_size), raw))


def file_to_va(file_offset):
    for name, rva, size, raw in sections:
        if raw <= file_offset < raw + size:
            return image_base + rva + file_offset - raw, name
    return None, None


name_offsets = []
start = 0
while True:
    hit = data.find(type_name + b"\0", start)
    if hit < 0: break
    name_offsets.append(hit)
    start = hit + 1
if not name_offsets:
    raise SystemExit(f"type name not found: {type_name.decode()}")

print(f"image_base=0x{image_base:08X} runtime_base=0x{runtime_base:08X}")
print(f"type_name={type_name.decode()}")
for name_file in name_offsets:
    td_file = name_file - 8
    td_va, td_section = file_to_va(td_file)
    print(f"type_descriptor=0x{td_va:08X} section={td_section} file=0x{td_file:X}")
    td_needle = struct.pack("<I", td_va)
    td_ref = 0
    while True:
        td_ref = data.find(td_needle, td_ref)
        if td_ref < 0: break
        col_file = td_ref - 12
        col_va, col_section = file_to_va(col_file)
        if col_va is not None and col_file >= 0 and u32(col_file) in (0, 1):
            hierarchy = u32(col_file + 16)
            print(f"  complete_object_locator=0x{col_va:08X} section={col_section} hierarchy=0x{hierarchy:08X}")
            col_needle = struct.pack("<I", col_va)
            col_ref = 0
            while True:
                col_ref = data.find(col_needle, col_ref)
                if col_ref < 0: break
                slot_va, slot_section = file_to_va(col_ref)
                if slot_va is not None:
                    preferred_vtable = slot_va + 4
                    rva = preferred_vtable - image_base
                    runtime_vtable = runtime_base + rva
                    print(f"    vtable=0x{preferred_vtable:08X} rva=0x{rva:08X} runtime=0x{runtime_vtable:08X} section={slot_section}")
                col_ref += 1
        td_ref += 1
