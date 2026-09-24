import importlib.util, os

spec = importlib.util.spec_from_file_location('tor', r'D:\SWTORClassic\swtoremu\Diagnostics\extract-tor-paths.py')
tor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tor)

paths = [
    '/art/fx/fxspec/0.fxspec',
    '/art/shaders/materials/speedtree_collision.mat',
    '/art/shaders/materials/handbma.mat',
    '/.tex',
    '/engine/staging/engine_staging_human_01.gr2',
    '/engine/staging/engine_staging_human_02.gr2',
    '/art/shaders/materials/07 - default.mat',
]

hashes = {}
for p in paths:
    for cand in (p, '/resources' + p):
        hashes[tor.tor_hash(cand)] = p

archives = [
    r'D:\SWTORClassic\swtoremu\nexusclient\nexusclient\main_gfx_1.tor',
    r'D:\SWTORClassic\swtoremu\nexusclient\nexusclient\main_gfx_1.release83.tor',
]

found = {}
for arc in archives:
    if not os.path.exists(arc):
        print('=== %s MISSING' % os.path.basename(arc))
        continue
    f = open(arc, 'rb')
    seen_this = {}
    for e in tor.archive_entries(f):
        if not e[0]:
            continue
        if e[4] in hashes:
            p = hashes[e[4]]
            found.setdefault(p, []).append(os.path.basename(arc))
            seen_this.setdefault(p, e[3])
    print('=== %s entries=%d' % (os.path.basename(arc), sum(1 for _ in tor.archive_entries(open(arc, 'rb')))))
    f.close()

for p in paths:
    print(('FOUND ' if p in found else 'missing ') + p, found.get(p, '-'))
