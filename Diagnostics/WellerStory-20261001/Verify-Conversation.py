"""Check emitted conversation records against the independent captured CRT decoder."""
import importlib.util
import sys
from pathlib import Path

folder = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('crt', folder.parent / 'Decode-Style7Replication.py')
crt = importlib.util.module_from_spec(spec)
sys.modules['crt'] = crt
spec.loader.exec_module(crt)
schemas, _, _ = crt.read_schema()
for area in (8, 19):
    data = (folder / f'conversation-{area}.bin').read_bytes()
    reader = crt.Reader(data, 16)
    assert reader.byte() == 1 and reader.packed() == 2
    for structure in (60, 59):
        record = crt.read_object_record(data, reader)
        assert record['structure_id'] == structure
        assert record['class_id'] == schemas[structure].base_class
        assert record['flags'] == 0x8a
        values = crt.Reader(data, record['body_start'], record['body_start'] + record['inner_size'])
        if structure == 60:
            assert values.packed() == 0x1ac6f6dc6d
            size = values.packed()
            name = data[values.pos:values.pos + size].decode('ascii')
            values.pos += size
            assert name == 'cnv.location.tython.class.jedi_knight_new.derrin_weller'
        else:
            assert values.packed() == 0x1ac7000001
        assert values.pos == values.end
        states, _ = crt.field_states(data, values.end, record['value_end'] - values.end, len(schemas[structure].fields), 8)
        assert states == [1] * len(states)
        assert record['value_end'] == values.end + 1
    assert reader.pos == len(data)
    print(f'PASS area {area}: instance before controller; captured schemas, values, reference, states and exact lengths ({len(data)} bytes).')
    for stage, node, structure in ((1, 0x1ac7000002, 59), (2, 0x1ac7000001, 60)):
        data = (folder / f'end-{area}-{stage}.bin').read_bytes()
        assert int.from_bytes(data[4:6], 'little') == 0x65b3
        assert int.from_bytes(data[6:8], 'little') == area
        reader = crt.Reader(data, 16)
        assert reader.byte() == 3 and reader.packed() == 1
        record = crt.read_object_record(data, reader)
        assert record['node'] == node and record['flags'] == 9
        assert record['structure_id'] == structure and record['style'] == 8
        assert reader.packed() == 1 and reader.packed() == node
        assert reader.pos == len(data)
        values = crt.Reader(data, record['body_start'], record['body_start'] + record['inner_size'])
        assert values.packed() == (0x1ac7000001 if stage == 1 else 0x1ac6f6dc6d)
        if stage == 2:
            length = values.packed()
            assert data[values.pos:values.pos + length].decode('ascii') == name
            values.pos += length
        assert values.pos == values.end
        states, _ = crt.field_states(data, values.end, record['value_end'] - values.end, len(schemas[structure].fields), 8)
        assert states == [1] * len(states)
    print(f'PASS area {area}: ordered controller/instance removal transactions; no unrelated fields touched; exact framing and values.')
