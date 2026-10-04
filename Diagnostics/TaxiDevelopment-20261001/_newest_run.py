"""Search only the NEWEST prelaunch-* log directory for the deciding merge lines.

The launcher preserves each run into Diagnostics/TaxiDevelopment-20261001/prelaunch-*,
so the newest directory is the run that just happened. Printing the exact merge
lines (or their absence) is what decides whether the experiment happened at all.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
dirs = sorted((p for p in HERE.glob('prelaunch-*') if p.is_dir()),
              key=lambda p: (p.stat().st_mtime, p.name))
if not dirs:
    print('no prelaunch-* directories found')
    raise SystemExit(1)
if len(sys.argv) > 1:
    chosen = [d for d in dirs if sys.argv[1] in d.name]
else:
    chosen = dirs[-1:]
NEEDLES = ('merged taxi', 'areamerge', 'tpthontaxi', 'control ladder',
           'falling back', 'exception', 'taxi')

for d in chosen:
    print('=' * 70)
    print('DIR %s' % d.name)
    for f in sorted(d.rglob('*')):
        if not f.is_file() or f.suffix.lower() not in ('.log', '.txt'):
            continue
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        lines = [ln.rstrip() for ln in text.splitlines()
                 if any(n in ln.lower() for n in NEEDLES)]
        if lines:
            print('--- %s (%d lines)' % (f.name, len(lines)))
            for ln in lines[:40]:
                print('   %s' % ln.strip()[:220])
    print()