#!/usr/bin/env python3
"""Read-only inventory of the captured Tython awareness GOM updates."""

import importlib.util
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "SharpServer" / "bin" / "Debug" / "AreaServer"


def load_decoder():
    path = HERE / "Decode-Style7Replication.py"
    spec = importlib.util.spec_from_file_location("style7_decoder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    decoder = load_decoder()
    names = decoder.name_table()
    structures, _, _ = decoder.read_schema()
    pattern = "tython_blockout-4611686019869492753-1.*.aaw"
    for path in sorted((SERVER / "Awareness").glob(pattern)):
        data = path.read_bytes()
        reader, flags, count = decoder.read_gom_update(data, 0, path.name)
        if reader is None:
            continue
        inventory = {}
        for index in range(count):
            record = decoder.read_object_record(data, reader)
            class_id = record["class_id"]
            if not class_id and record["structure_id"] in structures:
                class_id = structures[record["structure_id"]].base_class
            class_name = names.get(class_id, "")
            if class_name:
                inventory[class_name] = inventory.get(class_name, 0) + 1
            print(
                f"  {index:3} @0x{record['start']:04X} "
                f"node={record['node']:#018x} flags=0x{record['flags']:02X} "
                f"class={class_name or '<unknown>'} "
                f"parent={record['parent_id']:#018x} "
                f"structure={record['structure_id']}"
            )
            if record["structure_id"] == 41:
                values = data[record["body_start"]:
                              record["body_start"] + record["inner_size"]]
                # Structure 41 is the two-field hydTriggerEntity compact
                # structure.  Its captured value region is a UInt64 Hydra
                # script prototype followed by a Vector3 position.
                if len(values) == 21 and values[0] == 0xCF:
                    script_id = int.from_bytes(values[1:9], "big")
                    x, y, z = struct.unpack("<fff", values[9:])
                    print(
                        f"      hydRunScriptProtoId=0x{script_id:016X} "
                        f"hydPosition=({x:.6f},{y:.6f},{z:.6f})"
                    )
                else:
                    print(f"      structure41-values={values.hex()}")
        if flags & 0x02:
            removals = [reader.packed() for _ in range(reader.packed())]
            print("  removals: " + ", ".join(hex(node) for node in removals))
        print("  classes: " + ", ".join(
            f"{name}x{amount}" for name, amount in sorted(inventory.items())))
        print(f"  end=0x{reader.pos:X} of 0x{len(data):X}")


if __name__ == "__main__":
    main()
