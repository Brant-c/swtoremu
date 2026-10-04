"""Print exact leading whitespace for a line range (repr), to settle indentation."""
import sys
from pathlib import Path

path = Path(sys.argv[1])
start = int(sys.argv[2])
count = int(sys.argv[3])
raw = path.read_bytes().decode('utf-8')
eol = '\r\n' if '\r\n' in raw else '\n'
lines = raw.split(eol)
print('line endings: %s' % ('CRLF' if eol == '\r\n' else 'LF'))
for i in range(start - 1, min(start - 1 + count, len(lines))):
    print('%4d indent=%-3d %r' % (
        i + 1, len(lines[i]) - len(lines[i].lstrip(' ')), lines[i][:90]))