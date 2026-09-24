using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using ComponentAce.Compression.Libs.zlib;

namespace NexusToRServer
{
    // Serves repository requests from the local SWTOR .tor asset archives.
    //
    // Format (verified against Diagnostics/extract-tor-paths.py, which the asset
    // audit used successfully against Assets2012April):
    //   - 12-byte signature, then a u64 table offset at byte 12.
    //   - Each table: u32 entry count followed by the next u64 table offset,
    //     then entries of 34 bytes each:
    //     u64 dataOffset, u32 headerSize, u32 compressedSize, u32 uncompressedSize,
    //     u64 fileHash, u32 crc32, u16 method (0 = stored, 1 = zlib).
    //   - fileHash is computed from the lower-cased resource path with the
    //     SWTOR path hash (seed 0xDEADBEEF); Hash() below is a literal port of
    //     tor_hash() in extract-tor-paths.py.
    //
    // The index is built once on first use; file data is read on demand.
    static class TorArchive
    {
        private const UInt32 Seed = 0xDEADBEEF;
        private const Int32 ZFinish = 4; // zlib Z_FINISH

        private sealed class Entry
        {
            public string Archive;
            public Int64 DataOffset;
            public UInt32 HeaderSize, CompressedSize, UncompressedSize, Crc, Method;
        }

        private static readonly object Gate = new object();
        private static Dictionary<UInt64, List<Entry>> _index;
        private static int _archiveCount;

        /// <summary>Archive directory: env override, then relative to the exe, then the known absolute location.</summary>
        public static string Root
        {
            get
            {
                string env = Environment.GetEnvironmentVariable("SWTOR_TOR_ARCHIVES");
                if (!String.IsNullOrEmpty(env))
                    return env;
                string relative = Path.GetFullPath(Path.Combine(
                    AppDomain.CurrentDomain.BaseDirectory, @"..\..\..\..\Assets2012April"));
                if (Directory.Exists(relative))
                    return relative;
                return @"D:\SWTORClassic\swtoremu\Assets2012April";
            }
        }

        /// <summary>SWTOR resource path hash; literal port of tor_hash() (seed 0xDEADBEEF).</summary>
        public static UInt64 Hash(string path)
        {
            byte[] data = Encoding.ASCII.GetBytes(path.ToLowerInvariant());
            UInt32 eax = 0, ecx = 0, edx = 0;
            UInt32 ebx = (UInt32)(data.Length + Seed);
            UInt32 edi = ebx, esi = ebx;
            int i = 0;
            while (i + 12 < data.Length)
            {
                edi = (UInt32)(BitConverter.ToUInt32(data, i + 4) + edi);
                esi = (UInt32)(BitConverter.ToUInt32(data, i + 8) + esi);
                edx = (UInt32)(BitConverter.ToUInt32(data, i) - esi);
                edx = (UInt32)((edx + ebx) ^ (esi >> 28) ^ (esi << 4));
                esi += edi;
                edi = (UInt32)((edi - edx) ^ (edx >> 26) ^ (edx << 6));
                edx += esi;
                esi = (UInt32)((esi - edi) ^ (edi >> 24) ^ (edi << 8));
                edi += edx;
                ebx = (UInt32)((edx - esi) ^ (esi >> 16) ^ (esi << 16));
                esi += edi;
                edi = (UInt32)((edi - ebx) ^ (ebx >> 13) ^ (ebx << 19));
                ebx += esi;
                esi = (UInt32)((esi - edi) ^ (edi >> 28) ^ (edi << 4));
                edi += ebx;
                i += 12;
            }
            int tail = data.Length - i;
            if (tail > 0)
            {
                for (int p = 0; p < tail; p++)
                {
                    byte value = data[i + p];
                    if (p < 4) ebx += (UInt32)(value << (8 * p));
                    else if (p < 8) edi += (UInt32)(value << (8 * (p - 4)));
                    else esi += (UInt32)(value << (8 * (p - 8)));
                }
                esi = (UInt32)((esi ^ edi) - ((edi >> 18) ^ (edi << 14)));
                ecx = (UInt32)((esi ^ ebx) - ((esi >> 21) ^ (esi << 11)));
                edi = (UInt32)((edi ^ ecx) - ((ecx >> 7) ^ (ecx << 25)));
                esi = (UInt32)((esi ^ edi) - ((edi >> 16) ^ (edi << 16)));
                edx = (UInt32)((esi ^ ecx) - ((esi >> 28) ^ (esi << 4)));
                edi = (UInt32)((edi ^ edx) - ((edx >> 18) ^ (edx << 14)));
                eax = (UInt32)((esi ^ edi) - ((edi >> 8) ^ (edi << 24)));
            }
            return ((UInt64)edi << 32) | eax;
        }

        /// <summary>
        /// Resolves a resource path against the local archives. Returns true with
        /// data (as stored: zlib-compressed when the entry method is 1), the
        /// declared uncompressed size, and the archive CRC32 of the entry.
        /// </summary>
        public static Boolean TryRead(string path, out byte[] data, out UInt64 uncompressedSize, out UInt32 crc)
        {
            data = null;
            uncompressedSize = 0;
            crc = 0;
            EnsureIndex();
            if (_index == null)
                return false;
            List<Entry> list;
            if (!_index.TryGetValue(Hash(path), out list) || list.Count == 0)
                _index.TryGetValue(Hash("/resources" + path), out list);
            if (list == null || list.Count == 0)
                return false;
            Entry e = list[0];
            try
            {
                using (FileStream fs = File.OpenRead(e.Archive))
                {
                    fs.Seek(e.DataOffset + e.HeaderSize, SeekOrigin.Begin);
                    byte[] stored = new byte[e.Method == 1 ? e.CompressedSize : e.UncompressedSize];
                    int total = 0;
                    while (total < stored.Length)
                    {
                        int n = fs.Read(stored, total, stored.Length - total);
                        if (n <= 0)
                            return false;
                        total += n;
                    }
                    if (e.Method == 1)
                    {
                        byte[] output = new byte[e.UncompressedSize];
                        ZStream zs = new ZStream();
                        if (zs.inflateInit() != 0)
                            return false;
                        zs.next_in = stored;
                        zs.next_in_index = 0;
                        zs.avail_in = stored.Length;
                        zs.next_out = output;
                        zs.next_out_index = 0;
                        zs.avail_out = output.Length;
                        int err = zs.inflate(ZFinish);
                        zs.inflateEnd();
                        if ((err != 0 && err != 1) || zs.total_out != output.Length)
                            return false;
                        data = output;
                    }
                    else
                    {
                        data = stored;
                    }
                }
            }
            catch (Exception)
            {
                data = null;
                return false;
            }
            uncompressedSize = e.UncompressedSize;
            crc = e.Crc;
            return true;
        }

        /// <summary>Diagnostic: reports how far a path lookup gets and why it fails.</summary>
        public static string Probe(string path)
        {
            EnsureIndex();
            if (_index == null)
                return "index=null (archive directory missing?) root=" + Root;
            UInt64 h = Hash(path);
            UInt64 hRes = Hash("/resources" + path);
            List<Entry> list;
            if (!_index.TryGetValue(h, out list))
                _index.TryGetValue(hRes, out list);
            if (list == null || list.Count == 0)
                return String.Format("hash={0:X16} /resources={1:X16} NOT-INDEXED", h, hRes);
            Entry e = list[0];

            string step = String.Format(
                "root={0} archives={1} hashes={2} FOUND in {3} dataOffset={4} hdr={5} c={6} u={7} crc={8:X8} method={9}",
                Root, _archiveCount, _index.Count, Path.GetFileName(e.Archive),
                e.DataOffset, e.HeaderSize, e.CompressedSize, e.UncompressedSize, e.Crc, e.Method);
            try
            {
                byte[] data;
                UInt64 u;
                UInt32 c;
                if (!TryRead(path, out data, out u, out c))
                    return step + " TRYREAD-FALSE";
                return step + String.Format(" OK bytes={0}", data.Length);
            }
            catch (Exception ex)
            {
                return step + " THREW " + ex.GetType().Name + ": " + ex.Message;
            }
        }

        private static void EnsureIndex()
        {
            lock (Gate)
            {
                if (_index != null)
                    return;
                _index = new Dictionary<UInt64, List<Entry>>();
                string root = Root;
                if (!Directory.Exists(root))
                {
                    Log.Write(LogLevel.Error, "TorArchive: archive directory not found: {0}", root);
                    return;
                }
                foreach (string archive in Directory.GetFiles(root, "*.tor"))
                {
                    try
                    {
                        IndexArchive(archive);
                        _archiveCount++;
                    }
                    catch (Exception ex)
                    {
                        Log.Write(LogLevel.Error, "TorArchive: failed to index {0}: {1}", archive, ex.Message);
                    }
                }
                Log.Write(LogLevel.Info, "TorArchive: indexed {0} file hashes from {1} archives in {2}",
                    _index.Count, _archiveCount, root);
            }
        }

        private static void IndexArchive(string path)
        {
            using (FileStream fs = File.OpenRead(path))
            using (BinaryReader r = new BinaryReader(fs))
            {
                r.BaseStream.Seek(12, SeekOrigin.Begin);
                UInt64 tableOffset = r.ReadUInt64();
                while (tableOffset != 0)
                {
                    fs.Seek((Int64)tableOffset, SeekOrigin.Begin);
                    UInt32 count = r.ReadUInt32();
                    tableOffset = r.ReadUInt64();
                                        for (UInt32 n = 0; n < count; n++)
                    {
                        Int64 dataOffset = r.ReadInt64();
                        UInt32 headerSize = r.ReadUInt32();
                        UInt32 compressedSize = r.ReadUInt32();
                        UInt32 uncompressedSize = r.ReadUInt32();
                        UInt64 fileHash = r.ReadUInt64();
                        UInt32 crc = r.ReadUInt32();
                        ushort method = r.ReadUInt16();
                        if (dataOffset == 0)
                            continue;
                        Entry e = new Entry
                        {
                            Archive = path,
                            DataOffset = dataOffset,
                            HeaderSize = headerSize,
                            CompressedSize = compressedSize,
                            UncompressedSize = uncompressedSize,
                            Crc = crc,
                            Method = method
                        };
                        List<Entry> list;
                        if (!_index.TryGetValue(fileHash, out list))
                        {
                            list = new List<Entry>();
                            _index[fileHash] = list;

                        }
                        list.Add(e);
                    }
                }
            }
        }
    }
}
