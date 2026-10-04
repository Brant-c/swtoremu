"""Read retail client.gom; write only a diagnostic copy beside this script."""
import pathlib, struct, sys, zlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'python-deps'))
import zstandard
archive = pathlib.Path(r'C:\Program Files (x86)\Electronic Arts\BioWare\Star Wars - The Old Republic\Assets\swtor_main_global_1.tor')
with archive.open('rb') as f:
    header = f.read(36)
    table = struct.unpack_from('<Q', header, 12)[0]
    while table:
        f.seek(table)
        count, table = struct.unpack('<IQ', f.read(12))
        entries = [struct.unpack('<QIIIQIH', f.read(34)) for _ in range(count)]
        for offset, meta, packed, size, name, crc, method in entries:
            if name != 0x6107069DB7C70D58:
                continue
            f.seek(offset + meta)
            data = f.read(packed)
            raw = (zstandard.ZstdDecompressor().decompress(data, max_output_size=size)
                   if data.startswith(bytes.fromhex('28b52ffd')) else
                   zlib.decompress(data) if method == 1 else data)
            assert len(raw) == size
            output = pathlib.Path(__file__).with_name('client.gom')
            output.write_bytes(raw)
            print(f'Extracted {len(raw)} bytes to {output}')
            # One-resource test fixture only; retain the source archive version.
            # Use no per-entry metadata and no compression to isolate lookup.
            test_header = bytearray(header)
            struct.pack_into('<Q', test_header, 12, 512)
            struct.pack_into('<I', test_header, 20, 1)
            struct.pack_into('<I', test_header, 24, 1)
            fixture = bytearray(1024)
            fixture[:36] = test_header
            struct.pack_into('<IQ', fixture, 512, 1, 0)
            struct.pack_into('<QIIIQIH', fixture, 524, 1024, 0, len(raw), len(raw), name, zlib.adler32(raw), 0)
            fixture.extend(raw)
            fixture_path = output.with_name('client-gom-fixture.tor')
            fixture_path.write_bytes(fixture)
            print(f'Wrote isolated archive-reader fixture: {fixture_path}')
            sys.exit(0)
raise RuntimeError('client.gom hash not found')
