"""Reliable recursive grep: python _grep.py <root> <needle> [maxhits]

findstr /s proved unreliable in this shell, so reference counting is done here.
"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
needle = sys.argv[2].lower()
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 200
exts = ('.cs', '.csproj', '.ps1', '.py', '.md', '.txt', '.cmd', '.json')
hits = 0
for path in sorted(root.rglob('*')):
    if path.suffix.lower() not in exts or not path.is_file():
        continue
    if 'bin' in path.parts or 'obj' in path.parts:
        continue
    try:
        text = path.read_text(encoding='utf-8', errors='ignore').lower()
    except OSError:
        continue
    for n, line in enumerate(text.splitlines(), 1):
        if needle in line:
            print('%s:%d: %s' % (path, n, line.strip()[:150]))
            hits += 1
            if hits >= limit:
                print('... truncated at %d hits' % limit)
                raise SystemExit
print('TOTAL %d hits for %r' % (hits, needle))