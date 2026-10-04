"""Audit every client-requested repository path against the local .tor archives.

Run:  python Diagnostics/TaxiDevelopment-20261001/Audit-RequestedSpecAssets.py
Writes: Diagnostics/TaxiDevelopment-20261001/spec-asset-audit.txt

Context: the taxi run answered all 104 RepositoryDataRequest packets with
"FQN NOT FOUND" (Diagnostics/last-server-full.log). TorArchive indexes 378505
hashes from 91 archives, so the archives are readable. This checks whether the
specifically requested paths exist under the exact path form the client sends
and under the "/resources" prefix the server also tries.
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'tp', ROOT / 'Diagnostics/extract-tor-paths.py')
tor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tor)

LOG = ROOT / 'Diagnostics/last-server-full.log'
ARCHIVES = ROOT / 'Assets2012April'
OUT = Path(__file__).resolve().parent / 'spec-asset-audit.txt'

text = LOG.read_text(errors='replace')
paths = sorted({p for _, p in re.findall(r"request=(\d+), path='([^']+)'", text)})

wanted = {}
for p in paths:
    wanted[tor.tor_hash(p)] = (p, 'plain')
    wanted[tor.tor_hash('/resources' + p)] = (p, '/resources')

found = {}
archives = sorted(ARCHIVES.glob('*.tor'))
print('scanning %d archives for %d distinct requested paths' % (len(archives), len(paths)))
for n, arc in enumerate(archives, 1):
    try:
        with arc.open('rb') as f:
            for e in tor.archive_entries(f):
                if e[0] and e[4] in wanted:
                    path, how = wanted[e[4]]
                    found.setdefault(path, []).append((arc.name, e[3], how))
    except Exception as exc:  # a bad archive must not abort the audit
        print('  WARN %s: %s' % (arc.name, exc))
    if n % 10 == 0:
        print('  %d/%d archives, %d paths resolved' % (n, len(archives), len(found)))
        sys.stdout.flush()

lines = ['requested paths : %d' % len(paths),
         'resolved locally: %d' % len(found),
         '',
         '%-8s %-58s %s' % ('STATUS', 'PATH', 'ARCHIVE')]
lines.append('-' * 110)
for p in paths:
    hits = found.get(p)
    if hits:
        lines.append('%-8s %-58s %s (%d bytes, via %s)'
                     % ('FOUND', p, hits[0][0], hits[0][1], hits[0][2]))
    else:
        lines.append('%-8s %s' % ('MISSING', p))

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('\nresolved %d/%d; wrote %s' % (len(found), len(paths), OUT))
specs = [p for p in paths if '/art/dynamic/spec/' in p]
print('of those, /art/dynamic/spec/ requests: %d, resolved: %d'
      % (len(specs), len([p for p in specs if p in found])))