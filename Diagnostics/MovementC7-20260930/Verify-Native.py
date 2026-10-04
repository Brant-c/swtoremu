"""Verify bounded existing-listing excerpts against the pinned April PE."""
from pathlib import Path
import hashlib, json, re, struct
root = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
data = (root/'nexusclient/nexusclient/swtor-emu.exe').read_bytes()
sha = hashlib.sha256(data).hexdigest().upper()
assert sha == '2B47C25D2937A3DF2BE727A3224A93D748A5CDFA0F629B1A1C4FDCC163FB8494'
pe = struct.unpack_from('<I', data, 60)[0]
opt = pe+24
base = struct.unpack_from('<I', data, opt+28)[0]
sections = []
for i in range(struct.unpack_from('<H', data, pe+6)[0]):
    p = opt+struct.unpack_from('<H', data, pe+20)[0]+40*i
    _, rva, size, raw = struct.unpack_from('<IIII', data, p+8)
    sections.append((rva,size,raw))
def offset(va):
    for rva,size,raw in sections:
        if rva <= va-base < rva+size: return raw+va-base-rva
    raise ValueError(hex(va))
ranges = {'send-wrapper':(0xA80080,0xA80120),
          'movement-writer':(0xAA6920,0xAA69FF),
          'primitive-writers':(0x97C7F0,0x97C954),
          'raw-writer':(0x97C3D0,0x97C430)}
lines = {k:[] for k in ranges}
pat = re.compile(r'^\s+([0-9A-F]{8}): ((?:[0-9A-F]{2} )+)')
active=[]
count=0
with (root/'Diagnostics/swtor-disasm.txt').open(errors='replace') as f:
    for line in f:
        m=pat.match(line)
        if m:
            va=int(m[1],16)
            active=[k for k,(lo,hi) in ranges.items() if lo<=va<hi]
            if active:
                b=bytes.fromhex(m[2]); p=offset(va)
                assert data[p:p+len(b)] == b, hex(va)
                count+=1
        for k in active: lines[k].append(line.rstrip())
for k,v in lines.items(): (out/(k+'.txt')).write_text('\n'.join(v)+'\n')
(out/'verification.json').write_text(json.dumps({'PE_SHA256':sha,'verified_prefixes':count,
    'limit':'Existing listing prefixes verified; no fresh disassembly or process access'},indent=2)+'\n')
sample=(root/'Diagnostics/TriggerCollision-20260930/live-20260930-172807/movement-c7-first.bin').read_bytes()
assert len(sample)==56 and struct.unpack_from('<III',sample)==(0x61116AD5,0x65B30008,0xC7)
decoded={'heading':struct.unpack_from('<f',sample,12)[0],
         'move_vector':struct.unpack_from('<fff',sample,16),
         'end_position':struct.unpack_from('<fff',sample,28),
         'tail_u64':struct.unpack_from('<QQ',sample,40)}
(out/'decoded-first.json').write_text(json.dumps(decoded,indent=2)+'\n')
print('PASS pinned PE and',count,'printed prefixes; captured C7 offsets 12/16/28/40.')
