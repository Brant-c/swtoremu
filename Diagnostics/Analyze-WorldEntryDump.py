#!/usr/bin/env python3
"""Read-only analyzer for the world-entry minidumps.

Parses a Windows minidump, extracts the exception record, decodes the
MSVC C++ exception (0xE06D7363) metadata and candidate text buffers.
Reports stack address candidates as module+offset (not an unwound call
stack). Does not execute what() or any other code from the dump.
"""
import mmap
import struct
import sys
from pathlib import Path

MAGIC_MSVC = (0x19930520, 0x19930521, 0x19930522)


def u(fmt, buf, off=0):
    return struct.unpack_from('<' + fmt, buf, off)


class Minidump:
    def __init__(self, path):
        self.f = open(path, 'rb')
        self.m = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
        m = self.m
        sig, ver, nstreams, dirrva, _ = u('IIIII', m, 0)
        assert sig == 0x504D444D, 'not a minidump'
        self.streams = {}
        for i in range(nstreams):
            st, size, rva = u('III', m, dirrva + i * 12)
            self.streams.setdefault(st, []).append((rva, size))
        self.memory = self._memlist()

    def close(self):
        self.m.close()
        self.f.close()

    # ---- memory access -------------------------------------------------
    def _memlist(self):
        # Memory64ListStream (9): number, base_rva, then (start, size) pairs
        rva, _ = self.streams[9][0]
        count, base = u('QQ', self.m, rva)
        entries = []
        off = base
        p = rva + 16
        for _ in range(count):
            start, size = u('QQ', self.m, p)
            entries.append((start, size, off))
            off += size
            p += 16
        return entries

    def read(self, addr, length):
        for start, size, off in self.memory:
            # Some x86 dumps sign-extend addresses above 0x7fffffff.
            # Normalize only that representation for a 32-bit lookup.
            if 0 <= addr <= 0xffffffff and start >> 32 == 0xffffffff:
                start &= 0xffffffff
            if start <= addr < start + size:
                n = min(length, start + size - addr)
                return self.m[off + (addr - start): off + (addr - start) + n]
        return b''

    # ---- modules -------------------------------------------------------
    def modules(self):
        rva, _ = self.streams[4][0]
        count = u('I', self.m, rva)[0]
        out = []
        p = rva + 4
        for _ in range(count):
            base, size, cksum, tstamp, name_rva = u('QIIII', self.m, p)
            nlen = u('I', self.m, name_rva)[0]
            name = self.m[name_rva + 4: name_rva + 4 + nlen].decode('utf-16-le')
            out.append((base, size, name.rstrip('\0')))
            p += 108  # Fixed-size MINIDUMP_MODULE; name lives at a separate RVA.
        return out

    def symbolize(self, addr, modules):
        for base, size, name in modules:
            if base <= addr < base + size:
                short = Path(name).name
                return f'{short}+{addr - base:08X}'
        return f'{addr:08X}'

    # ---- exception -----------------------------------------------------
    def exception(self):
        rva, size = self.streams[6][0]
        tid, _align = u('II', self.m, rva)
        code, flags, record, addr, nparams = u('IIQQI', self.m, rva + 8)
        if nparams > 15:
            raise ValueError('Invalid exception parameter count')
        params = u('15Q', self.m, rva + 40)[:nparams]
        ctx_size, ctx_rva = u('II', self.m, rva + 160)
        if ctx_size < 204 or not (u('I', self.m, ctx_rva)[0] & 0x10000):
            raise ValueError('Expected x86 CONTEXT')
        esp = u('I', self.m, ctx_rva + 196)[0]
        eip = u('I', self.m, ctx_rva + 184)[0]
        return {
            'thread_id': tid, 'code': code, 'flags': flags,
            'address': addr, 'params': params, 'esp': esp, 'eip': eip,
        }


def decode_msvc_exc(dump, params):
    """Inspect x86 MSVC metadata without executing any code from the dump."""
    if len(params) != 3 or params[0] not in MAGIC_MSVC:
        print('Unsupported MSVC exception parameter layout')
        return
    _, obj_ptr, throw_info = params
    # x86 ThrowInfo contains four DWORDs, the last pointing to the array.
    ctarray = u('4I', dump.read(throw_info, 16))[3]
    ncatch = u('I', dump.read(ctarray, 4))[0]
    if not 1 <= ncatch <= 64:
        raise ValueError(f'Invalid catchable type count: {ncatch}')
    object_size = None
    for i in range(ncatch):
        ct = u('I', dump.read(ctarray + 4 + 4 * i, 4))[0]
        # properties, TypeDescriptor*, PMD (3 ints), size, copy function.
        props, descriptor, mdisp, pdisp, vdisp, size, copy = u(
            'IIiiiII', dump.read(ct, 28))
        name = dump.read(descriptor + 8, 256).split(b'\0')[0]
        print(f'catchable[{i}]: {name!r} size={size} displacement={mdisp}')
        if i == 0:
            object_size = size
    blob = dump.read(obj_ptr, min(object_size or 0, 256))
    print(f'exception object at {obj_ptr:08X}: {blob.hex(" ")}')
    # Layout of G::SerializationException is not yet known. These are only
    # candidate strings, not an invocation or confirmed result of what().
    for off in range(0, len(blob) - 3, 4):
        ptr = u('I', blob, off)[0]
        raw = dump.read(ptr, 512).split(b'\0')[0]
        if len(raw) >= 4 and all(32 <= c < 127 or c in (9, 10, 13) for c in raw):
            print(f'candidate string object+{off:02X} -> {ptr:08X}: {raw!r}')
    # Inspect possible begin/end/capacity triples observed in this object's
    # layout. Their semantics are unconfirmed; report bounded raw bytes.
    for off in (16, 32, 48):
        if len(blob) < off + 12:
            continue
        start, end, capacity = u('III', blob, off)
        print(f'candidate range object+{off:02X}: '
              f'{start:08X}..{end:08X} capacity={capacity:08X}')
        if not start or not start <= end <= capacity or end - start > 4096:
            print('  not a bounded candidate range')
            continue
        raw = dump.read(start, min(end - start, 512))
        print(f'  raw ({len(raw)} bytes mapped): {raw!r}')
        if raw:
            print(f'  utf16 candidate: '
                  f'{ascii(raw[:len(raw) // 2 * 2].decode("utf-16-le", errors="replace"))}')


def main():
    if len(sys.argv) < 2:
        print('usage: Analyze-WorldEntryDump.py <dump> [dump2 ...]')
        sys.exit(2)
    for path in sys.argv[1:]:
        print(f'=== {path} ===')
        d = Minidump(path)
        exc = d.exception()
        modules = d.modules()
        print(f"thread={exc['thread_id']} code={exc['code']:#010x} "
              f"flags={exc['flags']:#x} address={exc['address']:#010x}")
        params = exc['params']
        print('params:', [f'{p:#x}' for p in params])
        if exc['code'] == 0xE06D7363 and params:
            try:
                decode_msvc_exc(d, params)
            except (struct.error, ValueError) as error:
                print(f'Exception metadata could not be decoded: {error}')
        # walk the saved stack: scan stack memory for plausible return
        # addresses in loaded modules
        esp = exc['esp']
        stack = d.read(esp, 0x2000)
        print(f'--- stack candidates from esp={esp:#010x} (not an unwound call stack) ---')
        seen = []
        for i in range(0, len(stack) - 3, 4):
            v = u('I', stack, i)[0]
            sym = d.symbolize(v, modules)
            if '+' in sym and sym not in seen:
                seen.append(sym)
                print(f'  esp+{i:04X}: {sym}')
                if len(seen) >= 80:
                    print('  (candidate output capped at 80)')
                    break
        # strings near top of stack
        print('--- strings in first 1KB of stack ---')
        head = stack[:1024]
        cur = b''
        for idx, byte in enumerate(head):
            if 32 <= byte < 127:
                cur += bytes([byte])
            else:
                if len(cur) >= 6:
                    print(f'  esp+{idx - len(cur):04X}: {cur.decode()!r}')
                cur = b''
        d.close()


if __name__ == '__main__':
    main()