"""Extract verified April archives into a separate native compatibility cache."""
from pathlib import Path
import importlib.util
import json
import hashlib

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("tor_paths", here / "extract-tor-paths.py")
tor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tor)
cache = here / "GomCompatibility" / "ResourceCacheApril2012"
names = ["client.gom", "buckets.info", "prototypes.info", "scriptdef.list"]
paths = ["/resources/systemgenerated/" + name for name in names]
paths += [f"/resources/systemgenerated/buckets/{i}.bkt" for i in range(1000)]
wanted = {tor.tor_hash(path): path.removeprefix("/resources/") for path in paths}
report = []
for archive in sorted((here.parent / "Assets2012April").glob("*.tor")):
    entries = tor.read_archive(archive)
    selected = 0
    for key, payload in entries.items():
        name = wanted.get(key)
        if name is None and payload.startswith(b"SCPT"):
            name = f"scripts/{key:016X}.scpt"
        if name is None:
            continue
        target = cache / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        report.append(dict(path=name, archive=archive.name, size=len(payload), sha256=hashlib.sha256(payload).hexdigest()))
        selected += 1
    print(f"{archive.name}: extracted {selected} resources", flush=True)
for name in names:
    path = cache / "systemgenerated" / name
    if not path.exists():
        raise RuntimeError(f"Missing required resource: {name}")
    print(name, path.stat().st_size, path.read_bytes()[:12].hex(), flush=True)
(cache / "extraction.json").write_text(json.dumps(report, indent=2))
