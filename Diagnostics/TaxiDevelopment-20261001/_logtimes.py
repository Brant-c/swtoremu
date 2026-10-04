"""Timestamp every preserved run log and every merge line, newest first.

Needed because a preserved NexusToR.log can be stale: the deciding merge line
must be shown to belong to the run that just happened, not an earlier one.
"""
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'Diagnostics/TaxiDevelopment-20261001'
MERGE = 'merged taxi'


def stamp(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


print('now:', stamp(datetime.datetime.now().timestamp()))
print()
dirs = sorted((p for p in HERE.glob('prelaunch-*') if p.is_dir()),
              key=lambda p: p.stat().st_mtime)
print('--- preserved run directories (newest 5) ---')
for d in dirs[-5:]:
    print('%s  dir-mtime=%s' % (d.name, stamp(d.stat().st_mtime)))
print()
print('--- files in the newest directory ---')
newest = dirs[-1]
for f in sorted(newest.rglob('*')):
    if f.is_file():
        print('%-28s %10d  %s' % (f.name, f.stat().st_size,
                                  stamp(f.stat().st_mtime)))
print()
print('--- live NexusToR.log ---')
live = ROOT / 'SharpServer/bin/Debug/NexusToR.log'
if live.exists():
    print('%-28s %10d  %s' % (live.name, live.stat().st_size,
                              stamp(live.stat().st_mtime)))
    text = live.read_text(encoding='utf-8', errors='ignore')
    hits = [ln for ln in text.splitlines() if MERGE in ln.lower()]
    print('merge lines in live log: %d' % len(hits))
    for ln in hits[-5:]:
        print('   %s' % ln.strip()[:200])
print()
print('--- every preserved log containing a merge line, newest first ---')
for d in reversed(dirs):
    for f in sorted(d.rglob('*.log')):
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        hits = [ln for ln in text.splitlines() if MERGE in ln.lower()]
        if hits:
            print('%s / %s  (mtime %s)  %d line(s)' % (
                d.name, f.name, stamp(f.stat().st_mtime), len(hits)))
            for ln in hits[-2:]:
                print('    %s' % ln.strip()[:200])