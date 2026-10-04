"""Compare phsPhase across captured NPCs and our synthetic taxi.

User hypothesis: the taxi may be authored into the wrong phase, so the client
builds the object but the player never sees it -- possibly a consequence of our own
synthetic phase behaviour (phase exit / reentry experiments) rather than a bad
record.

chrNonPlayerCharacter carries a phsPhase field (struct-66 index 22). If the working
captured NPCs and our taxi disagree on it, that is a concrete, testable cause that
no amount of appearance-field tuning would ever fix.

Decodes one named field per record by walking the presence-run and value body the
same way the generator does, so the reported value is the real transmitted value and
not a re-derivation of offsets.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'Diagnostics'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


d = load('d7', HERE / 'Decode-Style7Replication.py')
g = load('cv', HERE / 'Generate-CrtValues.py')
schemas, _, _ = d.read_schema()
names = d.name_table()

TARGETS = [
    ('Weller (works, captured)',
     ROOT / 'SharpServer/bin/Debug/AreaServer/Awareness/tython_blockout-4611686019869492753-1.2.aaw',
     0x1AC6F6DC6D),
    ('medcenter droid (model renders)',
     ROOT / 'SharpServer/bin/Debug/AreaServer/Awareness/tython_blockout-4611686019869492753-1.1.aaw',
     0x1AC68957EB),
]

FIELDS = ('phsPhase', 'brkResourceName', '_characterSpecification',
          'chrAppearanceNppOverride', 'tmrContainer')

_orig = g.parse_part


def walker_for(structure_id, data, rec):
    s = schemas[structure_id]

    def pp(walker, field, index, style):
        kind = field.parts[index].kind
        if kind == 3:
            return g.Part(kind, 1)
        if kind == 2:
            return g.Part(kind, walker.packed_signed())
        if kind == 5:
            return g.Part(kind, walker.packed())
        return _orig(walker, field, index, style)

    return s, pp


def decode(path, node, label):
    data = path.read_bytes()
    if path.name.endswith('.bin'):
        rd = d.Reader(data, 6)
        count = 1
    else:
        rd, _, count = d.read_gom_update(data, 0, path.name)
    rec = None
    for _ in range(count):
        r = d.read_object_record(data, rd)
        if r['node'] == node:
            rec = r
            break
    if rec is None:
        print('%-32s NODE 0x%016X NOT FOUND' % (label, node))
        return
    sid = rec['structure_id']
    s, pp = walker_for(sid, data, rec)
    end = rec['body_start'] + rec['inner_size']
    # field_states returns (states, bits); unpack or the index test reads the tuple.
    states, _bits = d.field_states(data, end, rec['value_end'] - end,
                                   len(s.fields), 8)
    print('=== %s' % label)
    print('    struct=%d fields=%d inner_size=%d' % (sid, len(s.fields), rec['inner_size']))
    g.parse_part = pp
    try:
        w = g.ValueWalker(data, rec['body_start'], end, 8)
        for index, st in enumerate(states):
            if st != 1:
                continue
            f = s.fields[index]
            fname = names.get(f.definition, '?')
            # Containers are common in the appearance tail; guard them so one bad
            # walk does not abort the report for every record still pending.
            if f.parts[0].kind in (7, 8):
                try:
                    g.parse_container(w, f, 8)
                except Exception as exc:
                    print('    container walk failed at %s idx=%d: %s'
                          % (fname, index, exc))
                    break
                continue
            start = w.pos
            try:
                part = pp(w, f, 0, 8)
            except Exception as exc:
                print('    walk error at field %d (%s): %s'
                      % (index, fname, exc))
                break
            if fname in FIELDS:
                raw = (hex(part.value) if isinstance(part.value, int)
                       else repr(part.value))
                print('    %-28s idx=%-3d present=yes value=%s'
                      % (fname, index, raw))
            _ = start
    finally:
        g.parse_part = _orig
    # Report the presence of the interesting fields even when never walked, so an
    # absent field is distinguishable from a walk that never reached it.
    for want in FIELDS:
        idxs = [i for i, f in enumerate(s.fields)
                if names.get(f.definition) == want]
        if not idxs:
            continue
        i = idxs[0]
        state = 'PRESENT' if states[i] == 1 else 'absent'
        if state == 'absent':
            print('    %-28s idx=%-3d present=NO' % (want, i))


for label, path, node in TARGETS:
    if path.exists():
        decode(path, node, label)

TAXI = ROOT / 'SharpServer/AreaServer/TaxiNpc.bin'
if TAXI.exists():
    decode(TAXI, 0x1AC7001000, 'taxi (synthetic, ours)')