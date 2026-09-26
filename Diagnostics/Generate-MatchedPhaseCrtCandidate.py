#!/usr/bin/env python3
"""Generate an isolated, schema-matched CRT1/CRT3 diagnostic candidate.

This never edits AreaServer fixtures.  CRT1 retains its header and complete
transaction byte-for-byte while gaining three dependency-first structures.
CRT3 retains every byte except its compact structure reference, which changes
from the mismatched structure 1 to the proposed phsPlayerPhaseData structure.
"""
import argparse
import importlib.util
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


decoder = load("style7_decoder", "Decode-Style7Replication.py")
builder = load("style7_builder", "Build-Style7Schema.py")


def locate_crt3_structure(data):
    reader = decoder.Reader(data, 8)
    flags = reader.byte()
    if not flags & 1 or reader.packed() != 1:
        raise ValueError("CRT3 is not the expected one-object transaction")
    reader.packed()  # node
    object_flags = reader.byte()
    if object_flags & 0x80:
        reader.packed()
    if object_flags & 0x40:
        reader.packed()
    if object_flags & 0x20:
        reader.packed()
    if object_flags & 0x10:
        metadata_flags = reader.byte()
        if metadata_flags & 3:
            count = int.from_bytes(data[reader.pos:reader.pos + 4], "little")
            reader.pos += 4
            for _ in range(count):
                reader.packed()
    if not object_flags & 0x08:
        raise ValueError("CRT3 object has no value")
    transport, style = reader.byte(), reader.byte()
    reader.packed()  # outer size
    if (transport, style) != (5, 7):
        raise ValueError(f"unexpected CRT3 transport/style {(transport, style)}")
    offset = reader.pos
    old = reader.packed()
    if old != 1 or reader.pos != offset + 1:
        raise ValueError(f"expected one-byte structure 1, found {old}")
    return offset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    crt1_path = decoder.CRT_DIR / "tython_blockout-4611686019869492753-1.1.acrt"
    crt3_path = decoder.CRT_DIR / "tython_blockout-4611686019869492753-1.3.acrt"
    crt1 = crt1_path.read_bytes()
    crt3 = crt3_path.read_bytes()
    structures, consumed, _ = decoder.read_schema()
    proposed, assigned = builder.propose_phase_schema(
        builder.gom.DEFAULT_GOM, builder.gom.DEFAULT_NAMES, structures)
    phase_id = next(type_id for type_id in assigned
                    if builder.decoder.name_table().get(type_id) == "phsPlayerPhaseData")
    phase_structure = assigned[phase_id]
    if phase_structure >= 0xC0:
        raise ValueError("candidate structure number no longer fits one byte")

    encoded_schema = builder.encode_schema(proposed)
    original_schema_size = struct.unpack_from("<I", crt1, 4)[0]
    if original_schema_size != consumed - 8:
        raise ValueError(
            f"CRT1 header schema size {original_schema_size} does not match "
            f"decoded size {consumed - 8}")
    # Bytes 4..7 bound the client's schema sub-reader.  Growing the table
    # without updating this value makes the native reader stop at the end of
    # the original 104 structures, even though the appended bytes are present.
    candidate_header = bytearray(crt1[:8])
    struct.pack_into("<I", candidate_header, 4, len(encoded_schema))
    candidate1 = bytes(candidate_header) + encoded_schema + crt1[consumed:]
    structure_offset = locate_crt3_structure(crt3)
    candidate3 = bytearray(crt3)
    candidate3[structure_offset] = phase_structure
    differences = [i for i, (a, b) in enumerate(zip(crt3, candidate3)) if a != b]
    if differences != [structure_offset]:
        raise ValueError(f"unexpected CRT3 differences: {differences}")
    new_structures, new_consumed = builder.decode_schema_bytes(candidate1[8:])
    if len(new_structures) != 107:
        raise ValueError("candidate CRT1 did not decode 107 structures")
    if struct.unpack_from("<I", candidate1, 4)[0] != new_consumed:
        raise ValueError("candidate CRT1 header does not bound the full schema")
    if candidate1[new_consumed + 8:] != crt1[consumed:]:
        raise ValueError("candidate CRT1 transaction changed")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out1 = args.output_dir / crt1_path.name
    out3 = args.output_dir / crt3_path.name
    out1.write_bytes(candidate1)
    out3.write_bytes(candidate3)
    print(f"WROTE diagnostic CRT1: {out1} ({len(candidate1)} bytes)")
    print(f"CRT1 schema bound: {original_schema_size} -> {len(encoded_schema)} bytes")
    print(f"WROTE diagnostic CRT3: {out3} ({len(candidate3)} bytes)")
    print(f"CRT3 sole byte change: offset 0x{structure_offset:X}, 0x01 -> "
          f"0x{phase_structure:02X}")
    print("Production AreaServer fixtures were not modified.")


if __name__ == "__main__":
    main()
