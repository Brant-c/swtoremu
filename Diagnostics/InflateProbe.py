import importlib.util, zlib

spec = importlib.util.spec_from_file_location('tor', r'D:\SWTORClassic\swtoremu\Diagnostics\extract-tor-paths.py')
tor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tor)

names = ['swtor_main_art_fx_1', 'swtor_main_art_dynamic_mags_1', 'swtor_main_bnk_audiodata_1']
for fname in names:
    p = r'D:\SWTORClassic\swtoremu\Assets2012April' + '\\' + fname + '.tor'
    f = open(p, 'rb')
    found = ok = fail = 0
    for e in tor.archive_entries(f):
        if not (e[0] and e[6] == 1):
            continue
        found += 1
        f.seek(e[0] + e[1])
        payload = f.read(e[2])
        try:
            d = zlib.decompress(payload)
            ok += 1
        except Exception:
            fail += 1
        if found <= 3:
            print('%s off=%d hdr=%d c=%d u=%d first=%s inflate_ok=%s' % (
                fname, e[0], e[1], e[2], e[3], payload[:2].hex(), 'OK' if ok == found else 'FAIL'))
    print('%s: zlib entries=%d ok=%d fail=%d' % (fname, found, ok, fail))
    f.close()
