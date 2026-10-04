"""Print a numbered slice of a text file (diagnostic helper)."""
import sys
from pathlib import Path

path = Path(sys.argv[1])
start = int(sys.argv[2])
count = int(sys.argv[3])
lines = path.read_text(encoding='utf-8').splitlines()
out = []
for i in range(start - 1, min(start - 1 + count, len(lines))):
    out.append(str(i + 1).rjust(4) + '  ' + lines[i])
target = Path(__file__).resolve().parent / ('_slice_%d.txt' % start)
target.write_text('\n'.join(out), encoding='utf-8')
print('wrote %s (%d lines)' % (target, len(out)))