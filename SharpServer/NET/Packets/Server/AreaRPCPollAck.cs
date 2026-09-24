using System;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Echo reply for the client's CMsgF96DCDB0 area RPC request.
    /// Routing uses the area-service pair (server 0x65B3 -> client AreaServiceID),
    /// matching the routing on the incoming request.
    /// Body is the exact byte blob the client sent after its type/routing header.
    /// NOTE: the incoming body is [length:4 LE][RPC blob] — the client's own
    /// script RPC call in the same wire shape the server uses for
    /// AreaRequestRPC. Echo/swallow/ack were all tested equivalent client-side,
    /// so this reply is non-canonical; keep for parity with AreaPollExperiment.
    /// </summary>
    class AreaRPCPollAck : TORGameServerPacket
    {
        private byte _module;
        private UInt16 _clientAreaServiceID;
        private byte[] _body;

        public AreaRPCPollAck(UInt16 clientAreaServiceID, byte[] body)
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
            return PacketType.CMsgF96DCDB0;
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
