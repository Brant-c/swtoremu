using System;

namespace NexusToRServer.NET.Packets.Server
{
    // Native dispatcher64A454 field order;63EF90 recognizes FQN NOT FOUND
    // as FACE000F. This completes a failed request, never claims success.
    class RepositoryDataNotFound : TORGameServerPacket
    {
        private byte _module;
        private readonly UInt32 _component, _requestId;
        private readonly string _path;
        public RepositoryDataNotFound(UInt32 component, UInt32 requestId, string path)
        { _component = component; _requestId = requestId; _path = path; }
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            WriteUInt32((_component << 16) | (_component >> 16));
            WriteUInt32(_requestId);
            WriteString("FQN NOT FOUND");
            WriteString(_path);
            WriteUInt32(0);
            WriteString("");
            WriteString("");
            WriteString("");
            WriteUInt64(0);
            WriteUInt32(0); // Empty byte buffer (97D1D0).
            WriteUInt32(0);
        }
        public override PacketType GetType() { return PacketType.RepositoryDataNotFound; }
        public override void SetModule(byte module) { _module = module; }
        public override byte GetModule() { return _module; }
    }
}
