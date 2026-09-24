using System;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Echo reply for the client's CMsg61116AD5 character sync
    /// (CMSG_CHARACTER_SYNC). The client sends it once, right after the area
    /// service attach, carrying the applied placement (rotation + position) and
    /// the last replication stream ID it received. It was previously left
    /// unanswered, which left the entry handshake incomplete.
    /// </summary>
    class CMsg61116AD5Ack : TORGameServerPacket
    {
        private byte _module;
        private UInt32 _component;
        private byte[] _body;

        public CMsg61116AD5Ack(UInt32 component, byte[] body)
        {
            _component = component;
            _body = body ?? new byte[0];
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            WriteUInt32(_component);
            WriteBytes(_body);
        }

        public override PacketType GetType()
        {
            return PacketType.CMsg61116AD5;
        }

        public override void SetModule(byte inMod)
        {
            _module = inMod;
        }

        public override byte GetModule()
        {
            return _module;
        }
    }
}
