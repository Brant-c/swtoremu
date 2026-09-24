import argparse
import pathlib
import struct
import zlib


def entries(path):
    with path.open("rb") as stream:
        header = stream.read(0x100)
        table_offset = struct.unpack_from("<q", header, 12)[0]
        while table_offset:
            stream.seek(table_offset)
            count, next_table = struct.unpack("<iq", stream.read(12))
            table = stream.read(count * 0x22)
            for index in range(count):
                offset = index * 0x22
                yield struct.unpack_from("<qiiiQIH", table, offset)
            table_offset = next_table


def scan(path, output):
    found = 0
    failed = 0
    with path.open("rb") as stream:
        for data_offset, header_size, compressed_size, uncompressed_size, file_hash, crc, method in entries(path):
            stream.seek(data_offset + header_size)
            payload = stream.read(compressed_size if method == 1 else uncompressed_size)
            try:
                if method == 1:
                    payload = zlib.decompress(payload)
            except zlib.error:
                failed += 1
                continue
            if payload[:4] == b"SCPT":
                output.mkdir(parents=True, exist_ok=True)
                (output / f"{file_hash:016X}.scpt").write_bytes(payload)
                found += 1
    print(f"{path.name}: scripts={found} decompression_failures={failed}")


parser = argparse.ArgumentParser()
parser.add_argument("output", type=pathlib.Path)
parser.add_argument("archives", nargs="+", type=pathlib.Path)
args = parser.parse_args()
for archive in args.archives:
    scan(archive, args.output)
