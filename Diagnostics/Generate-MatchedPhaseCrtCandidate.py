#!/usr/bin/env python3
"""Generate an isolated, schema-matched phase diagnostic candidate.

This never edits AreaServer fixtures.  CRT1 keeps its header, schema and
complete captured transaction, gains three dependency-first structures, and
gains the captured phsClassPhaseInfo record inserted directly after the phase
instance.  CRT3 retains every byte except its compact structure reference, which
changes from the mismatched structure 1 to the proposed phsPlayerPhaseData
structure.  CRT4 loses that phase-info record, and CRT11 uses the production
fixture unchanged.

Placement is the point of this arrangement.  CRT2 creates the local player
character, and chrCharacter.Replication_Create fires OnPlayerCharacterNodeReady
-> phsoracle.OnPhasedInstanceUpdated exactly once.  That method returns early
when the player has no phase-info child, so the child must already exist when
CRT2 is applied.  CRT1 is sent before CRT2, so the instance and its child now
both exist in time for the phase banner and for pc.GetPhasedInstance() to become
valid, which is the precondition for phsCanExit.
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


PHASE_INSTANCE_NODE = 0x0000001AC688C97E
PHASE_INSTANCE_TEMPLATE = 0xE000E8E230304F84  # phs.tyt_jedi_knight_masters_retreat
PHASE_INSTANCE_STRUCTURE = 3                  # phsClassPhasedInstance in CRT1
PHASE_INFO_NODE = 0x0000001AC6F6DC1F


def remove_phase_instance_from_crt1(crt1, schema_end):
    reader = decoder.Reader(crt1, schema_end)
    if reader.byte() != 1:
        raise ValueError("CRT1 trailing transaction does not have object-list flags")
    count_offset = reader.pos
    count = reader.packed()
    if count != 53 or reader.pos != count_offset + 1:
        raise ValueError(f"CRT1 expected one-byte object count 53, found {count}")
    records = [decoder.read_object_record(crt1, reader) for _ in range(count)]
    if reader.pos != len(crt1):
        raise ValueError("CRT1 trailing object walk did not reach packet end")
    matches = [(index, record) for index, record in enumerate(records)
               if record["node"] == PHASE_INSTANCE_NODE]
    if len(matches) != 1:
        raise ValueError(f"expected one master-retreat instance, found {len(matches)}")
    index, record = matches[0]
    record_end = records[index + 1]["start"] if index + 1 < count else len(crt1)
    raw_record = crt1[record["start"]:record_end]
    tail = bytearray(crt1[schema_end:])
    relative_start = record["start"] - schema_end
    relative_end = record_end - schema_end
    tail[count_offset - schema_end] = count - 1
    del tail[relative_start:relative_end]
    return bytes(tail), raw_record, record


def remove_record_from_transaction(data, node, expected_count, label):
    reader = decoder.Reader(data, 8)
    flags = reader.byte()
    if flags != 1:
        raise ValueError(f"{label} expected object-list flags 1, found {flags}")
    count_offset = reader.pos
    count = reader.packed()
    if count != expected_count or reader.pos != count_offset + 1:
        raise ValueError(
            f"{label} expected one-byte object count {expected_count}, found {count}")
    records = [decoder.read_object_record(data, reader) for _ in range(count)]
    if reader.pos != len(data):
        raise ValueError(f"{label} object walk did not reach packet end")
    matches = [(index, record) for index, record in enumerate(records)
               if record["node"] == node]
    if len(matches) != 1:
        raise ValueError(f"{label} expected one record for {node:#x}")
    index, found = matches[0]
    record_end = records[index + 1]["start"] if index + 1 < count else len(data)
    raw = data[found["start"]:record_end]
    candidate = bytearray(data)
    candidate[count_offset] = count - 1
    del candidate[found["start"]:record_end]
    return bytes(candidate), raw, found


def insert_records(data, records, expected_count, label):
    reader = decoder.Reader(data, 8)
    flags = reader.byte()
    if flags != 1:
        raise ValueError(f"{label} expected object-list flags 1, found {flags}")
    count_offset = reader.pos
    count = reader.packed()
    if count != expected_count or reader.pos != count_offset + 1:
        raise ValueError(
            f"{label} expected one-byte object count {expected_count}, found {count}")
    insert_at = reader.pos
    payload = b"".join(records)
    candidate = bytearray(data)
    candidate[count_offset] = count + len(records)
    candidate[insert_at:insert_at] = payload

    # Verify both sides of the surgical insertion.  Only the object count and
    # the inserted record may differ from the captured transaction.
    if candidate[:count_offset] != data[:count_offset]:
        raise ValueError(f"{label} prefix changed before object count")
    if candidate[insert_at + len(payload):] != data[insert_at:]:
        raise ValueError(f"{label} suffix changed after inserted records")
    return bytes(candidate), insert_at


def insert_records_after(data, start, records, target_node, expected_count, label):
    """Insert raw records immediately after the record for ``target_node``.

    Unlike :func:`insert_records` this does not assume the object list begins at
    offset 8, because CRT1's list follows its 44 kB schema table.  Both sides of
    the surgical insertion are verified so only the object count and the inserted
    bytes can differ from the input.
    """
    reader = decoder.Reader(data, start)
    flags = reader.byte()
    if flags != 1:
        raise ValueError(f"{label} expected object-list flags 1, found {flags}")
    count_offset = reader.pos
    count = reader.packed()
    if count != expected_count or reader.pos != count_offset + 1:
        raise ValueError(
            f"{label} expected one-byte object count {expected_count}, found {count}")
    parsed = [decoder.read_object_record(data, reader) for _ in range(count)]
    if reader.pos != len(data):
        raise ValueError(f"{label} object walk did not reach packet end")
    matches = [(index, record) for index, record in enumerate(parsed)
               if record["node"] == target_node]
    if len(matches) != 1:
        raise ValueError(
            f"{label} expected one record for {target_node:#x}, found {len(matches)}")
    index, _ = matches[0]
    insert_at = parsed[index + 1]["start"] if index + 1 < count else len(data)
    payload = b"".join(records)
    candidate = bytearray(data)
    candidate[count_offset] = count + len(records)
    candidate[insert_at:insert_at] = payload
    if candidate[:count_offset] != data[:count_offset]:
        raise ValueError(f"{label} prefix changed before object count")
    if candidate[insert_at + len(payload):] != data[insert_at:]:
        raise ValueError(f"{label} suffix changed after inserted records")
    return bytes(candidate), insert_at


def validate_candidate_crt1(candidate, structures, phase_info_record):
    """CRT1 must create the instance and then its phase-info child.

    Both must be present in the *same* transaction that the client receives
    before CRT2 creates the local player character, because
    chrCharacter.Replication_Create fires OnPlayerCharacterNodeReady exactly
    once and phsoracle.OnPhasedInstanceUpdated returns early when the player has
    no phase-info child at that moment.
    """
    reader = decoder.Reader(candidate, 8 + struct.unpack_from("<I", candidate, 4)[0])
    if reader.byte() != 1 or reader.packed() != 54:
        raise ValueError("candidate CRT1 does not declare 54 objects")
    records = [decoder.read_object_record(candidate, reader) for _ in range(54)]
    if reader.pos != len(candidate):
        raise ValueError("candidate CRT1 object walk did not reach packet end")
    first = records[3]
    expected = (PHASE_INSTANCE_NODE, PHASE_INSTANCE_TEMPLATE, 8,
                PHASE_INSTANCE_STRUCTURE, 64)
    actual = (first["node"], first["template_id"], first["style"],
              first["structure_id"], first["inner_size"])
    if actual != expected:
        raise ValueError(f"candidate phase-instance record mismatch: {actual}")
    second = records[4]
    if second["node"] != PHASE_INFO_NODE or second["parent_id"] != PHASE_INSTANCE_NODE:
        raise ValueError("inserted phase-info identity/parent is wrong")
    if candidate[second["start"]:records[5]["start"]] != phase_info_record:
        raise ValueError("inserted phase-info record changed bytes")
    state_start = first["body_start"] + first["inner_size"]
    states, _ = decoder.field_states(candidate, state_start,
                                      first["value_end"] - state_start,
                                      len(structures[3].fields))
    if states != [1, 1]:
        raise ValueError(f"candidate phase-instance states decoded as {states}")


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
    crt4_path = decoder.CRT_DIR / "tython_blockout-4611686019869492753-1.4.acrt"
    crt1 = crt1_path.read_bytes()
    crt3 = crt3_path.read_bytes()
    crt4 = crt4_path.read_bytes()
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
    # CRT1 keeps its original phase-instance record in place and gains the
    # phase-info child immediately after it.  Both must arrive before CRT2
    # creates the local player character: chrCharacter.Replication_Create fires
    # OnPlayerCharacterNodeReady once, and phsoracle.OnPhasedInstanceUpdated
    # returns early when the player has no phase-info child at that instant, in
    # which case the phase banner never appears for the whole session.
    candidate_header = bytearray(crt1[:8])
    struct.pack_into("<I", candidate_header, 4, len(encoded_schema))
    candidate1_draft = bytes(candidate_header) + encoded_schema + crt1[consumed:]
    structure_offset = locate_crt3_structure(crt3)
    candidate3 = bytearray(crt3)
    candidate3[structure_offset] = phase_structure
    candidate4, phase_info_record, original_phase_info = remove_record_from_transaction(
        crt4, PHASE_INFO_NODE, 11, "CRT4")
    if original_phase_info["parent_id"] != PHASE_INSTANCE_NODE:
        raise ValueError("captured phase-info has unexpected parent")
    crt1_list_start = len(candidate_header) + len(encoded_schema)
    candidate1, crt1_insert_offset = insert_records_after(
        candidate1_draft, crt1_list_start, [phase_info_record],
        PHASE_INSTANCE_NODE, 53, "CRT1")
    validate_candidate_crt1(candidate1, proposed, phase_info_record)
    differences = [i for i, (a, b) in enumerate(zip(crt3, candidate3)) if a != b]
    if differences != [structure_offset]:
        raise ValueError(f"unexpected CRT3 differences: {differences}")
    new_structures, new_consumed = builder.decode_schema_bytes(candidate1[8:])
    if len(new_structures) != 107:
        raise ValueError("candidate CRT1 did not decode 107 structures")
    if struct.unpack_from("<I", candidate1, 4)[0] != new_consumed:
        raise ValueError("candidate CRT1 header does not bound the full schema")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out1 = args.output_dir / crt1_path.name
    out3 = args.output_dir / crt3_path.name
    out4 = args.output_dir / crt4_path.name
    out1.write_bytes(candidate1)
    out3.write_bytes(candidate3)
    out4.write_bytes(candidate4)

    # A stale CRT11 override would silently keep the superseded arrangement in
    # play, so it is removed deliberately rather than left behind.
    stale11 = args.output_dir / "tython_blockout-4611686019869492753-1.11.acrt"
    if stale11.exists():
        stale11.unlink()
        print(f"REMOVED stale CRT11 override: {stale11}")

    print(f"WROTE diagnostic CRT1: {out1} ({len(candidate1)} bytes)")
    print(f"CRT1 schema bound: {original_schema_size} -> {len(encoded_schema)} bytes")
    print(f"CRT1 object count: 53 -> 54; inserted the exact "
          f"{len(phase_info_record)}-byte phsClassPhaseInfo record at offset "
          f"0x{crt1_insert_offset:X}, directly after the phase instance")
    print(f"WROTE diagnostic CRT3: {out3} ({len(candidate3)} bytes)")
    print(f"CRT3 sole byte change: offset 0x{structure_offset:X}, 0x01 -> "
          f"0x{phase_structure:02X}")
    print(f"WROTE diagnostic CRT4: {out4} ({len(candidate4)} bytes)")
    print("CRT4 object count: 11 -> 10; removed that record")
    print("CRT11 uses the production fixture unchanged.")
    print("Production AreaServer fixtures were not modified.")


if __name__ == "__main__":
    main()
