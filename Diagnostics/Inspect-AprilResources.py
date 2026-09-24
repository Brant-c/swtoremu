from pathlib import Path
from collections import Counter
import importlib.util
here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tor', here / 'extract-tor-paths.py')
tor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tor)
for path in sorted((here.parent/'Assets2012April').glob('*.tor')):
    entries = tor.read_archive(path)
    print(path.name, len(entries), Counter(v[:4] for v in entries.values()).most_common(12), flush=True)
    if 'main_global' in path.name:
        for key, data in list((k,v) for k,v in entries.items() if v[:4] == b'PROT')[:3]:
            print('PROT SAMPLE',f'{key:016X}',len(data),data[:80].hex())
        print('PINF HEADER',entries[tor.tor_hash('/resources/systemgenerated/prototypes.info')][:80].hex())
    for key, data in entries.items():
        if b'_masterLayer' in data or '_masterLayer'.encode('utf-16le') in data:
            print('MASTER LAYER',f'{key:016X}',len(data),data[:16].hex(), flush=True)
            if len(data) < 20000:
                (here/'april-masterlayer-resource.txt').write_bytes(data)
