#!/usr/bin/env python3
"""Read-only April-client player lookup and field-accessor scan in a full dump."""
import argparse
import importlib.util
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "world_dump", HERE / "Analyze-WorldEntryDump.py")
world_dump = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world_dump)
schema_spec = importlib.util.spec_from_file_location(
    "style7", HERE / "Decode-Style7Replication.py")
style7 = importlib.util.module_from_spec(schema_spec)
schema_spec.loader.exec_module(style7)

PLAYER = 0x4000010E218A839B
FIELDS = {
    "chrIsMe": 0x4000000365D249CB,
    "chrCharacterPlayMode": 0x400000077CDF593B,
    "chrCharacterPhaseMode": 0x4000000886E130D2,
    "chrPlayerLoaded": 0x4000000D5DF53477,
}

VALUE_KINDS = {
    "chrIsMe": "bool",
    "chrCharacterPlayMode": "enum",
    "chrCharacterPhaseMode": "enum",
    "chrPlayerLoaded": "bool",
}


def dword(dump, address):
    raw = dump.read(address, 4)
    if len(raw) != 4:
        raise ValueError(f"unmapped DWORD at {address:08X}")
    return struct.unpack("<I", raw)[0]


def find_player(dump, image_base):
    manager_slot = image_base + 0x010929DC
    manager = dword(dump, manager_slot)
    tree = manager + 0x38
    sentinel = tree + 4
    node = dword(dump, tree + 0x0C)
    candidate = sentinel
    wanted_low = PLAYER & 0xFFFFFFFF
    wanted_high = PLAYER >> 32
    for _ in range(256):
        if not node:
            break
        low = dword(dump, node + 0x10)
        high = dword(dump, node + 0x14)
        if high > wanted_high or (high == wanted_high and low >= wanted_low):
            candidate = node
            node = dword(dump, node + 4)
        else:
            node = dword(dump, node)
    if candidate == sentinel:
        return manager, tree, candidate, 0
    low = dword(dump, candidate + 0x10)
    high = dword(dump, candidate + 0x14)
    character = dword(dump, candidate + 0x18) if (high, low) == (wanted_high, wanted_low) else 0
    return manager, tree, candidate, character


def memory_hits(dump, signature):
    for start, size, file_offset in dump.memory:
        virtual = start & 0xFFFFFFFF if start >> 32 == 0xFFFFFFFF else start
        end = file_offset + size
        position = dump.m.find(signature, file_offset, end)
        while position >= 0:
            yield virtual + position - file_offset
            position = dump.m.find(signature, position + 1, end)


def accessor_signature(field_id):
    low = field_id & 0xFFFFFFFF
    high = field_id >> 32
    return (b"\x81\xF0" + struct.pack("<I", low) + b"\x89\xF3\x81\xF3" +
            struct.pack("<I", high) + b"\x09\xC3")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", type=Path)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    dump = world_dump.Minidump(args.dump)
    try:
        modules = dump.modules()
        image = next((item for item in modules
                      if Path(item[2]).name.lower() == "swtor-emu.exe"), None)
        if not image:
            raise ValueError("swtor-emu.exe is not present in the dump")
        image_base = image[0]
        print(f"imageBase={image_base:08X}")
        manager, tree, node, character = find_player(dump, image_base)
        print(f"manager={manager:08X} tree={tree:08X} node={node:08X} character={character:08X}")
        if not character:
            raise ValueError("selected player was not found in the native character map")
        raw = dump.read(character, 0x300)
        if len(raw) != 0x300:
            raise ValueError("selected player object is not fully mapped for 0x300 bytes")
        if not args.summary_only:
            for offset in range(0, len(raw), 0x40):
                print(f"player+{offset:03X}: {raw[offset:offset + 0x40].hex(' ')}")
        vtable = dword(dump, character)
        vmethods = struct.unpack("<32I", dump.read(vtable, 32 * 4))
        print(f"characterVtable={vtable:08X} methods=" +
              " ".join(f"{method:08X}" for method in vmethods))
        node_lookup_sig = bytes.fromhex(
            "55 8b ec 83 e4 f8 8b 45 10 8b 55 0c 50 8b 45 08 52 50")
        node_lookup_hits = list(memory_hits(dump, node_lookup_sig))
        print("getNodeByIdSignatureHits=" +
              " ".join(f"{hit:08X}" for hit in node_lookup_hits))
        gom_nodes = []
        for label, signature in (
                ("characterPointer", struct.pack("<I", character)),
                ("playerId", struct.pack("<Q", PLAYER))):
            refs = list(memory_hits(dump, signature))
            shown_refs = refs[:8] if args.summary_only else refs[:128]
            print(f"{label}Refs={len(refs)} " + " ".join(f"{ref:08X}" for ref in shown_refs))
            context_refs = refs[:8] if args.summary_only else refs[:32]
            for ref in context_refs:
                if args.summary_only and label != "characterPointer":
                    continue
                if args.summary_only:
                    print(f"  {label}@{ref:08X}: {dump.read(ref - 0x20, 0x60).hex(' ')}")
                else:
                    print(f"  {label}@{ref:08X}: {dump.read(ref - 0x20, 0x60).hex(' ')}")
            if label == "playerId":
                for ref in refs:
                    try:
                        kind = dword(dump, ref + 8)
                        value = dword(dump, ref + 12)
                    except ValueError:
                        continue
                    if kind == 1 and value and len(dump.read(value, 0x60)) == 0x60:
                        gom_nodes.append(value)
                        print(f"  gomHashEntry={ref - 8:08X} kind={kind} value={value:08X} "
                              f"valueBytes={dump.read(value, 0x120).hex(' ')}")
        structures, _, _ = style7.read_schema()
        player_fields = sorted(field.definition for field in structures[26].fields)
        schema_signature = b"".join(struct.pack("<Q", value)
                                    for value in player_fields[:12])
        schema_hits = list(memory_hits(dump, schema_signature))
        print("playerSchemaPrefixHits=" + str(len(schema_hits)) + " " +
              " ".join(f"{hit:08X}" for hit in schema_hits))
        for ids_begin in schema_hits:
            owner_refs = list(memory_hits(dump, struct.pack("<I", ids_begin)))
            print(f"  idsBegin={ids_begin:08X} pointerRefs=" +
                  " ".join(f"{ref:08X}" for ref in owner_refs[:64]))
            for owner_ref in owner_refs:
                hero_type = owner_ref - 0x4C
                try:
                    if dword(dump, hero_type + 0x50) != ids_begin + len(player_fields) * 8:
                        continue
                    descriptors = dword(dump, hero_type + 0x9C)
                except ValueError:
                    continue
                object_refs = list(memory_hits(dump, struct.pack("<I", hero_type)))
                print(f"    heroType={hero_type:08X} descriptors={descriptors:08X} "
                      f"objectRefs=" + " ".join(f"{ref:08X}" for ref in object_refs[:64]))
        layouts = []
        queue = [(character, 0)] + [(gom_node, 0) for gom_node in gom_nodes]
        visited = set()
        while queue and len(visited) < 20000:
            hero_object, depth = queue.pop(0)
            if hero_object in visited:
                continue
            visited.add(hero_object)
            block = dump.read(hero_object, 0x300)
            if len(block) < 0xA0:
                continue
            if depth < (1 if args.summary_only else 3):
                for pointer_offset in range(0, len(block) - 3, 4):
                    pointer = struct.unpack_from("<I", block, pointer_offset)[0]
                    if pointer >= 0x10000 and pointer not in visited and len(dump.read(pointer, 0x20)) == 0x20:
                        queue.append((pointer, depth + 1))
            hero_type = dword(dump, hero_object + 0x18)
            try:
                ids_begin = dword(dump, hero_type + 0x4C)
                ids_end = dword(dump, hero_type + 0x50)
                descriptors = dword(dump, hero_type + 0x9C)
            except ValueError:
                continue
            if ids_end < ids_begin or (ids_end - ids_begin) % 8:
                continue
            count = (ids_end - ids_begin) // 8
            if count <= 0 or count > 4096 or len(dump.read(ids_begin, count * 8)) != count * 8:
                continue
            present = [field_id for field_id in FIELDS.values()
                       if struct.pack("<Q", field_id) in dump.read(ids_begin, count * 8)]
            if present:
                layouts.append((hero_object, hero_type, ids_begin, ids_end,
                                descriptors, count))
                print(f"heroObject={hero_object:08X} heroType={hero_type:08X} "
                      f"ids={ids_begin:08X}..{ids_end:08X} count={count} "
                      f"descriptors={descriptors:08X} targetFields={len(present)}")
                if not args.summary_only:
                    print(f"  heroObjectBytes={dump.read(hero_object, 0x180).hex(' ')}")
        print(f"heroGraphObjectsVisited={len(visited)} matchingLayouts={len(layouts)}")
        for name, field_id in FIELDS.items():
            matches = []
            for hero_object, hero_type, ids_begin, ids_end, descriptors, count in layouts:
                for index in range(count):
                    if struct.unpack("<Q", dump.read(ids_begin + index * 8, 8))[0] == field_id:
                        descriptor = descriptors + index * 12
                        words = struct.unpack("<III", dump.read(descriptor, 12))
                        matches.append(index)
                        print(f"{name} heroObject={hero_object:08X} "
                              f"runtimeIndex={index} descriptor={descriptor:08X} "
                              f"words={words[0]:08X},{words[1]:08X},{words[2]:08X}")
                        print(f"  fieldMetaBytes={dump.read(words[0], 0x80).hex(' ')}")
                        # Scalar proxy methods at 0x004CFE90/0x004D1020 use
                        # HeroClass+0x14 as the per-value context.  0x004D0DA0
                        # then resolves the ID a second time in [context+4].
                        context = dword(dump, hero_object + 0x14)
                        concrete_type = dword(dump, context + 4)
                        concrete_ids_begin = dword(dump, concrete_type + 0x4C)
                        concrete_ids_end = dword(dump, concrete_type + 0x50)
                        concrete_descriptors = dword(dump, concrete_type + 0x9C)
                        concrete_count = (concrete_ids_end - concrete_ids_begin) // 8
                        concrete_index = None
                        for candidate_index in range(concrete_count):
                            candidate = struct.unpack(
                                "<Q", dump.read(concrete_ids_begin + candidate_index * 8, 8))[0]
                            if candidate == field_id:
                                concrete_index = candidate_index
                                break
                        if concrete_index is None:
                            print(f"  concreteContext={context:08X} type={concrete_type:08X} "
                                  "fieldMissing")
                            continue
                        resolved_descriptor = concrete_descriptors + concrete_index * 12
                        resolved_words = struct.unpack(
                            "<III", dump.read(resolved_descriptor, 12))
                        storage_base = dword(dump, context + 8)
                        state_address = (storage_base + resolved_words[1]) & 0xFFFFFFFF
                        value_address = (storage_base + resolved_words[2]) & 0xFFFFFFFF
                        state_raw = dump.read(state_address, 1)
                        print(f"  contextBytes={dump.read(context, 0x30).hex(' ')}")
                        if not state_raw:
                            print(f"  context={context:08X} storageBase={storage_base:08X} "
                                  f"unmappedStateAddress={state_address:08X}")
                            continue
                        state_byte = state_raw[0]
                        value_bytes = dump.read(value_address, 0x20)
                        value_kind = VALUE_KINDS.get(name)
                        runtime_value = None
                        if (state_byte & 3) == 0 and value_kind == "bool" and value_bytes:
                            runtime_value = "true" if value_bytes[0] else "false"
                        elif ((state_byte & 3) == 0 and value_kind == "enum" and
                              len(value_bytes) >= 4):
                            runtime_value = str(struct.unpack_from("<I", value_bytes)[0])
                        print(f"  context={context:08X} concreteType={concrete_type:08X} "
                              f"resolvedIndex={concrete_index} "
                              f"resolvedDescriptor={resolved_descriptor:08X} "
                              f"resolvedWords={resolved_words[0]:08X},{resolved_words[1]:08X},{resolved_words[2]:08X} "
                              f"storageBase={storage_base:08X} "
                              f"stateAddress={state_address:08X} stateByte={state_byte:02X} "
                              f"state={state_byte & 3} valueAddress={value_address:08X} "
                              f"valueBytes={value_bytes.hex(' ')}")
                        if runtime_value is not None:
                            print(f"  runtimeValue={runtime_value} ({value_kind})")
                        if name == "chrPlayerLoaded":
                            for reference_name, reference_value in (
                                    ("fieldMeta", resolved_words[0]),
                                    ("stateAddress", state_address),
                                    ("valueAddress", value_address)):
                                references = list(memory_hits(
                                    dump, struct.pack("<I", reference_value)))
                                print(f"  {reference_name}PointerRefs={len(references)} " +
                                      " ".join(f"{item:08X}" for item in references[:64]))
                                if reference_name == "fieldMeta":
                                    for item in references[:16]:
                                        print(f"    ref@{item:08X}=" +
                                              dump.read(item - 0x20, 0x60).hex(' '))
                                        if dump.read(item - 8, 8) == struct.pack("<Q", field_id):
                                            for delta in (-0x20, -0x10, -0x0C, -8, 0):
                                                candidate = (item + delta) & 0xFFFFFFFF
                                                candidate_refs = list(memory_hits(
                                                    dump, struct.pack("<I", candidate)))
                                                print(f"      candidate={candidate:08X} "
                                                      f"pointerRefs={len(candidate_refs)} " +
                                                      " ".join(f"{ref:08X}" for ref in candidate_refs[:32]))
                                                for candidate_ref in candidate_refs[:8]:
                                                    print(f"        pointerRef@{candidate_ref:08X}=" +
                                                          dump.read(candidate_ref - 0x20, 0x80).hex(' '))
            hits = list(memory_hits(dump, accessor_signature(field_id)))
            print(f"{name} id={field_id:016X} accessorSignatureHits={len(hits)} " +
                  " ".join(f"{hit:08X}" for hit in hits[:16]))
            for hit in hits[:4]:
                entry = hit - 0x94
                code = dump.read(entry, 0x180)
                print(f"  candidate={entry:08X} bytes={code.hex(' ')}")
            raw_hits = list(memory_hits(dump, struct.pack("<Q", field_id)))
            print(f"  rawIdHits={len(raw_hits)} " +
                  " ".join(f"{hit:08X}" for hit in raw_hits[:32]))
            if not args.summary_only:
                for hit in raw_hits[:16]:
                    before = dump.read(hit - 0x20, 0x60)
                    print(f"    raw@{hit:08X}: {before.hex(' ')}")
    finally:
        dump.close()


if __name__ == "__main__":
    main()
