#!/usr/bin/env python3
"""Locate a byte pattern in PE sections and print nearby x86 instructions."""

import argparse
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32


def sections(data):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    count = struct.unpack_from("<H", data, pe + 6)[0]
    optional_size = struct.unpack_from("<H", data, pe + 20)[0]
    optional = pe + 24
    image_base = struct.unpack_from("<I", data, optional + 28)[0]
    table = optional + optional_size
    for index in range(count):
        off = table + index * 40
        name = data[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII", data, off + 8
        )
        yield name, image_base + virtual_address, raw_offset, raw_size, virtual_size


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("hex_pattern", help="hex bytes, e.g. 901cf4db")
    parser.add_argument("--context", type=int, default=48)
    parser.add_argument("--virtual-address", type=lambda value: int(value, 0))
    parser.add_argument("--length", type=int, default=256)
    parser.add_argument("--data", action="store_true")
    args = parser.parse_args()

    data = args.image.read_bytes()
    needle = bytes.fromhex(args.hex_pattern)
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)

    if args.virtual_address is not None:
        for name, va, raw, raw_size, _ in sections(data):
            if va <= args.virtual_address < va + raw_size:
                offset = args.virtual_address - va
                body = data[raw + offset:raw + min(raw_size, offset + args.length)]
                print(f"{name}: VA=0x{args.virtual_address:08X}")
                if args.data:
                    for row in range(0, len(body), 16):
                        chunk = body[row:row + 16]
                        print(f"{args.virtual_address + row:08X}  " + " ".join(f"{value:02X}" for value in chunk))
                    return
                for insn in decoder.disasm(body, args.virtual_address):
                    print(f"   {insn.address:08X}  {insn.mnemonic:8} {insn.op_str}")
                return
        raise SystemExit("virtual address is outside the file-backed sections")

    found = 0
    for name, va, raw, raw_size, _ in sections(data):
        body = data[raw:raw + raw_size]
        start = 0
        while True:
            match = body.find(needle, start)
            if match < 0:
                break
            found += 1
            match_va = va + match
            print(f"{name}: file+0x{raw + match:08X} VA=0x{match_va:08X}")
            begin = max(0, match - args.context)
            end = min(len(body), match + len(needle) + args.context)
            for insn in decoder.disasm(body[begin:end], va + begin):
                marker = "=>" if insn.address <= match_va < insn.address + insn.size else "  "
                print(f"{marker} {insn.address:08X}  {insn.mnemonic:8} {insn.op_str}")
            print()
            start = match + 1
    if not found:
        print("pattern not found")


if __name__ == "__main__":
    main()
