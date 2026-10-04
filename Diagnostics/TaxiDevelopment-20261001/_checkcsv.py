"""Validate Protocol-Evidence.csv: every row must have the header's field count."""
import csv
import sys
from pathlib import Path

path = Path(sys.argv[1])
rows = list(csv.reader(path.open(encoding='utf-8')))
width = len(rows[0])
bad = [(i, len(r)) for i, r in enumerate(rows) if len(r) != width and r]
print('rows      :', len(rows))
print('field count:', width)
print('malformed  :', bad if bad else 'none')
sys.exit(1 if bad else 0)