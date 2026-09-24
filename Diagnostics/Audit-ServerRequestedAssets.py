# Audit repository paths requested by the CLIENT (from the server log)
# against the locally installed .tor archives. Mirrors Audit-RequestedAssets.py
# but reads SharpServer/bin/Debug/NexusToR.log, whose RepositoryDataRequest
# lines record every asset the client asked the server to serve.
from pathlib import Path
import re, importlib.util, json

root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tor', root / 'extract-tor-paths.py')
tor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tor)

LOG = root.parent / 'SharpServer' / 'bin' / 'Debug' / 'NexusToR.log'
text = LOG.read_text(errors='replace')
pairs = re.findall(r"request=(\d+), path='([^']+)'", text)
paths = sorted({p for _, p in pairs})
print('requests=%d distinct-paths=%d' % (len(pairs), len(paths)))

wanted = {}
for path in paths:
    for candidate in [path, '/resources' + path]:
        wanted[tor.tor_hash(candidate)] = (path, candidate)

found = {}
for archive in sorted((root.parent / 'Assets2012April').glob('*.tor')):
    with archive.open('rb') as f:
        for entry in tor.archive_entries(f):
            if entry[0] and entry[4] in wanted:
                path, candidate = wanted[entry[4]]
                found.setdefault(path, []).append(
                    dict(archive=archive.name, path=candidate, size=entry[3]))

out = {p: found.get(p, []) for p in paths}
(root / 'server-requested-asset-audit.json').write_text(json.dumps(out, indent=2))
print('served-from-archives: %d/%d' % (len(found), len(paths)))
for p in paths:
    if p in found:
        print('FOUND  ', p, '->', found[p][0]['archive'])
missing = [p for p in paths if p not in found]
print('missing: %d (showing up to 20)' % len(missing))
for p in missing[:20]:
    print('MISSING', p)
