using System;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Echo reply for the client's CMsgCCACB51D area vector poll.
    /// Routing uses the area-service pair (server 0x65B3 -> client AreaServiceID).
    /// Body is the exact byte blob the client sent after its type/routing header.
    /// </summary>
    class AreaVectorPollAck : TORGameServerPacket
    {
        private byte _module;
        private UInt16 _clientAreaServiceID;
        private byte[] _body;

        public AreaVectorPollAck(UInt16 clientAreaServiceID, byte[] body)
        {
            _clientAreaServiceID = clientAreaServiceID;
            _body = body ?? new byte[0];
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            WriteUInt32(((UInt32)0x65B3 << 16) | _clientAreaServiceID);
            WriteBytes(_body);
        }

        public override PacketType GetType()
        {
            return PacketType.CMsgCCACB51D;
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
