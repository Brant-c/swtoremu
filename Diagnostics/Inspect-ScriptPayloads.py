from pathlib import Path
import struct, json
out=Path('Diagnostics/DecodedScripts2012'); out.mkdir(exist_ok=True)
matches=[]; count=0
for path in Path('Diagnostics/Scripts2012').glob('*.scpt'):
    b=path.read_bytes()
    if b[:8] != b'SCPT\x05\x00\x05\x00': continue
    size=struct.unpack_from('<I',b,33)[0]
    data=b[37:37+size]
    if b[24]: data=bytes(v^((0x35+i*0x36)&255) for i,v in enumerate(data))
    (out/(path.stem+'.bin')).write_bytes(data)
    count+=1
    if b'LS_OnAreaLoaded' in data or 'LS_OnAreaLoaded'.encode('utf-16le') in data or b'LS_ONAREALOADED' in data:
        matches.append(path.stem)
print(json.dumps({'decoded':count,'area_loaded_matches':matches}))
