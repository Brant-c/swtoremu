from pathlib import Path
import importlib.util
here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tor',here/'extract-tor-paths.py')
tor=importlib.util.module_from_spec(spec);spec.loader.exec_module(tor)
entries=tor.read_archive(here.parent/'Assets2012April/swtor_main_gamedata_1.tor')
cache=here/'GomCompatibility/ResourceCacheApril2012/guixml'
cache.mkdir(parents=True,exist_ok=True)
names=['guixml.lst','_heguixml.lst']
for name in names[:]:
    data=entries[tor.tor_hash('/resources/guixml/'+name)]
    names += [line.strip() for line in data.decode('utf-8-sig').splitlines() if line.strip()]
for name in dict.fromkeys(names):
    assert '/' not in name and '\\' not in name and '..' not in name
    data=entries[tor.tor_hash('/resources/guixml/'+name)]
    (cache/name.lower()).write_bytes(data)
    print(name,len(data))
