using System;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Echo reply for the client's CMsg4A765897 client RPC request.
    /// Routing uses the game-systems service pair (server 0x65AC -> client GameSystemsServiceID).
    /// Body is the exact byte blob the client sent after its type/routing header.
    /// </summary>
    class ClientRPCAck : TORGameServerPacket
    {
        private byte _module;
        private UInt16 _clientGameSystemsServiceID;
        private byte[] _body;

        public ClientRPCAck(UInt16 clientGameSystemsServiceID, byte[] body)
        {
            _clientGameSystemsServiceID = clientGameSystemsServiceID;
            _body = body ?? new byte[0];
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            WriteUInt32(((UInt32)0x65AC << 16) | _clientGameSystemsServiceID);
            WriteBytes(_body);
        }

        public override PacketType GetType()
        {
            return PacketType.CMsg4A765897;
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
