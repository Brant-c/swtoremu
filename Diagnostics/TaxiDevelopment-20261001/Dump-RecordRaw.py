"""Dump the raw bytes of one awareness record from its record header onward.

Usage: python Dump-RecordRaw.py <node_hex> [capture-file]
Default capture is tython_blockout-4611686019869492753-1.1.aaw; pass 1.2.aaw to
inspect the Weller capture.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / '_recorddump.txt'
lines = []


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


d7 = load('d7', ROOT / 'Diagnostics/Decode-Style7Replication.py')
capture = sys.argv[2] if len(sys.argv) > 2 else 'tython_blockout-4611686019869492753-1.1.aaw'
data = (ROOT / 'SharpServer/bin/Debug/AreaServer/Awareness' / capture).read_bytes()
reader, flags, count = d7.read_gom_update(data, 0, capture)
records = [d7.read_object_record(data, reader) for _ in range(count)]

want = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x1AC68957EB
i = next(k for k, r in enumerate(records) if r['node'] == want)
r = records[i]
nxt = records[i + 1] if i + 1 < len(records) else None
start = r['start']
stop = nxt['start'] if nxt else len(data)
lines.append('rec %d node=%#x start=%d stop=%d flags=0x%02X struct=%s '
             'style=%s inner=%s body_start=%s value_end=%s meta=%s' % (
                 i, r['node'], start, stop, r['flags'], r['structure_id'],
                 r['style'], r['inner_size'], r['body_start'], r['value_end'],
                 r['metadata_counts']))
lines.append('outer_start=%s (structure_id+inner occupy %d bytes)' % (
    r['outer_start'], r['body_start'] - r['outer_start']))
lines.append('')
for off in range(start, stop, 16):
    chunk = data[off:min(off + 16, stop)]
    tag = ''
    if r['outer_start'] <= off < r['body_start']:
        tag = '  <- style/structure header'
    elif off == r['body_start']:
        tag = '  <- value body start'
    elif off == r['body_start'] + r['inner_size']:
        tag = '  <- state stream start'
    lines.append('  @%5d (%+5d rel body)  %-47s%s' % (
        off, off - r['body_start'], chunk.hex(' '), tag))

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('wrote %s' % OUT)