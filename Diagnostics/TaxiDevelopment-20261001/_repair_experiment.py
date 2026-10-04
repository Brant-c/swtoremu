"""Repair: move the accidentally-prepended block into its own experiment file.

The block was written into the authoritative record's title slot. This puts the
original title back exactly and preserves the new text as a separate experiment
record, per the one-record-per-run policy. Nothing is discarded.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent / 'Experiments'
src = EXP / '2026-10-02-05-taxi-wire-surface-and-precreate-spec.md'
dst = EXP / '2026-10-02-06-taxi-merged-list-acceptance.md'
TITLE = ('# Taxi record: definitive finding — the payload was never the '
         'problem')

lines = src.read_text(encoding='utf-8').splitlines()
assert lines[0].startswith('# Taxi NPC next run'), lines[0]
assert lines[98].startswith('Date: 2026-10-02. Confidence: **Client-derived**'), \
    lines[98]

block = lines[0:97]
if not dst.exists():
    dst.write_text('\n'.join(block) + '\n', encoding='utf-8')

restored = [TITLE] + lines[97:]
src.write_text('\n'.join(restored) + '\n', encoding='utf-8')

print('restored title :', restored[0])
print('restored line 2:', repr(restored[1]))
print('restored line 3:', restored[2][:60])
print('total lines    :', len(restored))
print('new experiment :', dst.name, len(block), 'lines')