"""Dump the one NPC-shaped replication contract in the whole capture, annotated.

CRT12 is the only captured contract that targets a known non-player character
(Weller, 0x1AC6F6DC6D), and the only working NPC in the room. It is therefore the
only available template for the contract a taxi would need. This script is the
reference for cloning that contract onto a new node id. Read only.
"""
from pathlib import Path

CRT12 = Path(r'D:\SWTORClassic\swtoremu\SharpServer\bin\Debug\AreaServer\CRT'
             r'\tython_blockout-4611686019869492753-1.12.acrt')

b = CRT12.read_bytes()
print('CRT12 full hex (%d bytes):' % len(b))
for i in range(0, len(b), 8):
    print('  %2d: %s' % (i, ' '.join('%02x' % x for x in b[i:i + 8])))

print('\nlayout:')
print('  0-3   stream id       = %s' % b[0:4].hex())
print('  4-7   schema count    = %d' % int.from_bytes(b[4:8], 'little'))
print('  8     flags           = 0x%02x' % b[8])
print('  9     contract count  = %d' % b[9])
print('  10-15 node prefix     = %s   (0x1AC6F6DC6D, packed)' % b[10:16].hex())
print('  16    record flags    = 0x%02x' % b[16])
print('  17    field version   = %d' % b[17])
print('  18    style           = %d' % b[18])
print('  19    value size      = %d' % b[19])
print('  20    structure id    = %d  -> 62 = chrNonPlayerCharacter' % b[20])
print('  21    inner size      = %d' % b[21])
print('  22-25 body            = %s' % b[22:].hex())

print('\nto clone onto a taxi node: replace bytes 10-15 with the packed taxi node id')
print('and keep everything else byte-identical. Structure 62 is already the taxi\'s')
print('own class, so the contract shape does not need to change.')