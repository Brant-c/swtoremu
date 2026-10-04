#!/usr/bin/env python3
"""Append run-8 taxi results to the protocol evidence registry.

Usage: python Record-Run8Evidence.py
Appends only; never rewrites existing rows. Each row carries exactly one primary
confidence level per the evidence policy, and the negative results are recorded as
explicitly as the positive ones so a future run does not re-test them blind.
"""
import csv
from pathlib import Path

CSV = Path(__file__).resolve().parents[1] / 'Protocol-Evidence.csv'

ROWS = [
    ["n/a", "S2C", "TaxiAwarenessRecord", "Area",
     "AreaAwarenessEntered (A1D9E226) object list, 5 records, 677 bytes",
     "struct 66 chrNonPlayerCharacter + taxTerminalComponent; 31/95 fields transmitted",
     "Captured",
     "SharpServer/NET/Packets/Server/AreaTaxiAwareness.cs; "
     "Diagnostics/TaxiDevelopment-20261001/Verify-TaxiFixture.py; "
     "Diagnostics/TaxiDevelopment-20261001/Verify-RunFixture.py",
     "Record framing, offsets and delivery verified. Node substitution replayed to "
     "the exact logged sha256, proving the client received this fixture and not a "
     "stale build."],

    ["n/a", "S2C", "TaxiCharacterSpecificationSelfReference", "Area",
     "field-level claim inside the taxi awareness record",
     "struct-64 field 78 / struct-66 field 77 _characterSpecification",
     "Behavior-verified",
     "Diagnostics/Experiments/2026-10-01-04-tython-taxi-npc-and-travel-map.md "
     "(run 8a, 2026-10-01 21:48)",
     "NEGATIVE. Replacing the donor capture-time hash 0x5541E56931B58335 with the "
     "taxi prototype's own spec 0xE0008B8CC0FAEA1D produced byte-identical script "
     "errors, so the field is not the lever. Do not re-test without new evidence."],

    ["n/a", "S2C", "TaxiStaEnterIdlePresenceBit", "Area",
     "single presence bit in the style-8 field-state run",
     "struct-66 field 37 staEnterIdle, Boolean, zero-length value",
     "Behavior-verified",
     "Diagnostics/Experiments/2026-10-01-04-tython-taxi-npc-and-travel-map.md "
     "(run 8b, 2026-10-01 22:03)",
     "NEGATIVE. Chosen because it was the only field the taxi lacked that Weller "
     "carries, and Weller's lone CRT12 contract transmits exactly it. Identical "
     "traces prove the field was never read on the failing path."],

    ["n/a", "S2C", "TaxiClassChainResolution", "Area",
     "client-side object construction, observed in the script-error trace",
     "chrNonPlayerCharacter + aiCharacterAgentOverrideComponent + "
     "spnSpawnedComponent + brkOwnerComponent + taxTerminalComponent",
     "Behavior-verified",
     "Diagnostics/Experiments/2026-10-01-04-tython-taxi-npc-and-travel-map.md "
     "(run 8 traces)",
     "POSITIVE. The client builds exactly struct 66's additional_classes from "
     "template 0xE0008B8CC0FAEA1D. Template and structure selection are correct, "
     "which removes the wrong-template/wrong-class family of hypotheses."],

    ["n/a", "S2C", "TaxiAwarenessOrderingVsCapturedSet", "Area",
     "sequence of AreaAwarenessEntered packets in the startup bundle",
     "taxi 5-object packet, then CRT 13, then captured awareness set 1 (77 objects)",
     "Captured",
     "SharpServer/bin/Debug/NexusToR.log lines 1004-1008 (2026-10-01 22:03:44)",
     "Awareness set 1 lands AFTER the taxi. Under the run-7 replacement-semantics "
     "hypothesis this suppresses the taxi regardless of record content, so a "
     "correct record and a wrong record currently look identical. Must be decoupled "
     "from content experiments."],

    ["n/a", "S2C", "TaxiVendorVsTaxTerminalComponent", "Area",
     "additional_classes list written explicitly by the generator",
     "struct 64 vndVendorComponent vs struct 66 taxTerminalComponent",
     "Captured",
     "Diagnostics/Decode-Style7Replication.py schema; "
     "SharpServer/AreaServer/TaxiNpc.bin; "
     "Diagnostics/Experiments/2026-10-01-04-tython-taxi-npc-and-travel-map.md",
     "The captured medcenter droid, which renders a model, is struct 64 with "
     "vndVendorComponent; the taxi is struct 66 with taxTerminalComponent. Three of "
     "four classes are identical. Untested and currently confounded by ordering."],

    ["0x61116AD5", "S2C", "WellerNpcReplicationContract", "Area",
     "AreaClientReplicationTransaction, 26 bytes, 1 contract",
     "node 0x1AC6F6DC6D, struct 62, value size 6, inner size 0, body cc 37 35 80",
     "Hypothesis",
     "Diagnostics/TaxiDevelopment-20261001/Dump-Crt12Contract.py; "
     "Diagnostics/TaxiDevelopment-20261001/Survey-CrtContracts.py",
     "The only captured contract targeting a known NPC, and Weller is the only "
     "working NPC. Body is NOT decoded: value size 6 with inner size 0 is not a "
     "normal field run, and cc 37 35 80 does not parse as a packed value. n=1. "
     "Survey shows 110 contracts across 16 CRTs, only one of them NPC-targeted."],

    ["n/a", "S2C", "CrtOverrideDirectoryActive", "Area",
     "SWTOR_CRT_OVERRIDE_DIRECTORY replaces captured .acrt fixtures",
     "CRT 1 57382->57636 bytes; CRT 4 1833->1785 bytes",
     "Captured",
     "SharpServer/AreaServer/CRT.cs:24; SharpServer/bin/Debug/NexusToR.log "
     "lines 982 and 1025",
     "Env-gated and intentional, but it means run 8 was not a clean captured "
     "baseline: the taxi test ran on top of the phase-exit CRT candidates."],
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