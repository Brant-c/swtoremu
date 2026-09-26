#!/usr/bin/env python3
"""Walk a bounded x86 EBP chain and show code preceding each return address."""

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
    raise SystemExit("usage: Trace-DumpFrameChain.py <dump> <hex-ebp>")

dump = Minidump(Path(sys.argv[1]))
try:
    modules = dump.modules()
    frame = int(sys.argv[2], 16)
    seen = set()
    for depth in range(32):
        if not frame or frame in seen:
            break
        seen.add(frame)
        raw = dump.read(frame, 8)
        if len(raw) != 8:
            print(f"{depth:02d} frame={frame:08X} unmapped")
            break
        previous, returned = struct.unpack("<II", raw)
        code = dump.read(max(0, returned - 24), 32)
        print(f"{depth:02d} frame={frame:08X} prev={previous:08X} "
              f"return={returned:08X} {dump.symbolize(returned, modules)}")
        print(f"   before/after: {code.hex(' ')}")
        frame = previous
finally:
    dump.close()
