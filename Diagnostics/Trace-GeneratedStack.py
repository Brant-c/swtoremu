#!/usr/bin/env python3
"""Report high-address generated-code candidates from a captured x86 stack."""

import importlib.util
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "world_dump", HERE / "Analyze-WorldEntryDump.py")
world_dump = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world_dump)
Minidump = world_dump.Minidump

if len(sys.argv) != 3:
    raise SystemExit("usage: Trace-GeneratedStack.py <dump> <hex-esp>")

dump = Minidump(Path(sys.argv[1]))
try:
    esp = int(sys.argv[2], 16)
    stack = dump.read(esp, 0x1000)
    for offset in range(0, len(stack) - 3, 4):
        value = struct.unpack_from("<I", stack, offset)[0]
        if not 0xE0000000 <= value < 0xF4000000:
            continue
        code = dump.read(max(0, value - 24), 40)
        if not code:
            continue
        print(f"esp+{offset:04X} value={value:08X}")
        print(f"  code: {code.hex(' ')}")
finally:
    dump.close()
