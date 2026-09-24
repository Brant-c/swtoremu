using System;

namespace NexusToRServer.NET.Packets.Server
{
    // Success variant of the resource reply. Same wire message as
    // RepositoryDataNotFound (opcode 2F7A6A25); per
    // Diagnostics/Repository-Protocol-Findings.md the payload after opcode and
    // component is: uint32 ID, error string, path string, uint32, three
    // strings, uint64, length-prefixed byte buffer, uint32.
    //
    // The client's reply decoder (0064A454) passes the error string to handler
    // 0063EF90, which defaults to native status 1 and only returns FACE000F
    // when the string does not match the empty-string constant. An EMPTY error
    // string therefore takes the success path; "FQN NOT FOUND" takes the
    // not-found path. The buffer is served exactly as stored in the .tor
    // archive (zlib for method 1) for the native Repository Decompression
    // Thread, with the archive's declared uncompressed size as the uint64 and
    // the archive CRC32 as the trailing uint32.
    class RepositoryDataReply : TORGameServerPacket
    {
        private byte _module;
        private readonly UInt32 _component, _requestId, _crc;
        private readonly string _path;
        private readonly byte[] _data;
        private readonly UInt64 _uncompressedSize;

        public RepositoryDataReply(UInt32 component, UInt32 requestId, string path,
                                   byte[] data, UInt64 uncompressedSize, UInt32 crc)
        {
            _component = component;
            _requestId = requestId;
            _path = path;
            _data = data;
            _uncompressedSize = uncompressedSize;
            _crc = crc;
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            WriteUInt32((_component << 16) | (_component >> 16));
            WriteUInt32(_requestId);
            WriteString("");                    // empty error string = success
            WriteString(_path);
            WriteUInt32(0);
            WriteString("");
            WriteString("");
            WriteString("");
            WriteUInt64(_uncompressedSize);
            WriteUInt32((UInt32)_data.Length);
            WriteBytes(_data);
            WriteUInt32(_crc);
        }

        // Deliberately the same PacketType as the failure reply: it is the same
        // wire message; the client distinguishes the two by the error string.
        public override PacketType GetType() { return PacketType.RepositoryDataNotFound; }
        public override void SetModule(byte module) { _module = module; }
        public override byte GetModule() { return _module; }
    }
}
