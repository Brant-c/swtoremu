import argparse
import pathlib
import struct
import zlib


MASK = 0xFFFFFFFF


def u32(value):
    return value & MASK


def tor_hash(path, seed=0xDEADBEEF):
    data = path.lower().encode("ascii")
    eax = ecx = edx = 0
    ebx = edi = esi = u32(len(data) + seed)
    i = 0
    while i + 12 < len(data):
        edi = u32(int.from_bytes(data[i + 4:i + 8], "little") + edi)
        esi = u32(int.from_bytes(data[i + 8:i + 12], "little") + esi)
        edx = u32(int.from_bytes(data[i:i + 4], "little") - esi)
        edx = u32((edx + ebx) ^ (esi >> 28) ^ u32(esi << 4))
        esi = u32(esi + edi)
        edi = u32((edi - edx) ^ (edx >> 26) ^ u32(edx << 6))
        edx = u32(edx + esi)
        esi = u32((esi - edi) ^ (edi >> 24) ^ u32(edi << 8))
        edi = u32(edi + edx)
        ebx = u32((edx - esi) ^ (esi >> 16) ^ u32(esi << 16))
        esi = u32(esi + edi)
        edi = u32((edi - ebx) ^ (ebx >> 13) ^ u32(ebx << 19))
        ebx = u32(ebx + esi)
        esi = u32((esi - edi) ^ (edi >> 28) ^ u32(edi << 4))
        edi = u32(edi + ebx)
        i += 12

    tail = data[i:]
    if tail:
        for position, value in enumerate(tail):
            if position < 4:
                ebx = u32(ebx + (value << (8 * position)))
            elif position < 8:
                edi = u32(edi + (value << (8 * (position - 4))))
            else:
                esi = u32(esi + (value << (8 * (position - 8))))
        esi = u32((esi ^ edi) - ((edi >> 18) ^ u32(edi << 14)))
        ecx = u32((esi ^ ebx) - ((esi >> 21) ^ u32(esi << 11)))
        edi = u32((edi ^ ecx) - ((ecx >> 7) ^ u32(ecx << 25)))
        esi = u32((esi ^ edi) - ((edi >> 16) ^ u32(edi << 16)))
        edx = u32((esi ^ ecx) - ((esi >> 28) ^ u32(esi << 4)))
        edi = u32((edi ^ edx) - ((edx >> 18) ^ u32(edx << 14)))
        eax = u32((esi ^ edi) - ((edi >> 8) ^ u32(edi << 24)))
        return (edi << 32) | eax
    return (esi << 32) | eax


def archive_entries(stream):
    stream.seek(12)
    table_offset = struct.unpack("<Q", stream.read(8))[0]
    while table_offset:
        stream.seek(table_offset)
        count, table_offset = struct.unpack("<IQ", stream.read(12))
        for _ in range(count):
            yield struct.unpack("<QIIIQIH", stream.read(34))


def read_archive(path):
    result = {}
    with path.open("rb") as stream:
        for entry in archive_entries(stream):
            data_offset, header_size, compressed_size, uncompressed_size, file_hash, crc, method = entry
            if not data_offset:
                continue
            resume = stream.tell()
            stream.seek(data_offset + header_size)
            payload = stream.read(compressed_size if method == 1 else uncompressed_size)
            if method == 1:
                payload = zlib.decompress(payload)
            elif method != 0:
                raise ValueError(f"Unknown compression method {method}")
            result[file_hash] = payload
            stream.seek(resume)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    entries = read_archive(args.archive)
    for requested_path in args.paths:
        key = tor_hash(requested_path)
        payload = entries.get(key)
        print(f"{requested_path} hash={key:016X} size={len(payload) if payload is not None else 'missing'}")
        if payload is not None:
            destination = args.output / requested_path.lstrip("/").replace("/", pathlib.os.sep)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
