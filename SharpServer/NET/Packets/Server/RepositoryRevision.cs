using System;

namespace NexusToRServer.NET.Packets.Server
{
    // Native64B10D ->63F700: NotifyDatabaseImportVersion(string).
    // Revision1 identifies this fixed local repository, not a retail timestamp.
    class RepositoryRevision : TORGameServerPacket
    {
        private byte _module;
        private readonly UInt16 _serviceID;
        public RepositoryRevision(UInt16 serviceID) { _serviceID = serviceID; }
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            WriteUInt32(((UInt32)_serviceID << 16) | 0x65A8);
            WriteString("1");
        }
        public override PacketType GetType() { return PacketType.RepositoryRevision; }
        public override void SetModule(byte module) { _module = module; }
        public override byte GetModule() { return _module; }
    }
}
