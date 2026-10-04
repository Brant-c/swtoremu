"""Check the LIVE (not preserved) logs of the run that just happened.

Preserve-CurrentLogs.ps1 runs BEFORE launching, so a prelaunch-* directory holds
the PREVIOUS run's logs. The live files in Diagnostics/TaxiDevelopment-20261001/
and SharpServer/bin/Debug/ are the ones that describe the current run.

Checks for the six taxi script-error signatures, which are the client's own
report that it processed our record at all.
"""
import datetime
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'Diagnostics/TaxiDevelopment-20261001'
LIVE = HERE / 'launcher-console.log'
HOOK = HERE / 'nexus_hook.log'
SERVER = ROOT / 'SharpServer/bin/Debug/NexusToR.log'

SIGNATURES = (
    'Char spec missing',
    'not a MAG node',
    'Mag node',
    'valid animation agent',
    'Unknown spec',
    'hero scripterror',
)


def stamp(p):
    return datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime('%H:%M:%S')


for path in (LIVE, HOOK, SERVER):
    if not path.exists():
        print('%-46s MISSING' % path.name)
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    print('%-46s %9d bytes  mtime %s' % (
        path.name, path.stat().st_size, stamp(path)))
    total = 0
    for sig in SIGNATURES:
        n = len(re.findall(re.escape(sig), text, re.I))
        if n:
            print('    %-28s %d' % (sig, n))
            total += n
    if not total:
        print('    (no taxi script-error signatures)')
    if path is SERVER:
        for ln in text.splitlines():
            if 'merged taxi' in ln.lower() or 'tythontaxi' in ln.lower():
                print('    > %s' % ln.strip()[:210])
    print()