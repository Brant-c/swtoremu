"""Append run 9 (clone control and single-list merge) to the evidence registry.

Appends only; never rewrites existing rows. Run 9 contains the first POSITIVE
result of the taxi investigation, so the two findings are deliberately split:
the zero-error content result is Behavior-verified, while merge acceptance stays
Hypothesis because the discriminating observation (whether the captured NPCs
survived the merged list) has not been supplied.
"""
import csv
from pathlib import Path

CSV = Path(__file__).resolve().parents[1] / 'Protocol-Evidence.csv'

ROWS = [
    ["n/a", "S2C", "TaxiCloneControlZeroErrors", "Area",
     "AreaAwarenessEntered, one record, 478 bytes, clone of captured record",
     "struct 64, template 0xE0005CB11264F32D, parent 0x1AC688BE1E, node identity only change",
     "Behavior-verified",
     "Diagnostics/Experiments/2026-10-01-04-tython-taxi-npc-and-travel-map.md (run 9a, 23:13); "
     "SharpServer/NET/Packets/Server/AreaTaxiCloneAwareness.cs",
     "POSITIVE and decisive. A generated record at our delivery position produced ZERO "
     "script errors against six in taxi mode, proving the Char spec missing / Mag node / "
     "animation agent failures are caused by the taxi's CONTENT, not by our assembly, "
     "framing or delivery. Taxi tutorial prompt also disappeared, corroborating the "
     "medcenter template was used. First positive result of this investigation."],

    ["n/a", "S2C", "TaxiProblemsAreContentAndOrdering", "Area",
     "conclusion drawn from runs 8a/8b versus 9a/9b",
     "two independent failure axes: taxi content, and delivery ordering",
     "Behavior-verified",
     "Diagnostics/Experiments/2026-10-01-04-tython-taxi-npc-and-travel-map.md (runs 8-9)",
     "Explains why three content experiments produced byte-identical traces. Axis 1 "
     "(content) is closed by the clone control. Axis 2 (ordering) is established from "
     "the run log: set 1 is delivered after our packet (idx 1022 ours, idx 1062 set 1) "
     "and the client never references our node afterwards."],

    ["n/a", "S2C", "MergedAwarenessSingleObjectList", "Area",
     "AreaAwarenessEntered carrying captured set 1 plus one appended record",
     "13960 bytes = captured 13488 + clone record 472; count 77->78",
     "Captured",
     "SharpServer/NET/Packets/Server/AreaMergedAwareness.cs; "
     "Diagnostics/TaxiDevelopment-20261001/Verify-SingleListMerge.py; run 9b server log",
     "Emitted in run 9b with count 77->78 and captured payload verified byte-identical "
     "in memory. Count-byte WIDTH was recovered by probing the decoder rather than "
     "assumed. Zero script errors. Removes the ordering variable: our record now travels "
     "inside the same packet as the 77 captured objects."],

    ["n/a", "S2C", "MergedAwarenessAcceptance", "Area",
     "question: did the client accept the 78-record list and instantiate the clone",
     "distinguishing observation is whether the captured NPCs survived",
     "Hypothesis",
     "Diagnostics/Experiments/2026-10-01-04-tython-taxi-npc-and-travel-map.md (run 9b)",
     "UNRESOLVED. Clone node never referenced by the client and no droid rendered, but "
     "it has NOT been stated whether the medcenter droid, Weller and other working NPCs "
     "survived the merged list. If they survived, the list was accepted and the record is "
     "ignored in-list. If they vanished, the appended record causes wholesale rejection, "
     "matching the reverted merge. Do not infer further without that observation."],

    ["n/a", "S2C", "AwarenessDanglingParentAccepted", "Area",
     "parent reference of a chrNonPlayerCharacter awareness record",
     "parent 0x1AC688BE1E absent from awareness set 1 and set 2",
     "Behavior-verified",
     "Diagnostics/TaxiDevelopment-20261001/Verify-SingleListMerge.py; captured set 1 and 2",
     "Clears a suspected cause of the earlier reverted merge: the CAPTURED medcenter "
     "droid carries the same parent that is absent from set 1, and the client accepts "
     "it. A missing parent is therefore not the hazard."],
]


def main():
    with CSV.open(newline='', encoding='utf-8') as fh:
        header = next(csv.reader(fh))
    assert header[6] == 'Confidence', header
    with CSV.open('a', newline='', encoding='utf-8') as fh:
        for row in ROWS:
            assert len(row) == len(header), (len(row), len(header))
            assert row[6] in ('Captured', 'Client-derived', 'Behavior-verified',
                              'Hypothesis'), row[6]
            csv.writer(fh, quoting=csv.QUOTE_ALL).writerow(row)
    print('appended %d rows to %s' % (len(ROWS), CSV.name))


if __name__ == '__main__':
    main()