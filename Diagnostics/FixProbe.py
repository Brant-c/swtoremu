import io

p = r'D:\SWTORClassic\swtoremu\SharpServer\Base\TorArchive.cs'
s = open(p, encoding='utf-8').read()

bad = '''            UInt64 h = Hash(path);
                        List<Entry> list;
            if (!_index.TryGetValue(Hash(path), out list))
                _index.TryGetValue(Hash("/resources" + path), out list);
            if (list == null || list.Count == 0)
                return false;
            Entry e = list[0];'''

good = '''            UInt64 h = Hash(path);
            UInt64 hRes = Hash("/resources" + path);
            List<Entry> list;
            if (!_index.TryGetValue(h, out list))
                _index.TryGetValue(hRes, out list);
            if (list == null || list.Count == 0)
                return String.Format("hash={0:X16} /resources={1:X16} NOT-INDEXED", h, hRes);
            Entry e = list[0];'''

assert bad in s, 'bad block not found'
open(p, 'w', encoding='utf-8').write(s.replace(bad, good))
print('Probe fixed')
