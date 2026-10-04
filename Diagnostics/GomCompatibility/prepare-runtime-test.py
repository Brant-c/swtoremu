"""Copy one retail archive and recompress only client.gom; never edit retail."""
import pathlib, struct, zlib, shutil, json
here = pathlib.Path(__file__).resolve().parent
source = pathlib.Path(r'C:\Program Files (x86)\Electronic Arts\BioWare\Star Wars - The Old Republic\Assets\swtor_main_global_1.tor')
target = here / 'RuntimeAssets'
target.mkdir(exist_ok=True)
dest = target / source.name
raw = (here / 'client.gom').read_bytes()
packed = zlib.compress(raw)
shutil.copyfile(source, dest)
with dest.open('r+b') as f:
    header = f.read(36)
    table = struct.unpack_from('<Q', header, 12)[0]
    found = False
    while table and not found:
        f.seek(table)
        count, table = struct.unpack('<IQ', f.read(12))
        for i in range(count):
            row = f.tell()
            entry = list(struct.unpack('<QIIIQIH', f.read(34)))
            if entry[4] != 0x6107069DB7C70D58:
                continue
            old = entry[:]
            f.seek(entry[0])
            metadata = f.read(entry[1])
            f.seek(0, 2)
            entry[0] = f.tell()
            entry[2] = len(packed)
            # Preserve the original checksum: its algorithm is not established.
            # The uncompressed bytes and per-entry metadata are unchanged.
            f.write(metadata + packed)
            f.seek(row)
            f.write(struct.pack('<QIIIQIH', *entry))
            f.seek(entry[0] + entry[1])
            assert zlib.decompress(f.read(entry[2])) == raw
            report = {'source': str(source), 'test_archive': str(dest), 'original_entry': old, 'test_entry': entry,
                      'note': 'Partial archive set. Only client.gom compression changed; runtime compatibility remains under test.'}
            (here / 'runtime-test.json').write_text(json.dumps(report, indent=2))
            found = True
            break
    assert found
print(dest)
