"""Build opt-in taxi awareness from captured schemas, not new packet IDs.

Placement and vendor health values are compatibility defaults for the first
NPC acceptance run. They are not an authored taxi location or combat stats.

Appearance/identity: every object that renders in this client (the captured
vendor 0x1AC68957EB, Weller) carries more than health and a visual index -- it
also carries the identity fields that let the client resolve a model:
chrCreatureTypeList, cbtFaction, chrTemplateVisualIndex, cbtCreatureType,
brkResourceName, chrClass, _characterSpecification, ablContainer and chrLevel.
The first synthesized record omitted all of them, so the client instantiated
the object (minimap marker, Taxis tutorial) but rendered no droid.

Those fields live in the vendor's captured tail. This generator transplants the
vendor's tail block verbatim into the same record slots, so the appearance
bytes are proven-rendering bytes rather than a re-derivation. The block is
carried as an opaque span because the client's wire layout for the tail
(enums as raw bytes, Int64 as signed packed tokens) does not match every
assumption in the local decoder, so splitting it per field locally would be
guesswork. The struct-64 tail indices map to struct-66 as follows (struct 66
drops struct-64 index 69 vndVendorIconOnExtraMaps, so indices >= 70 shift by
one): 62->62, 63->63, 66->66, 68->68, 70->69, 77->76, 78->77, 80->79, 86->85.
"""
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('generator', ROOT/'Diagnostics/Generate-CrtValues.py')
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
s, _, _ = g.d7.read_schema()
pack = g.pack_int
source = ROOT/'SharpServer/bin/Debug/AreaServer/Awareness/tython_blockout-4611686019869492753-1.1.aaw'
data = source.read_bytes()
r, flags, count = g.d7.read_gom_update(data, 0, 'captured awareness')
records = [g.d7.read_object_record(data, r) for _ in range(count)]
assert r.pos == len(data)
donor = next(x for x in records if x['node'] == 0x1AC68957EB)
assert donor['structure_id'] == 64 and donor['inner_size'] == 380
NPC, EQP, POS, NEG, OTHER = [0x1AC7001000+i for i in range(5)]
TEMPLATE, TERMINAL = 0xE0008B8CC0FAEA1D, 0xE000DC42A2436F58
# Authored anchor, not a vendor offset. The area instance dump stores coordinates
# as integers with X = col1/10, Z = col2/10, Y = col3/10; that mapping is pinned by
# med_poi01_masters_retreat.spn_c (-597,-1285,-69) -> (-59.7,-6.9,-128.5), which
# matches the captured exterior vendor at (-59.787,-6.8998,-128.335) to 0.19.
# The taxi pad spawner row (-535,-1255,-77) is therefore (-53.5,-7.7,-125.5),
# with the pad mapnote at (-53.6,-7.7,-125.9) and the two authored air speeders at
# (-52.9,-7.7,-125.3) and (-53.9,-7.7,-125.1).
PLACEMENT = (-53.5, -7.7, -125.5)
# Borrowed spawn-link probe. spnSpawnedComponentClassMethods resolves the spawn
# chain as GetSpawner() -> Me.spnParentAnchorId, then
# $SPAWNER.GetSpawnerSpecForNode(anchor). spnSpawnerSpec is a script-side cache,
# not a replicated chrCharacter field, so the anchor is the only replicated
# handle into that chain -- and every captured set-1 NPC carries one while this
# record carried none. These two values are the captured vendor's, i.e. already
# accepted by the client, so this tests whether the spawn link matters at all.
# It is deliberately a probe, not the authored taxi anchor: that is an opaque
# hash absent from the GOM name table and not exposed by the Jedipedia node
# reader (which publishes only hyd/mpn/npc categories).
# chrNonPlayerCharacterClassMethods.Replication_Create registers a replicated NPC as
# $SPAWNER.spnReplicatedNpcs[spnParentAnchorId], so borrowing the vendor's anchor
# put this NPC under the SAME key as the captured medcenter droid. An NPC with no
# anchor is instead registered in spnReplicatedAnchorlessNpcs, which is the
# correct bucket for one with no spawner. So the borrowed anchor is REMOVED, not
# merely unhelpful: it is a key collision with a working NPC.
# _characterSpecification (struct-64 field 78, struct-66 field 77) is replaced
# with the taxi's own spec: the taxi prototype's chrNonPlayerCharacterSpec is a
# self-reference to 0xE0008B8CC0FAEA1D. The donor's value 0x5541E56931B58335 is a
# capture-time runtime hash, which is why the client reports "Unknown spec(0)".
TAXI_CHAR_SPEC = 0xE0008B8CC0FAEA1D
DONOR_CHAR_SPEC = 0x5541E56931B58335
TMR_CONTAINER = 0x1AC68957EC
# Taxi-authored identity, from _JPEXTRACT/NPC/npc.location.tython.taxi.jediretreat_pad1.json
# (authoritative client content the operator extracted from Jedipedia).
# brkResourceName matters most: the client reports "Mag node doesn't have a valid
# asset spec" and "not a valid animation agent" against our node, and the
# transplanted tail was carrying the medcenter droid's resource name. The taxi
# prototype's own value replaces it in place (both encode as one 0xCF token plus
# eight bytes, so the patch cannot change the record length).
TAXI_RESOURCE_NAME = 16141090805656758403        # 0xE000AC918E7EA883
VENDOR_RESOURCE_NAME = 0xE000C970F186EEC0       # the value currently in the tail
# chrGender (struct-66 field 8) and chrAppearanceNppOverride (field 59) were
# sent as chrNPCGenderComplete=5 and npcAppearanceOverride=3. Both are AUTHORED on
# the taxi prototype but NEITHER is in its replicated surface, which is exactly
# taxTerminalSpec + brkResourceName, and neither appears in any reference NPC
# record. Dropping them makes this record present the same field set the captured
# vendor does: the single variable of Experiments/2026-10-02-07. The record gets 2
# bytes shorter, so every identity-patch offset downstream must move with it.
values = {0:struct.pack('<3f', *PLACEMENT),
    1:data[donor['body_start']+12:donor['body_start']+24],
    9:struct.pack('<f',1), 10:struct.pack('<f',.1), 13:pack(2),
    22:pack(1),23:pack(EQP),24:pack(POS),25:pack(NEG),26:pack(OTHER),
    32:pack(TERMINAL),33:pack(TMR_CONTAINER),
    57:pack(TEMPLATE)}
# staEnterIdle (struct-66 field 37) is the only field the taxi lacks that Weller
# -- the single confirmed working NPC -- carries. Weller receives it through
# CRT12, the one NPC replication contract in the whole capture. We first try the
# cheaper route and set it directly in the awareness record.
# It is a Boolean (part kind 3), so it consumes ZERO value bytes: its state bit
# IS its value. Adding it flips exactly one presence bit in the state run and
# leaves the record length unchanged. Evidence: Weller struct-62 field 38
# decodes to state 1 (present).
values[37]=b''
# Copy only independently bounded captured NPC health/stat fields. Enum keys
# are packed, including 232/233/254/255; the older diagnostic's byte-enum walk
# cannot round-trip this NPC. The verified spans end before appearance fields.
# The presence-bit run is TWO BITS PER FIELD (style 8) and lives AFTER the value
# body, at body_start + inner_size. Weller's captured record proves this: 96
# fields x 2 bits = 192 bits = 24 bytes, and the run is exactly 24 bytes. Style 7
# would be 12 bytes and leave 12 unexplained. Do not "fix" this to 7.
stats_start = donor['body_start']+73
w = g.ValueWalker(data,stats_start,donor['body_start']+donor['inner_size'],8)
for index in (34,35):
    start=w.pos; raw=w.packed(); assert raw % 2 == 0
    for _ in range(raw//2):
        w.packed(); w.raw(4)
    values[index] = data[start:w.pos]
assert w.raw(4) == struct.pack('<f',460)
values[36] = struct.pack('<f',460)
values[38] = pack(3); values[39] = struct.pack('<f',-1)
# Walk the donor's own body up to the appearance/identity tail (fields 62..86 in
# struct-64 order) with the model that reconciles through field 61: presence
# carries Booleans, enums are packed, Int64 is signed.
donor_structure = s[donor['structure_id']]
donor_begin = donor['body_start']; donor_end = donor_begin+donor['inner_size']
donor_states = g.dc.field_states(data,donor_end,donor['value_end']-donor_end,
                                 len(donor_structure.fields),8)
_parse_part = g.parse_part
def _walk_part(walker,field,index,style):
    kind=field.parts[index].kind
    if kind==3: return g.Part(kind,1)
    if kind==2: return g.Part(kind,walker.packed_signed())
    if kind==5: return g.Part(kind,walker.packed())
    return _parse_part(walker,field,index,style)
# parse_container calls the module-level parse_part for entries, so patch it for
# the donor walk and restore it before the captured-container round-trips.
g.parse_part = _walk_part
try:
    donor_walker = g.ValueWalker(data,donor_begin,donor_end,8)
    for index,state in enumerate(donor_states):
        if state!=1: continue
        if index>=62: break
        field=donor_structure.fields[index]
        if field.parts[0].kind in (7,8): g.parse_container(donor_walker,field,8)
        else: g.parse_part(donor_walker,field,0,8)
finally:
    g.parse_part = _parse_part
tail_block = data[donor_walker.pos:donor_end]
# Replace the donor's brkResourceName inside the opaque tail with the taxi's own.
# Both values encode as one 0xCF token plus eight big-endian bytes, so the
# substitution is length-preserving and cannot disturb any other field's offset.
vendor_rn = b'\xCF' + VENDOR_RESOURCE_NAME.to_bytes(8, 'big')
taxi_rn = b'\xCF' + TAXI_RESOURCE_NAME.to_bytes(8, 'big')
assert len(vendor_rn) == len(taxi_rn) == 9, (len(vendor_rn), len(taxi_rn))
hits = tail_block.count(vendor_rn)
assert hits == 1, f'expected exactly one donor resource name in the tail, found {hits}'
tail_block = tail_block.replace(vendor_rn, taxi_rn)
assert taxi_rn in tail_block and vendor_rn not in tail_block
# Replace the donor's _characterSpecification with the taxi's own spec. Both encode
# as one 0xCF token plus eight bytes, so this is also length-preserving.
donor_spec = b'\xCF' + DONOR_CHAR_SPEC.to_bytes(8, 'big')
taxi_spec = b'\xCF' + TAXI_CHAR_SPEC.to_bytes(8, 'big')
assert len(donor_spec) == len(taxi_spec) == 9
assert tail_block.count(donor_spec) == 1, f'donor char spec count {tail_block.count(donor_spec)}'
tail_block = tail_block.replace(donor_spec, taxi_spec)
assert taxi_spec in tail_block and donor_spec not in tail_block
# The donor's captured tail fields, in struct-64 order, and their struct-66
# indices (struct 66 drops struct-64 index 69, so indices >= 70 shift by one).
donor_tail = [i for i,state in enumerate(donor_states) if state==1 and i>=62]
assert donor_tail==[62,63,66,68,70,77,78,80,86], donor_tail
APPEARANCE = (62,63,66,68,69,76,77,79,85)
assert len(tail_block)==57, len(tail_block)
# Targetability is represented by the captured Boolean field state, with no
# value byte. This is provisional until the client renders/selects this NPC.
states = [1 if i in values or i == 61 or i in APPEARANCE else 2 for i in range(len(s[66].fields))]
assert states[37] == 1, 'staEnterIdle must be marked present'
body=b''.join(values[i] for i in sorted(values) if i<=61)+tail_block
bits=''.join('01' if state==1 else '00' for state in states)
bits+='0'*(-len(bits)%8)
state_bytes=bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8))
assert g.dc.field_states(state_bytes,0,len(state_bytes),len(states),8)==states
outer=pack(66)+pack(len(body))+body+state_bytes
record=pack(NPC)+bytes([0x7A])+pack(TEMPLATE)+pack(donor['parent_id'])
record+=bytes([1])+struct.pack('<I',len(s[66].additional_classes))
record+=b''.join(struct.pack('<Q',c) for c in s[66].additional_classes)
record+=bytes([5,8])+pack(len(outer))+outer
generated=[record]
for old,new in ((0x1AC68957ED,EQP),(0x1AC68957EF,POS),(0x1AC68957F0,NEG),(0x1AC68957F1,OTHER)):
    captured=next(x for x in records if x['node']==old)
    assert g.roundtrip_record(data,captured,s[captured['structure_id']],g.d7.name_table())[0]
    # Preserve prototype/shared-container spec fields, empty the effect list,
    # and make the equipment owner point to this NPC. No copied effect nodes.
    start=captured['body_start']; end=start+captured['inner_size']
    walker=g.ValueWalker(data,start,end,7)
    states=g.dc.field_states(data,end,captured['value_end']-end,5,7)
    fields={}
    for i,state in enumerate(states):
        if state != 1: continue
        field=s[captured['structure_id']].fields[i]
        part=g.parse_container(walker,field,7) if field.parts[0].kind in (7,8) else g.parse_part(walker,field,0,7)
        if i==0: part.count=0; part.children=[]
        if i==3: part.value=NPC
        output=bytearray();g.emit_part(output,part);fields[i]=bytes(output)
    assert walker.pos==end
    body=b''.join(fields[i] for i in sorted(fields))
    outer=pack(captured['structure_id'])+pack(len(body))+body+g.encode_states(states,7)
    generated.append(pack(new)+bytes([0xAA])+pack(captured['class_id'])+pack(NPC)+bytes([5,7])+pack(len(outer))+outer)
payload=struct.pack('<I',0)+bytes([1])+pack(len(generated))+b''.join(generated)
reader,_,count=g.d7.read_gom_update(payload,0,'generated taxi awareness')
result=[g.d7.read_object_record(payload,reader) for _ in range(count)]
assert reader.pos==len(payload) and len(result)==5
assert result[0]['template_id']==TEMPLATE and result[0]['structure_id']==66
output=ROOT/'SharpServer/AreaServer/TaxiNpc.bin'
output.write_bytes(payload)
patches=[]
for slot,node in enumerate((NPC,EQP,POS,NEG,OTHER)):
    token=pack(node);start=0
    while (offset:=payload.find(token,start))>=0:
        patches.append({'offset':offset,'slot':slot});start=offset+len(token)
# ------------------------------------------------------------------ control clone
# The captured medcenter droid record, byte-for-byte, with ONLY the node id changed.
#
# Why this exists: the taxi record has produced three consecutive behavioural no-ops
# (brkResourceName, _characterSpecification, staEnterIdle), all with byte-identical
# error traces. Meanwhile the captured medcenter droid -- delivered unmodified in the
# real initial payload, never constructed by this generator -- demonstrably renders a
# model. So the clone isolates OUR synthesis and delivery from the taxi's CONTENT:
#   renders  -> the generator path is sound; the fault is taxi-specific content, and
#               the struct-64/vndVendorComponent swap becomes a real candidate.
#   no model -> the generator assembly or the delivery position is at fault, and every
#               content experiment so far was uninterpretable.
# Delivered from the same place in the startup bundle as the taxi, so versus runs
# 8a/8b the only variable is record content.
donor_index=records.index(donor)
assert donor_index+1<len(records),'donor is the last record; cannot bound its raw span'
donor_stop=records[donor_index+1]['start']
clone_record=bytearray(data[donor['start']:donor_stop])
donor_token=pack(donor['node'])
assert bytes(clone_record[:len(donor_token)])==donor_token,'clone must start with the donor node'
clone_token=pack(NPC)
assert len(clone_token)==len(donor_token),'node widths differ; substitution would move every offset'
clone_record[:len(clone_token)]=clone_token
# Same object-list framing as the captured awareness: LE u32 pad, flags, count, record.
clone_payload=struct.pack('<I',0)+bytes([1])+pack(1)+bytes(clone_record)
CLONE_NODE_OFFSET=4+1+len(pack(1))
clone_out=ROOT/'SharpServer/AreaServer/TaxiClone.bin'
clone_out.write_bytes(clone_payload)
_crdr,_,_ccount=g.d7.read_gom_update(clone_payload,0,'taxi clone control')
_crec=g.d7.read_object_record(clone_payload,_crdr)
assert _ccount==1 and _crec['node']==NPC and _crec['structure_id']==donor['structure_id']
assert _crec['template_id']==donor['template_id'],'clone must keep the captured template'
report={'source_sha256':hashlib.sha256(data).hexdigest(),'fixture_sha256':hashlib.sha256(payload).hexdigest(),
        'bytes':len(payload),'patches':sorted(patches,key=lambda p:p['offset']),
        'placement':list(PLACEMENT),'placement_source':'authored taxi_poi01_jediretreat_pad1.spn_c instance row (-535,-1255,-77); X=col1/10 Z=col2/10 Y=col3/10 calibrated against the captured vendor',
        'taxi_template':hex(TEMPLATE),'terminal':hex(TERMINAL),
        'appearance_fields':list(APPEARANCE),'donor_tail_bytes':len(tail_block),
        'donor_tail_fields':donor_tail,
        'confidence':'Hypothesis','records':result,
        'clone_control':{'file':str(clone_out.relative_to(ROOT)).replace('\\','/'),
                         'bytes':len(clone_payload),
                         'sha256':hashlib.sha256(clone_payload).hexdigest(),
                         'node_offset':CLONE_NODE_OFFSET,
                         'source_node':hex(donor['node']),'source_template':hex(donor['template_id']),
                         'structure_id':donor['structure_id'],
                         'confidence':'Behavior-verified pending'}}
Path(__file__).with_name('fixture.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
