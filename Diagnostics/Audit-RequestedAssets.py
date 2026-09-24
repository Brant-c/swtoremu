from pathlib import Path
import re, importlib.util, json
root=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tor',root/'extract-tor-paths.py')
tor=importlib.util.module_from_spec(spec);spec.loader.exec_module(tor)
raw=(root/'last-compatibility-run.log').read_bytes()
text=raw.decode('utf-16') if raw.startswith(b'\xff\xfe') else raw.decode('utf-8',errors='replace')
paths=set(re.findall(r'path=(/[^\s]+)',text))
paths.update(['/art/defaultassets/white.tex','/engine/white.tex','/art/dynamic/spec/petmouse.dat','/art/dynamic/spec/petmouse.dyc','/anim/pet/am_pet.xml'])
wanted={}
for path in paths:
    for candidate in [path,'/resources'+path]:
        wanted[tor.tor_hash(candidate)]=(path,candidate)
found={}
for archive in sorted((root.parent/'Assets2012April').glob('*.tor')):
    with archive.open('rb') as f:
        for entry in tor.archive_entries(f):
            if entry[0] and entry[4] in wanted:
                path,candidate=wanted[entry[4]]
                found.setdefault(path,[]).append(dict(archive=archive.name,path=candidate,size=entry[3]))
report={path:found.get(path,[]) for path in sorted(paths)}
(root/'requested-asset-audit.json').write_text(json.dumps(report,indent=2))
print(f'{len(found)}/{len(paths)} requested paths found in currently installed archives')
for path in sorted(paths):
    if path in found: print('FOUND',path,found[path][0]['archive'],found[path][0]['path'])
    else: print('MISSING',path)
