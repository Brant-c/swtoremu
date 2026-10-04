"""Why did the taxi run answer every RepositoryDataRequest with FQN NOT FOUND?

Run:  python Diagnostics/TaxiDevelopment-20261001/Probe-RepositoryHash.py
Writes: probe-repository.txt

Established so far:
  * TorArchive indexes 378505 hashes from 91 archives, no errors -> archives readable.
  * The C# Hash() and extract-tor-paths.tor_hash() share seed 0xDEADBEEF and the
    same `while i + 12 < len` loop bound, so the hashes should agree.
  * A one-off scan found /art/dynamic/spec/bmanew_skeleton.gr2 inside
    swtor_main_art_dynamic_mags_1.tor, yet the full audit resolved 0/100
    client-requested paths. Those two results contradict each other, so one of
    them is wrong. This probe isolates which.
"""
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'tp', ROOT / 'Diagnostics/extract-tor-paths.py')
tor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tor)

LOG = ROOT / 'Diagnostics/last-server-full.log'
ARCHIVES = ROOT / 'Assets2012April'
OUT = Path(__file__).resolve().parent / 'probe-repository.txt'
lines = []


def say(text=''):
    print(text)
    lines.append(text)


log = LOG.read_text(errors='replace')
paths = sorted({p for _, p in re.findall(r"request=(\d+), path='([^']+)'", log)})
say('distinct requested paths: %d' % len(paths))
say('  /art/dynamic/spec/ requests: %d'
    % len([p for p in paths if '/art/dynamic/spec/' in p]))
for p in paths:
    if '/art/dynamic/spec/' in p:
        say('    %s' % p)

# Two known-good references.
probe = '/art/dynamic/spec/bmanew_skeleton.gr2'
mags = ARCHIVES / 'swtor_main_art_dynamic_mags_1.tor'
h = tor.tor_hash(probe)
say('')
say('reference probe: %s' % probe)
say('  tor_hash      = 0x%016X' % h)
say('  archive       = %s (%d MB)' % (mags.name, mags.stat().st_size // (1024 * 1024)))

say('')
say('scanning %s ...' % mags.name)
hits = 0
with mags.open('rb') as f:
    for e in tor.archive_entries(f):
        if e[4] == h:
            hits += 1
            if hits <= 3:
                say('  MATCH entry=%r' % (e,))
say('  entries whose hash equals the probe: %d' % hits)

say('')
say('Interpretation:')
if hits:
    say('  The hash DOES occur in the archives, so both tor_hash() and the archive')
    say('  parser are correct. A full audit returning 0/100 is therefore wrong,')
    say('  most likely because archive_entries() yielded nothing for some archives,')
    say('  or the audit compared entry[4] against a differently-shaped tuple.')
else:
    say('  The hash does NOT occur, so the earlier "FOUND" was a false positive and')
    say('  /art/dynamic/spec/ content is genuinely not present in the local archives.')

OUT.write_text('\n'.join(lines), encoding='utf-8')
print('\nwrote %s' % OUT)