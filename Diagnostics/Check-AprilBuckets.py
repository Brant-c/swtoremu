from pathlib import Path
import importlib.util
here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tor', here / 'extract-tor-paths.py')
tor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tor)
data = (here / 'GomCompatibility/ResourceCacheApril2012/systemgenerated/buckets.info').read_bytes()
assert data[:4] == b'PBCK' and data[8] == 0xc9
count = int.from_bytes(data[9:11], 'big')
offset = 11
names = []
for _ in range(count):
    length = data[offset]
    names.append(data[offset+1:offset+1+length].decode('ascii'))
    offset += 1 + length
print('List:', count, 'first:', names[0], 'last:', names[-1], 'trailing bytes:', len(data)-offset)
entries = tor.read_archive(here.parent / 'Assets2012April/swtor_main_global_1.tor')
found = [i for i in range(1000) if tor.tor_hash(f'/resources/systemgenerated/buckets/{i}.bkt') in entries]
print('Archive buckets among 0..999:',len(found),'range:',min(found),max(found))
print('Missing declared buckets:', [n for n in names if tor.tor_hash('/resources/systemgenerated/buckets/'+n) not in entries])
print('PINF contains _masterLayer:', b'_masterLayer' in entries[tor.tor_hash('/resources/systemgenerated/prototypes.info')])
