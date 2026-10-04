"""Verify built packet framing and schema fields independently of the writer."""
import importlib.util
import struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('d7',ROOT/'Diagnostics/Decode-Style7Replication.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
schemas,_,_=d.read_schema()
HERE=Path(__file__).resolve().parent
for area in (8,19):
    data=(HERE/f'awareness-{area}.bin').read_bytes()
    assert struct.unpack('<IHH',data[:8])==(0xA1D9E226,0x65B3,area)
    payload=data[8:];r,flags,count=d.read_gom_update(payload,0,'taxi')
    records=[d.read_object_record(payload,r) for _ in range(count)]
    assert r.pos==len(payload) and count==5
    assert {x['node'] for x in records}==set(range(0x1AC7002000,0x1AC7002005))
    npc=records[0]
    assert npc['structure_id']==66 and npc['template_id']==0xE0008B8CC0FAEA1D
    assert npc['parent_id']==0x1AC688BE1E
    values=d.Reader(payload,npc['body_start'],npc['body_start']+npc['inner_size'])
    # Authored taxi pad anchor (instance row -535,-1255,-77); rotation follows the
    # captured vendor and is still unverified.
    assert tuple(round(v,4) for v in struct.unpack('<3f',payload[values.pos:values.pos+12]))==(-53.5,-7.7,-125.5)
    values.pos+=24
    assert values.byte()==5             # chrGender, from the taxi chrNPCGenderComplete
    values.pos+=8
    assert values.packed()==2 and values.packed()==1
    assert [values.packed() for _ in range(4)]==list(range(0x1AC7002001,0x1AC7002005))
    # Borrowed spawn-link probe: spnParentAnchorId (27), taxTerminalSpec (32),
    # tmrContainer (33). See Generate-Taxi.py for why these are borrowed values.
    # spnParentAnchorId (27) is deliberately ABSENT: Replication_Create keys
    # spnReplicatedNpcs[spnParentAnchorId], so borrowing the donor's anchor
    # collided with the medcenter droid. Then taxTerminalSpec (32), tmrContainer (33).
    assert values.packed()==0xE000DC42A2436F58
    assert values.packed()==0x1AC68957EC
    for _ in range(2):
        entries=values.packed();assert entries%2==0
        for _ in range(entries//2):
            values.packed();values.pos+=4
    assert struct.unpack('<f',payload[values.pos:values.pos+4])[0]==460
    values.pos+=4
    assert values.packed()==3
    values.pos+=4
    assert values.packed()==0xE0008B8CC0FAEA1D
    # Captured-vendor appearance/identity tail transplanted verbatim (57 bytes).
    appearance=[62,63,66,68,69,76,77,79,85]
    assert values.end-values.pos==58, values.end-values.pos
    assert values.byte()==3             # chrAppearanceNppOverride, taxi npcAppearanceOverride
    assert values.end-values.pos==57, values.end-values.pos
    nend=npc['body_start']+npc['inner_size']
    nstates,_=d.field_states(payload,nend,npc['value_end']-nend,len(schemas[66].fields),8)
    assert set(appearance).issubset({i for i,x in enumerate(nstates) if x==1})
    for rec in records[1:]: assert rec['parent_id']==npc['node']
    for stage in ('known','clear','open'):
        data=(HERE/f'{stage}-{area}.bin').read_bytes()
        assert struct.unpack('<IHH',data[:8])==(0x0D446E80,0x65B3,area)
        r,flags,count=d.read_gom_update(data,12,'interaction')
        rec=d.read_object_record(data,r)
        assert r.pos==len(data) and count==1 and rec['structure_id']==26
        end=rec['body_start']+rec['inner_size']
        states,_=d.field_states(data,end,rec['value_end']-end,len(schemas[26].fields))
        expected=[42] if stage=='known' else [42,51,60]
        assert [i for i,x in enumerate(states) if x==1]==expected
        assert rec['value_end']-end == (len(schemas[26].fields)*2+7)//8
        v=d.Reader(data,rec['body_start'],end)
        assert v.packed()==4
        assert v.packed()==0xE000DC42A2436F58 and v.byte()==1
        assert v.packed()==0xE0009C95E5C2E162 and v.byte()==1
        if stage!='known':
            assert v.packed()==(0x1AC7002000 if stage=='open' else 0)
            assert v.packed()==(3 if stage=='open' else 1)
        assert v.pos==end
print('PASS: both area routes; exact five-object creation; fresh linked nodes; taxi template/terminal; NPC value bounds; transplanted appearance/identity tail; complete player known/clear/open updates.')
