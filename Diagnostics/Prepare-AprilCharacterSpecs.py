from pathlib import Path
import importlib.util,re
here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tor',here/'extract-tor-paths.py')
tor=importlib.util.module_from_spec(spec);spec.loader.exec_module(tor)
entries=tor.read_archive(here.parent/'Assets2012April/swtor_main_anim_misc_1.tor')
raw=(here/'last-compatibility-run.log').read_bytes()
log=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8',errors='replace')
paths=sorted(set(re.findall(r'Character-spec resource path: (\S+)',log)))
if not paths:raise RuntimeError('No captured character-spec paths in current log')
missing=[]
for path in paths:
    data=entries.get(tor.tor_hash('/resources'+path))
    if data is None:missing.append(path);continue
    target=here/'GomCompatibility/ResourceCacheApril2012'/path.lstrip('/')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
print('Requested',len(paths),'extracted',len(paths)-len(missing),'missing',missing)
print('Sample',repr((here/'GomCompatibility/ResourceCacheApril2012/art/dynamic/spec/petmouse.dat').read_bytes()[:400]))
if missing:raise RuntimeError('Missing required character specs')
