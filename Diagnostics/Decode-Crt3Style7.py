"""Read-only token inspection for the Tython CRT3 candidate.

This does not rewrite or enable CRT3. It applies the transport-version 5
primitive rules used by the historical Hero tools and reports every possible
packed integer, float, and terminator boundary. GOM field semantics still
require the owning class schema; this tool intentionally does not guess them.
"""
from pathlib import Path
import struct

ROOT = Path(r"D:\SWTORClassic\swtoremu")
CRT = ROOT / "SharpServer" / "bin" / "Debug" / "AreaServer" / "CRT" / "tython_blockout-4611686019869492753-1.3.acrt"
PAYLOAD_OFFSET = 30


def packed_integer(data, offset):
    token = data[offset]
    if token < 0xC0:
        return token, offset + 1, f"small={token}"
    if not 0xC7 <= token <= 0xCF:
        return None
    length = token - 0xC7
    end = offset + 1 + length
    if end > len(data):
        return None
    value = int.from_bytes(data[offset + 1:end], "big")
    return value, end, f"packed{length}=0x{value:016X}"


def main():
    raw = CRT.read_bytes()
    payload_length = raw[PAYLOAD_OFFSET - 1]
    payload = raw[PAYLOAD_OFFSET:PAYLOAD_OFFSET + payload_length]
    print(f"fixture={CRT}")
    print(f"file_bytes={len(raw)} payload_bytes={len(payload)}")
    print("payload:", payload.hex(" "))
    print("\nprimitive candidates:")

    offset = 0
    while offset < len(payload):
        token = payload[offset]
        packed = packed_integer(payload, offset)
        if packed is not None:
            value, end, description = packed
            print(f"  +{offset:02d}: token=0x{token:02X} {description} next=+{end:02d}")
            offset = end
            continue

        if token == 0xD3:
            print(f"  +{offset:02d}: end-token 0xD3")
            offset += 1
            continue

        if offset + 4 <= len(payload):
            value = struct.unpack_from("<f", payload, offset)[0]
            print(f"  +{offset:02d}: raw-float={value!r} bytes={payload[offset:offset + 4].hex(' ')}")
        else:
            print(f"  +{offset:02d}: trailing bytes={payload[offset:].hex(' ')}")
        offset += 1

    print("\nKnown CRT3 observations:")
    print("  expected stream sequence is 0x001B5014")
    print("  current payload ends with class id 0x4000010E218A839C plus token 0x%02X" % payload[-1])
    print("  no field meaning is inferred by this diagnostic")


if __name__ == "__main__":
    main()
