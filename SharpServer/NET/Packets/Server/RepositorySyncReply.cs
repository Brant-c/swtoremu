using System;

namespace NexusToRServer.NET.Packets.Server
{
    // April client dispatch64A67C reads one terminated byte string, then
    // calls63F810. Empty error text invokes the registered sync callback(1).
    class RepositorySyncReply : TORGameServerPacket
    {
        private byte _module;
        private readonly UInt16 _serviceID;
        public RepositorySyncReply(UInt16 serviceID) { _serviceID = serviceID; }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            // Sender must match RepositoryServer's SignatureResponse handle.
            // Native9EE9FB indexes the route by BOTH 16-bit handles.
            WriteUInt32(((UInt32)_serviceID << 16) | 0x65A8);
            WriteString("");
        }

        public override PacketType GetType() { return PacketType.RepositorySyncReply; }
        public override void SetModule(byte module) { _module = module; }
        public override byte GetModule() { return _module; }
    }
}
