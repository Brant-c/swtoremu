from pathlib import Path
import importlib.util,re
from collections import Counter
here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tor',here/'extract-tor-paths.py')
tor=importlib.util.module_from_spec(spec);spec.loader.exec_module(tor)
for name in ['gamedata','art_creature_a','art_misc','art_zed','zed']:
    archive=here.parent/f'Assets2012April/swtor_main_{name}_1.tor'
    entries=tor.read_archive(archive)
    tags=Counter()
    for key,data in entries.items():
        if data[:2]==b'\xff\xfe': text=data[:2000].decode('utf-16',errors='replace')
        else:text=data[:2000].decode('utf-8-sig',errors='replace')
        match=re.search(r'<([a-zA-Z][a-zA-Z_0-9]*)',text)
        if match:tags[match[1]]+=1
        if 'petmouse' in text.lower():print(name,f'{key:016X}',repr(text[:350]))
    print(name,tags.most_common(20),Counter(v[:4] for v in entries.values()).most_common(5),flush=True)
