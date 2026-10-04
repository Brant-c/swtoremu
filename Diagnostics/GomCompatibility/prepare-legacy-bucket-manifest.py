"""Limit the modern bucket manifest to the 500 buckets used by the 2012 client tools."""
import hashlib
import json
import pathlib

here = pathlib.Path(__file__).resolve().parent
target = here / "ResourceCache" / "systemgenerated" / "buckets.info"
original = target.with_name("buckets-modern.info")
raw = original.read_bytes() if original.exists() else target.read_bytes()
if raw[:8] != b"PBCK\x01\x00\x05\x00" or raw[8] != 0xC9:
    raise ValueError("Unexpected buckets.info header")
modern_count = int.from_bytes(raw[9:11], "big")
if modern_count < 500:
    raise ValueError(f"Modern manifest has only {modern_count} buckets")

if not original.exists():
    original.write_bytes(raw)
names = [f"{index}.bkt".encode("ascii") for index in range(500)]
legacy = bytearray(raw[:8])
legacy.append(0xC9)
legacy.extend((500).to_bytes(2, "big"))
for name in names:
    if len(name) >= 0xC0:
        raise ValueError("Unexpected long bucket filename")
    legacy.append(len(name))
    legacy.extend(name)
if len(legacy) > len(raw):
    raise ValueError("Compatibility manifest unexpectedly exceeds source size")
legacy.extend(b"\0" * (len(raw) - len(legacy)))
target.write_bytes(legacy)

report = {
    "source_bucket_count": modern_count,
    "compatibility_bucket_count": 500,
    "source_sha256": hashlib.sha256(raw).hexdigest(),
    "compatibility_sha256": hashlib.sha256(legacy).hexdigest(),
    "compatibility_size": len(legacy),
}
(here / "bucket-manifest.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
