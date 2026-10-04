import sys, re
exe = sys.argv[1]
data = open(exe, 'rb').read()
# extract ASCII strings length >= 5
strs = []
for m in re.finditer(rb'[\x20-\x7e]{5,}', data):
    strs.append((m.start(), m.group().decode('ascii')))
print('total ascii strings (len>=5): %d' % len(strs))
terms = ['gnarls', 'Room', 'room', 'SetRoom', 'RoomName', '_Room', 'Room Specification', 'Area', 'area', 'portal', 'Portal', 'collision', 'Collision']
for off, s in strs:
    if any(t in s for t in terms):
        print('0x%08X  %r' % (off, s))
