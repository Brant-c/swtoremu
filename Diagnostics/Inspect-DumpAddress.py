#!/usr/bin/env python3
"""Print bounded bytes at selected virtual addresses in a client dump."""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "world_dump", HERE / "Analyze-WorldEntryDump.py")
world_dump = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world_dump)
Minidump = world_dump.Minidump

if len(sys.argv) < 3:
    raise SystemExit("usage: Inspect-DumpAddress.py <dump> <hex-address> [...]")

dump = Minidump(Path(sys.argv[1]))
try:
    for value in sys.argv[2:]:
        address = int(value, 16)
        raw = dump.read(address, 128)
        printable = ''.join(chr(byte) if 32 <= byte < 127 else '.' for byte in raw)
        print(f"{address:08X} ({len(raw)} bytes): {raw.hex(' ')}")
        print(f"  {printable}")
finally:
    dump.close()
