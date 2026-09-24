from pathlib import Path
import struct
for name in ['swtor_main_global_1.tor','swtor_en-us_global_1.tor']:
 p=Path('AssetsConverted')/name
 with p.open('r+b') as f:
  f.seek(4);old=f.read(4);assert old==struct.pack('<I',6);f.seek(4);f.write(struct.pack('<I',5))
 print(name,'test format version 6 -> 5')
