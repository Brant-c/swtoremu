using System;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Echo reply for the client's AreaModulesList poll.
    /// Routing uses the area-service pair (server 0x65B3 -> client AreaServiceID),
    /// matching the routing on the incoming poll.
    /// Body is the exact byte blob the client sent after its type/routing header.
    /// </summary>
    class AreaModulesListAck : TORGameServerPacket
    {
        private byte _module;
        private UInt16 _clientAreaServiceID;
        private byte[] _body;

        public AreaModulesListAck(UInt16 clientAreaServiceID, byte[] body)
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
            return PacketType.AreaModulesList;
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
