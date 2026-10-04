#!/usr/bin/env python3
"""Resolve an observed relocated April-client vtable through PE32 RTTI."""
from pathlib import Path
import struct
import sys


def u16(data, off): return struct.unpack_from("<H", data, off)[0]
def u32(data, off): return struct.unpack_from("<I", data, off)[0]


exe = Path(sys.argv[1])
runtime_base = int(sys.argv[2], 0)
runtime_vtable = int(sys.argv[3], 0)
data = exe.read_bytes()
pe = u32(data, 0x3C)
sections_count = u16(data, pe + 6)
optional_size = u16(data, pe + 20)
optional = pe + 24
image_base = u32(data, optional + 28)
section_table = optional + optional_size
sections = []
for index in range(sections_count):
    off = section_table + index * 40
    name = data[off:off+8].rstrip(b"\0").decode("ascii", "replace")
    virtual_size, rva, raw_size, raw = struct.unpack_from("<IIII", data, off + 8)
    sections.append((name, rva, max(virtual_size, raw_size), raw))


def rva_to_file(rva):
    for name, start, size, raw in sections:
        if start <= rva < start + size:
            return raw + rva - start
    raise ValueError(f"RVA 0x{rva:X} is outside file sections")


def va_to_file(va): return rva_to_file(va - image_base)


rva = runtime_vtable - runtime_base
preferred_vtable = image_base + rva
vtable_file = rva_to_file(rva)
col_va = u32(data, vtable_file - 4)
col_file = va_to_file(col_va)
signature, object_offset, cd_offset, type_va, hierarchy_va = struct.unpack_from("<IIIII", data, col_file)
type_file = va_to_file(type_va)
name_start = type_file + 8
name_end = data.index(b"\0", name_start)
type_name = data[name_start:name_end].decode("ascii", "replace")

print(f"exe={exe}")
print(f"runtime_base=0x{runtime_base:08X}")
print(f"runtime_vtable=0x{runtime_vtable:08X}")
print(f"rva=0x{rva:08X}")
print(f"image_base=0x{image_base:08X}")
print(f"preferred_vtable=0x{preferred_vtable:08X}")
print(f"complete_object_locator=0x{col_va:08X}")
print(f"rtti_signature={signature} object_offset=0x{object_offset:X} cd_offset=0x{cd_offset:X}")
print(f"type_descriptor=0x{type_va:08X}")
print(f"type_name={type_name}")
print(f"class_hierarchy_descriptor=0x{hierarchy_va:08X}")
print("vtable_entries:")
for index in range(16):
    value = u32(data, vtable_file + index * 4)
    print(f"  [{index:02}] 0x{value:08X} rva=0x{value-image_base:08X}")

needle = struct.pack("<I", preferred_vtable)
xrefs = []
start = 0
while True:
    hit = data.find(needle, start)
    if hit < 0: break
    for name, section_rva, size, raw in sections:
        if raw <= hit < raw + size:
            xrefs.append((image_base + section_rva + hit - raw, name, hit))
            break
    start = hit + 1
print("preferred_vtable_dword_occurrences:")
for va, name, file_offset in xrefs:
    print(f"  va=0x{va:08X} section={name} file=0x{file_offset:X}")
