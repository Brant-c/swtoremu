from pathlib import Path
import re, json, html

root = Path(__file__).resolve().parent
entries = []
for product, filename in [('d3-assets_swtor_main', 'jedipedia-main-release-48.html'),
                          ('d3-assets_swtor_en_us', 'jedipedia-en-us-release-48.html')]:
    page = html.unescape((root / filename).read_text(encoding='utf-8'))
    for row in page.split('<tr>'):
        name = re.search(r'file=(swtor_[\w-]+\.tor)', row)
        size = re.search(r'title="([\d,]+) bytes"', row)
        checksum = re.search(r'<span>([a-f0-9]{32})</span>', row)
        if name and size and checksum:
            entries.append(dict(product=product, release=48, name=name[1],
                                size=int(size[1].replace(',', '')), md5=checksum[1]))
print(f'{len(entries)} archives, {sum(x["size"] for x in entries)/1024**3:.2f} GiB')
for item in entries:
    print(item['name'], item['size'], item['md5'])
(root / 'april-asset-manifest.json').write_text(json.dumps(entries, indent=2))
