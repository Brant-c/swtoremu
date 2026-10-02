"""Extract placed-instance positions and calibrate against captured awareness.

The rendered instance dump stores coordinates as integers x100 with columns in a
fixed order. Comparing a known captured object (the exterior vendor, world
position -59.79,-6.90,-128.33) against its instance row pins the column order and
scale, so an authored taxi anchor can be read directly.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
text = (ROOT/'_JPEXTRACT/DAT/instances.txt').read_text(encoding='utf-8', errors='replace')

# Each row: asset id mark, then Asset name, then three coordinate marks.
rows = []
for chunk in text.split('</tr>'):
    marks = re.findall(r'<mark>(-?\d+),?</mark>', chunk)
    name = re.search(r'Asset name:\s*(.+?)"\s*><span', chunk)
    if not name or len(marks) < 4:
        continue
    fqn = name.group(1).replace('\\', '/').replace('/', '.')
    rows.append((fqn, [int(v) for v in marks[-3:]]))

print(f"rows parsed: {len(rows)}")

VENDOR = 16141002980083430189
wanted = [r for r in rows if any(
    k in r[0] for k in ('taxi', 'jediretreat', 'masters_retreat'))]
print(f"\n-- taxi/retreat placement rows ({len(wanted)}) --")
for fqn, coords in wanted:
    print(f"  {coords}  {fqn[:110]}")

# Calibration: find rows whose coords look like the captured cluster.
print("\n-- rows whose coords scale to the captured awareness cluster --")
near = [r for r in rows if any(abs(c) in range(5800, 6100) for c in r[1][:1])]
for fqn, coords in near[:25]:
    print(f"  {coords}  {fqn[:110]}")