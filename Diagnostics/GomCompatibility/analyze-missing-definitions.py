"""Classify DefinitionNotFoundException names seen while loading modern buckets."""
import collections
import json
import pathlib
import re
import struct

HERE = pathlib.Path(__file__).resolve().parent


def records(dblb, source):
    if dblb[:4] != b"DBLB" or struct.unpack_from("<I", dblb, 4)[0] not in (1, 2):
        raise ValueError(f"Bad DBLB header in {source}")
    pos = 8
    while pos + 4 <= len(dblb):
        length = struct.unpack_from("<I", dblb, pos)[0]
        if length == 0:
            break
        if length < 24 or pos + length > len(dblb):
            raise ValueError(f"Bad record length {length} at {source}+{pos}")
        record = dblb[pos:pos + length]
        ident = struct.unpack_from("<Q", record, 8)[0]
        kind = (struct.unpack_from("<H", record, 16)[0] >> 3) & 15
        nameoff = struct.unpack_from("<H", record, 20)[0]
        name = ""
        if 0 < nameoff < len(record):
            name = record[nameoff:].split(b"\0", 1)[0].decode("ascii", errors="replace")
        yield ident, kind, name, pos, record
        pos = (pos + length + 7) & ~7


def bucket_streams(path):
    raw = path.read_bytes()
    if raw[:4] != b"PBUK":
        raise ValueError(f"Bad PBUK header in {path}")
    pos = 8
    for frame in range(2):
        size = struct.unpack_from("<I", raw, pos)[0]
        pos += 4
        yield frame, raw[pos:pos + size]
        pos += size


trace = (HERE / "trace-resource-bridge-names-utf16.txt").read_text(errors="replace")
observed = re.findall(r"^MISSING DEFINITION name=([^ ]+)", trace, re.MULTILINE)
counts = collections.Counter(observed)
numeric = {int(value) for value in counts if value.isdecimal()}

definitions = {}
named_definitions = collections.defaultdict(list)
core = (HERE / "client-field-isolation.gom").read_bytes()
for ident, kind, name, pos, record in records(core, "client-field-isolation.gom"):
    definitions.setdefault(ident, []).append({"source": "client.gom", "kind": kind, "name": name, "offset": pos})
    if name:
        named_definitions[name].append({"id": str(ident), "source": "client.gom", "kind": kind})

bucket_dir = HERE / "ResourceCache" / "systemgenerated" / "buckets"
bucket_record_count = 0
for path in sorted(bucket_dir.glob("*.bkt"), key=lambda p: int(p.stem)):
    for frame, data in bucket_streams(path):
        for ident, kind, name, pos, record in records(data, f"{path.name} frame {frame}"):
            bucket_record_count += 1
            if name in counts:
                named_definitions[name].append({"id": str(ident), "source": path.name, "frame": frame, "kind": kind})
            if ident in numeric:
                definitions.setdefault(ident, []).append({
                    "source": path.name, "frame": frame, "kind": kind,
                    "name": name, "offset": pos,
                })

xml = (HERE.parents[1] / "Tools" / "tor_tools" / "gom_type_names.xml").read_text(errors="replace")
xml_hits = {}
for ident in numeric:
    match = re.search(rf"<[^>]+id=[\"']{ident}[\"'][^>]*", xml, re.IGNORECASE)
    if match:
        xml_hits[str(ident)] = match.group(0)

rows = []
for value, count in counts.most_common():
    row = {"name": value, "count": count, "numeric": value.isdecimal()}
    if value.isdecimal():
        row["definitions"] = definitions.get(int(value), [])
        if value in xml_hits:
            row["xml"] = xml_hits[value]
    elif value in named_definitions:
        row["definitions"] = named_definitions[value]
    rows.append(row)

report = {
    "exception_count": sum(counts.values()),
    "unique_name_count": len(counts),
    "numeric_unique_count": len(numeric),
    "bucket_record_count": bucket_record_count,
    "numeric_ids_defined_in_loaded_data": sum(bool(definitions.get(i)) for i in numeric),
    "numeric_ids_in_name_xml": len(xml_hits),
    "rows": rows,
}
(HERE / "missing-definition-analysis.json").write_text(json.dumps(report, indent=2))
print(json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=2))
for row in rows[:20]:
    print(row)
