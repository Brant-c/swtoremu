import io, sys

p = r'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Server\AreaStartupBundle.cs'
lines = io.open(p, encoding='utf-8-sig', newline='').read().split('\n')

# Find the CRT2 line (the only '..., 2, characterID' transaction)
crt2_idx = None
for i, l in enumerate(lines):
    if 'ReplicationTransaction(area, areaID, areaCode, 2, characterID)' in l:
        crt2_idx = i
        break

print('CRT2 line index:', crt2_idx)
for j in range(crt2_idx - 3, crt2_idx + 2):
    print('  %d: %r' % (j, lines[j]))

# Remove the preceding 'if (client.ActiveCharacter != null)' + 'SetCharacter' lines
# (the OLD SetCharacter that was before CRT2). The NEW SetCharacter (before HackPack)
# is untouched because it is not followed by CRT2.
assert 'if (client.ActiveCharacter != null)' in lines[crt2_idx - 2], lines[crt2_idx - 2]
assert 'AreaSetCharacter' in lines[crt2_idx - 1], lines[crt2_idx - 1]
del lines[crt2_idx - 2:crt2_idx]

io.open(p, 'w', encoding='utf-8-sig', newline='').write('\n'.join(lines))
print('removed old SetCharacter; done')
