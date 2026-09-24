#!/usr/bin/env python3
"""Read-only, build-specific CRT reader check for the captured x86 client.

Uses the frame returning to RVA 0x1AE35A (the three-component reader call)
plus repeated reader arguments in its callers. No guessed pointer scanning.
Offsets describe this observed client build, not a general Hero decoder.
"""
import argparse
import importlib.util
from pathlib import Path
import struct

spec = importlib.util.spec_from_file_location(
    'world_dump', Path(__file__).with_name('Analyze-WorldEntryDump.py'))
world_dump = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world_dump)


def frames(dump):
    rva, _ = dump.streams[6][0]
    size, context = world_dump.u('II', dump.m, rva + 160)
    dump.exception()  # Validate x86 context before using EBP.
    bp = world_dump.u('I', dump.m, context + 180)[0]
    for _ in range(64):
        raw = dump.read(bp, 16)
        if len(raw) != 16:
            return
        next_bp, ret, arg1, arg2 = struct.unpack('<4I', raw)
        yield bp, ret, arg1, arg2
        if next_bp <= bp or next_bp - bp > 0x10000 or next_bp % 4:
            return
        bp = next_bp


def reader_buffer(dump, address):
    raw = dump.read(address, 40)
    if len(raw) != 40:
        raise ValueError('Reader header is not fully mapped')
    words = struct.unpack('<10I', raw)
    style, cursor, length, capacity, pointer = (
        words[0], words[6], words[7], words[8], words[9])
    if style != 7 or not 0 < length <= capacity <= 1024 * 1024 or cursor > length:
        raise ValueError('Reader does not match the observed bounded style-7 layout')
    blob = dump.read(pointer, length)
    if len(blob) != length:
        raise ValueError('Declared reader buffer is not fully mapped')
    return pointer, cursor, length, blob


def fixture_matches(blob, root):
    # Restrict searches to the small area fixtures, not archives or dumps.
    for path in sorted(root.rglob('*')):
        if path.suffix not in ('.acrt', '.aaw', '.aeff', '.ahp'):
            continue
        if path.stat().st_size > 4 * 1024 * 1024:
            continue
        data = path.read_bytes()
        start = 0
        while True:
            offset = data.find(blob, start)
            if offset < 0:
                break
            yield path, offset
            start = offset + 1


def inspect(path, fixtures, emitted_packet=None):
    dump = world_dump.Minidump(path)
    try:
        base = next(base for base, _, name in dump.modules()
                    if Path(name).name.lower() == 'swtor-emu.exe')
        chain = list(frames(dump))
        candidates = [frame for frame in chain if frame[1] - base == 0x1AE35A]
        if len(candidates) != 1:
            raise ValueError('Expected one three-component-reader frame for this build')
        address = candidates[0][2]
        if sum(frame[2] == address for frame in chain) < 3:
            raise ValueError('Reader argument is not corroborated by caller frames')
        pointer, cursor, length, blob = reader_buffer(dump, address)
        print(f'{path}\nreader={address:08X} buffer={pointer:08X} '
              f'style=7 cursor={cursor} length={length} remaining={length-cursor}')
        print('buffer:', blob.hex(' '))
        matches = list(fixture_matches(blob, fixtures))
        for file, offset in matches:
            print(f'exact match: {file} offset={offset} bytes={len(blob)}')
        if not matches:
            raise ValueError('No exact fixture match')
        if emitted_packet is not None:
            packet = emitted_packet.read_bytes()
            # Explicitly scoped to the 55-byte CRT3 fixture, not a generic parser.
            if (len(packet) != 63 or packet[:4] != bytes.fromhex('80 6e 44 0d')
                    or packet[35:38] != bytes.fromhex('05 07 19')):
                raise ValueError('Expected emitted CRT3 packet with 25-byte style-7 blob')
            emitted = packet[38:]
            if emitted != blob:
                offset = next((i for i, (a, b) in enumerate(zip(emitted, blob))
                               if a != b), min(len(emitted), len(blob)))
                raise ValueError(f'Emitted/client buffer first differs at offset {offset}')
            print(f'PASS: all {len(blob)} emitted bytes match the active client buffer; '
                  'no mismatching byte.')
        print('Scope: identifies input and exhaustion, not field schema or a repair.')
    finally:
        dump.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dumps', type=Path, nargs='+')
    parser.add_argument('--emitted-packet', type=Path,
                        help='Optional plaintext CRT3 packet emitted by the wire test')
    parser.add_argument('--fixtures', type=Path, default=Path(__file__).resolve().parent.parent /
                        'SharpServer/bin/Debug/AreaServer')
    args = parser.parse_args()
    if not args.fixtures.is_dir():
        parser.error('Fixture directory does not exist')
    for path in args.dumps:
        inspect(path, args.fixtures, args.emitted_packet)


if __name__ == '__main__':
    main()
