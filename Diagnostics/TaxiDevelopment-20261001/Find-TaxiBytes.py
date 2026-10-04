"""Search local captures/content for taxi template and terminal component bytes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
patterns = {
    'taxi_template E0008B8CC0FAEA1D': bytes([0xCF, 0xE0, 0x00, 0x8B, 0x8C, 0xC0, 0xFA, 0xEA, 0x1D]),
    'taxTerminalComponent 40000003DE992C08': bytes([0xCF, 0x40, 0x00, 0x00, 0x03, 0xDE, 0x99, 0x2C, 0x08]),
    'taxTerminalSpec 40000003DE992C09': bytes([0xCF, 0x40, 0x00, 0x00, 0x03, 0xDE, 0x99, 0x2C, 0x09]),
}
roots = [
    ROOT/'SharpServer/bin/Debug/AreaServer',
    ROOT/'Diagnostics',
    ROOT/'SharpServer/AreaServer',
]
exts = {'.acrt', '.aaw', '.bin', '.crt', '.dat'}
seen = set()
for root in roots:
    if not root.exists():
        continue
    for path in root.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            data = path.read_bytes()
        except OSError:
            continue
        for label, pat in patterns.items():
            start = 0
            hits = []
            while True:
                i = data.find(pat, start)
                if i < 0:
                    break
                hits.append(i)
                start = i + 1
            if hits:
                print(f"{label}: {path.relative_to(ROOT)} offsets={hits[:12]}")
print("done")
