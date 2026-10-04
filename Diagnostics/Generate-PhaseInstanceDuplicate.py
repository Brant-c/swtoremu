#!/usr/bin/env python3
"""Generate a duplicate phase-instance create on a fresh node ID.

Why this exists
---------------
The 2026-09-28 audit proved that no engine trigger of type INSTANCE_GATEWAY is
present in the replicated area-object stream, so
`phsPhasedInstance.OnReplicationNodeCreate` cannot match one in
`GetTriggersByType(4)`. Before investing in server-side trigger emission we need
to rule out one remaining confound: re-sending the *existing* instance create is
ignored by the engine (a create for a node that already exists does not re-fire
the create handler), so the earlier retry probe could not tell us whether the
client registry actually contains the doorway trigger.

This writes a separate replication transaction that creates a *second*
phsClassPhasedInstance node from the exact same captured template, with a new,
unused node ID. A fresh node guarantees `OnReplicationNodeCreate` runs again.

Outcome interpretation
----------------------
- A gateway attaches and entering the doorway produces a phase RPC or an
  on-screen phase message  -> the engine trigger exists client-side and only the
  create timing was wrong.
- Nothing at all happens     -> the INSTANCE_GATEWAY trigger must be replicated
  by the server; it does not exist client-side.

The duplicated record is byte-for-byte the captured one except for its packed
node ID. No existing fixture is modified and no phase-info child is duplicated,
so the player's own phase membership is untouched.

Corrected 2026-09-28 - the node ID is now proven free, not asserted
-----------------------------------------------------------------

The first version hard-coded 0x1AC688C980 as its "fresh" node ID. That ID is in
use, and it is in use in a way a record-level scan cannot see: it occurs twice
inside production CRT1's *value regions* (file offsets 0xB4B4 and 0xB5B2) as a
node reference, while never appearing as any record's own node or parent. The
transaction it produced was therefore an update to a live node, not a create, so
OnReplicationNodeCreate never re-ran - the second independent reason the 14:36
probe was inconclusive, on top of re-sending a node that already existed.

The fix is not a different magic number, it is a proof. A candidate is accepted
only after its exact packed byte sequence is searched for across every .acrt in
the production set and found zero times, including inside value regions. The
generator's own output file is excluded from that scan so re-running stays
idempotent. If no candidate survives, the generator refuses to write anything.

Regenerate with:

    python Diagnostics/Generate-PhaseInstanceDuplicate.py
"""

import argparse
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
CANDIDATE_DIR = HERE / "GeneratedPhaseCandidate"
PRODUCTION_CRT_DIR = HERE.parent / "SharpServer" / "bin" / "Debug" / "AreaServer" / "CRT"
CRT1_NAME = "tython_blockout-4611686019869492753-1.1.acrt"
FRAMING_NAME = "tython_blockout-4611686019869492753-1.11.acrt"
OUTPUT_NAME = "tython_blockout-4611686019869492753-1.18.acrt"

PHASE_INSTANCE_NODE = 0x0000001AC688C97E
PHASE_INSTANCE_TEMPLATE = 0xE000E8E230304F84  # phs.tyt_jedi_knight_masters_retreat
PHASE_INSTANCE_STRUCTURE = 3                  # phsClassPhasedInstance
PACKED_SOURCE_NODE = bytes.fromhex("CC 1A C6 88 C9 7E")

# Candidate duplicate node IDs in preference order, kept inside the captured
# node-ID band so the packed encoding stays the same width as the source node.
# These are only *candidates*: find_free_node_id() must prove one is unused
# before the generator will write anything.
DUPLICATE_NODE_CANDIDATES = (
    0x0000001AC688C981,
    0x0000001AC688C982,
    0x0000001AC688C9FF,
    0x0000001AC688CA00,
)

# Every directory whose .acrt files must not already reference a candidate.
DEFAULT_SCAN_DIRS = (PRODUCTION_CRT_DIR, CANDIDATE_DIR)


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


decoder = load("style7_decoder", "Decode-Style7Replication.py")
builder = load("style7_builder", "Build-Style7Schema.py")


def pack_unsigned(value):
    """Match the client's compact unsigned encoding: 0xC7 + byte count, then
    the value big-endian with no leading zero bytes."""
    if value < 0xC0:
        return bytes([value])
    width = (value.bit_length() + 7) // 8
    if width > 8:
        raise ValueError(f"value 0x{value:X} does not fit a compact unsigned")
    return bytes([0xC7 + width]) + value.to_bytes(width, "big")


def collect_scan_files(scan_dirs, exclude=()):
    """Every .acrt the proofs must consider, minus the generator's own output."""
    excluded = {Path(path).resolve() for path in exclude}
    files = []
    for directory in scan_dirs:
        directory = Path(directory)
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.acrt")):
            if path.resolve() not in excluded:
                files.append(path)
    if not files:
        raise ValueError("no .acrt files found to scan; nothing can be proven")
    return files


def find_free_stream_id(files):
    """Pick a stream id no fixture already uses.

    Stream ids are unique per transaction in the capture - 0x001B5012 for CRT1,
    stepping up one per CRT to 0x001B502D for CRT17. The first version of this
    probe reused CRT11's id (0x001B5023) for the new transaction, and CRT11 is
    delivered in the startup bundle, so the client could discard the resend as
    a duplicate stream before any new-node callback ran. That is a third
    independent reason the 14:30 probe could not have shown anything.
    """
    used = sorted(int.from_bytes(path.read_bytes()[:4], "little")
                  for path in files)
    candidate = used[-1] + 1
    while candidate in used:
        candidate += 1
    return candidate, used


def find_free_node_id(files):
    """Return the first candidate whose packed bytes appear nowhere on disk.

    A record-level scan for node/parent IDs is not sufficient. The ID that broke
    the first version of this generator is a live CRT1 object node, and it also
    occurs *inside* a value region as a parent reference, which a node/parent
    scan cannot see. So the search is over raw file bytes.
    """
    for candidate in DUPLICATE_NODE_CANDIDATES:
        packed = pack_unsigned(candidate)
        if len(packed) != len(PACKED_SOURCE_NODE):
            continue
        hits = []
        for path in files:
            raw = path.read_bytes()
            start = raw.find(packed)
            while start != -1:
                hits.append(f"{path.name}@0x{start:X}")
                start = raw.find(packed, start + 1)
        if not hits:
            print(f"free node ID 0x{candidate:016X} "
                  f"({len(files)} .acrt files scanned, zero references)")
            return candidate
        print(f"rejecting 0x{candidate:016X}: referenced by {', '.join(hits)}")

    raise ValueError(
        "no candidate node ID is unused; extend DUPLICATE_NODE_CANDIDATES")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crt1-dir", type=Path, default=CANDIDATE_DIR,
                        help="directory holding the schema-carrying -1.1.acrt; "
                             "falls back to the production set when absent")
    parser.add_argument("--framing-dir", type=Path, default=PRODUCTION_CRT_DIR,
                        help="directory holding a non-CRT1 fixture for framing")
    parser.add_argument("--output-dir", type=Path, default=CANDIDATE_DIR)
    parser.add_argument("--scan-dir", type=Path, action="append", default=None,
                        help="directory whose .acrt files must not already "
                             "reference the candidate node ID; repeatable")
    args = parser.parse_args()

    scan_dirs = args.scan_dir if args.scan_dir else list(DEFAULT_SCAN_DIRS)
    out = args.output_dir / OUTPUT_NAME
    files = collect_scan_files(scan_dirs, exclude=(out,))
    duplicate_node = find_free_node_id(files)
    stream_id, used_streams = find_free_stream_id(files)

    # The captured master-retreat instance lives in CRT1, not in the small
    # per-CRT fixtures: CRT1 is the transaction that carries all 53+ phase
    # instances, and its object list sits after the compact schema, so it needs
    # the schema-aware offset. The framing prefix comes from an ordinary
    # non-CRT1 fixture, because CRT1's own bytes 4..7 are the schema length.
    crt1_dir = args.crt1_dir
    if not (crt1_dir / CRT1_NAME).is_file():
        crt1_dir = PRODUCTION_CRT_DIR
    source = (crt1_dir / CRT1_NAME).read_bytes()
    framing = (args.framing_dir / FRAMING_NAME).read_bytes()
    if len(framing) < 10:
        raise ValueError(f"{FRAMING_NAME} is too short to supply .acrt framing")

    _, schema_length = builder.decode_schema_bytes(source[8:])
    reader = decoder.Reader(source, 8 + schema_length)
    flags = reader.byte()
    count = reader.packed() if flags & 0x01 else 0
    if count == 0:
        raise ValueError(f"{CRT1_NAME} declares no objects (flags 0x{flags:02X})")

    records = [decoder.read_object_record(source, reader) for _ in range(count)]
    if reader.pos != len(source):
        raise ValueError("CRT1 object walk did not reach the packet end")

    matches = [index for index, item in enumerate(records)
               if item["node"] == PHASE_INSTANCE_NODE
               and item.get("template_id") == PHASE_INSTANCE_TEMPLATE
               and item["structure_id"] == PHASE_INSTANCE_STRUCTURE]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one master-retreat instance in {CRT1_NAME}, "
            f"found {len(matches)}")
    index = matches[0]
    instance = records[index]
    record_end = (records[index + 1]["start"]
                  if index + 1 < len(records) else len(source))
    record = source[instance["start"]:record_end]
    if not record.startswith(PACKED_SOURCE_NODE):
        raise ValueError("instance record does not start with its packed node ID")
    if record.count(PACKED_SOURCE_NODE) != 1:
        raise ValueError(
            "packed source node ID occurs more than once in the record; "
            "a blind replacement would corrupt the value region")
    print(f"{CRT1_NAME}: object {index} of {count} at 0x{instance['start']:X}, "
          f"record {len(record)} bytes")

    packed_duplicate = pack_unsigned(duplicate_node)
    if len(packed_duplicate) != len(PACKED_SOURCE_NODE):
        raise ValueError("duplicate node ID encoding must be the same width")
    duplicate_record = packed_duplicate + record[len(PACKED_SOURCE_NODE):]

    # Reuse the source framing (stream ID, reserved word, object-list flag) and
    # emit exactly one record.
    output = (stream_id.to_bytes(4, "little") + framing[4:8] +
              bytes([0x01]) + pack_unsigned(1) + duplicate_record)

    # Re-parse the result so a malformed transaction can never reach the server.
    check = decoder.Reader(output, 8)
    if check.byte() != 1:
        raise ValueError("generated transaction lost its object-list flag")
    if check.packed() != 1:
        raise ValueError("generated transaction does not declare one record")
    generated = decoder.read_object_record(output, check)
    if check.pos != len(output):
        raise ValueError("generated record does not end at the packet end")
    if (generated["node"] != duplicate_node or
            generated["template_id"] != PHASE_INSTANCE_TEMPLATE or
            generated["structure_id"] != PHASE_INSTANCE_STRUCTURE):
        raise ValueError("generated duplicate does not match the captured instance")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out.write_bytes(output)

    # Last check, on the bytes actually written: the new node ID must not be
    # referenced by any other fixture, or the engine would treat this as an
    # update to a live node and OnReplicationNodeCreate would never re-run.
    others = files
    for path in others:
        if packed_duplicate in path.read_bytes():
            out.unlink()
            raise ValueError(
                f"{path.name} references 0x{duplicate_node:016X}; removed the "
                f"generated file rather than ship a duplicate-node update")

    print(f"WROTE duplicate instance transaction: {out} ({len(output)} bytes)")
    print(f"stream 0x{stream_id:08X} (next id after the capture's "
          f"0x{used_streams[0]:08X}..0x{used_streams[-1]:08X} range; framing "
          f"layout reused from {FRAMING_NAME})")
    print(f"node 0x{PHASE_INSTANCE_NODE:016X} -> 0x{duplicate_node:016X}")
    print(f"record {len(record)} bytes, changed only the "
          f"{len(packed_duplicate)}-byte packed node ID; template "
          f"0x{PHASE_INSTANCE_TEMPLATE:016X}, structure {PHASE_INSTANCE_STRUCTURE}")
    print(f"verified: 0x{duplicate_node:016X} is unreferenced by "
          f"{len(others)} other .acrt files, so this is a create, not an update")
    print("No existing fixture was modified.")


if __name__ == "__main__":
    main()
