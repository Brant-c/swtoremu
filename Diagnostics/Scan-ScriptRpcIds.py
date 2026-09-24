"""Search SWTOR v5 SCPT payloads for numeric RPC/call identifiers.

This is deliberately read-only.  It reuses the v5 container rules implemented
by Tools/SCPTExtractor, searches both byte orders, and prints nearby printable
strings so a raw hit can be assigned to a script vocabulary/context.

Usage:
    py Diagnostics/Scan-ScriptRpcIds.py 0x1279C371
    py Diagnostics/Scan-ScriptRpcIds.py 0x1279C371 0x654BE507
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "Diagnostics" / "Scripts2012"


def decode_v5_scpt(path: Path) -> bytes:
    data = path.read_bytes()
    if len(data) < 37 or data[:8] != b"SCPT\x05\x00\x05\x00":
        raise ValueError("not a v5 SCPT container")

    encrypted = data[24] != 0
    size = struct.unpack_from("<I", data, 33)[0]
    payload = data[37 : 37 + size]
    if len(payload) != size:
        raise ValueError(f"truncated payload: expected {size}, got {len(payload)}")
    if encrypted:
        payload = bytes(value ^ ((0x35 + index * 0x36) & 0xFF)
                        for index, value in enumerate(payload))
    return payload


def printable_runs(data: bytes, minimum: int = 4) -> list[tuple[int, int, str]]:
    runs: list[tuple[int, int, str]] = []
    start = None
    for index, value in enumerate(data + b"\x00"):
        printable = 0x20 <= value <= 0x7E or value in (0x09, 0x0A, 0x0D)
        if printable and start is None:
            start = index
        elif not printable and start is not None:
            if index - start >= minimum:
                text = data[start:index].decode("ascii", errors="replace")
                runs.append((start, index, text.replace("\r", "\\r").replace("\n", "\\n")))
            start = None
    return runs


def context_strings(runs: list[tuple[int, int, str]], offset: int,
                    radius: int = 192, limit: int = 8) -> list[str]:
    ranked = []
    for start, end, text in runs:
        distance = min(abs(offset - start), abs(offset - end))
        if start - radius <= offset <= end + radius:
            ranked.append((distance, start, text))
    ranked.sort()
    return [text for _, _, text in ranked[:limit]]


def find_all(data: bytes, needle: bytes) -> list[int]:
    offsets = []
    cursor = 0
    while True:
        cursor = data.find(needle, cursor)
        if cursor < 0:
            return offsets
        offsets.append(cursor)
        cursor += 1


def parse_target(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFFFFFFFF:
        raise argparse.ArgumentTypeError("target must fit in an unsigned 32-bit value")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="+", type=parse_target)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    targets = {
        target: {
            "little": struct.pack("<I", target),
            "big": struct.pack(">I", target),
        }
        for target in args.targets
    }
    results = []
    scanned = 0
    rejected = 0

    for path in sorted(args.input.glob("*.scpt")):
        try:
            payload = decode_v5_scpt(path)
        except ValueError:
            rejected += 1
            continue
        scanned += 1
        runs = printable_runs(payload)
        for target, encodings in targets.items():
            for byte_order, needle in encodings.items():
                for offset in find_all(payload, needle):
                    results.append({
                        "file": path.name,
                        "target": f"0x{target:08X}",
                        "byte_order": byte_order,
                        "offset": f"0x{offset:X}",
                        "context": context_strings(runs, offset),
                    })

    summary = {
        "input": str(args.input),
        "scanned_v5_scripts": scanned,
        "rejected_non_v5_scripts": rejected,
        "targets": [f"0x{target:08X}" for target in args.targets],
        "hits": results,
    }
    if args.as_json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Scanned {scanned} v5 SCPT files ({rejected} non-v5/rejected).")
        print("Targets: " + ", ".join(summary["targets"]))
        if not results:
            print("No exact 32-bit references found in either byte order.")
        for hit in results:
            print(f"{hit['file']} {hit['target']} {hit['byte_order']} @ {hit['offset']}")
            for value in hit["context"]:
                print(f"  {value[:180]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
