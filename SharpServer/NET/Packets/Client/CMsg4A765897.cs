using System;
using System.IO;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    // Client->server RPC request on the game-systems service (routing
    // 0x65AC0009). Body after the 8-byte transport header is
    // [length:4 LE][RPC blob] — the same wire shape as the server's own
    // AreaRequestRPC payload, i.e. these are the client's own script RPC calls
    // (NOT responses to server RPCs; there is no RPC id field — the leading
    // u32 is a byte length). Observed bodies: 09 00 00 00 CF 6F 6F 2E 93 B7 43 63 6C,
    // 09 00 00 00 C7 71 C3 79 12 43 35 7C 7C.
    // The client does not appear to gate on a reply (echo/swallow tested
    // equivalent), so the echo below is non-canonical but harmless.
    class CMsg4A765897 : TORGameClientPacket
    {
        private byte[] _body;

        public override void ReadImplementation()
        {
            // Read the 8-byte transport header (type + routing).
            ReadUInt32(); // packet type
            ReadUInt32(); // routing/component
            // Remaining bytes are the body.
            int remaining = (int)(_stream.Length - _stream.Position);
            _body = remaining > 0 ? ReadBytes(remaining) : new byte[0];
        }

        public override void RunImplementation()
        {
            TORGameClient client = GetClient();
            string hex = _body == null ? "(null)" : BitConverter.ToString(_body);
            if (client == null)
            {
                Log.Write(LogLevel.Warning, "CMsg4A765897: no client; rpc dropped. hex={0}", hex);
                return;
            }
            if (client.GameSystemsServiceID == 0)
            {
                Log.Write(LogLevel.Client, "CMsg4A765897: client rpc received (body {0} bytes), game-systems service not attached, no reply. hex={1}", _body == null ? 0 : _body.Length, hex);
                return;
            }

            var mode = RpcReply.GetMode();
            if (mode == RpcReply.Mode.Mirror || mode == RpcReply.Mode.Results)
            {
                RpcReply.SendResults(client, 0x65AC, client.GameSystemsServiceID, "CMsg4A765897", _body);
                Log.Write(LogLevel.Client,
                    "CMsg4A765897: client rpc received (body {0} bytes), SMSG_RESULTS sent. gameSysSvc=0x{1:X4} hex={2}",
                    _body == null ? 0 : _body.Length, client.GameSystemsServiceID, hex);
                return;
            }
            if (mode == RpcReply.Mode.Swallow)
            {
                Log.Write(LogLevel.Client, "CMsg4A765897: client rpc received (body {0} bytes), swallowed. hex={1}",
                    _body == null ? 0 : _body.Length, hex);
                return;
            }

            client.SendPacket(new ClientRPCAck(client.GameSystemsServiceID, mode == RpcReply.Mode.Ack ? new byte[0] : _body));
            Log.Write(LogLevel.Client,
                "CMsg4A765897: client rpc received (body {0} bytes), echo-reply sent. gameSysSvc=0x{1:X4} hex={2}",
                _body == null ? 0 : _body.Length, client.GameSystemsServiceID, hex);
        }

        public override PacketType GetType()
        {
            return PacketType.CMsg4A765897;
        }
    }
}
