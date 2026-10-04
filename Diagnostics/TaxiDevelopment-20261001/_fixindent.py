"""Fix the stray indent before the `values = {` dict in Generate-Taxi.py."""
import sys
from pathlib import Path

path = Path(__file__).resolve().parent / 'Generate-Taxi.py'
lines = path.read_bytes().decode('utf-8').split('\n')
NUM = 91
if not lines[NUM - 1].startswith('  values = {'):
    print('ABORT: line %d is %r' % (NUM, lines[NUM - 1]))
    sys.exit(1)
lines[NUM - 1] = lines[NUM - 1].lstrip(' ')
# The continuation lines are over-indented relative to the new head; normalise.
for i in range(NUM, NUM + 6):
    if i - 1 < len(lines) and lines[i - 1].startswith('            '):
        lines[i - 1] = '    ' + lines[i - 1].strip()
path.write_bytes('\n'.join(lines).encode('utf-8'))
print('fixed indentation at line %d and its 5 continuations' % NUM)