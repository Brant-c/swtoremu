from pathlib import Path
import re, html, hashlib, json
from urllib.parse import unquote
root=Path(__file__).resolve().parent
page=html.unescape((root/'jedipedia-client-release-37.html').read_text(encoding='utf-8'))
items=[]
for row in page.split('<tr>'):
    name=re.search(r'file=([^&\s\x27]+)',row)
    checksum=re.search(r'<span>([a-f0-9]{32})</span>',row)
    size=re.search(r'title="([\d,]+) bytes"',row)
    if not (name and checksum and size): continue
    name=unquote(name[1].rstrip('\\'))
    path=root.parent/'nexusclient'/'nexusclient'/name
    actual=hashlib.md5(path.read_bytes()).hexdigest() if path.exists() else None
    item=dict(name=name,md5=checksum[1],size=int(size[1].replace(',','')),actual=actual)
    items.append(item)
    print(name, 'MATCH' if actual==checksum[1] else 'DIFFERS' if actual else 'MISSING')
(root/'april-client-files-audit.json').write_text(json.dumps(items,indent=2))
