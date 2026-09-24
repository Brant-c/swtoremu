r'''Rewrite CMsgF96DCDB0.cs deterministically (clean line endings, RpcReply-based
reply with mirror/results/echo/swallow/ack modes).'''
import io

PATH = r'D:\SWTORClassic\swtoremu\SharpServer\NET\Packets\Client\CMsgF96DCDB0.cs'

CONTENT = '''\ufeffusing System;
using System.IO;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    class CMsgF96DCDB0 : TORGameClientPacket
    {
        private UInt32 _component;
        private byte[] _body;

        public override void ReadImplementation()
        {
            ReadUInt32();
            _component = ReadUInt32();
            int remaining = (int)(_stream.Length - _stream.Position);
            _body = remaining > 0 ? ReadBytes(remaining) : new byte[0];
        }

        public override void RunImplementation()
        {
            TORGameClient client = GetClient();
            string sub = (_body != null && _body.Length > 0) ? _body[0].ToString("X2") : "??";
            bool tail = _body != null && _body.Length >= 4 && _body[_body.Length-4]==0x74 && _body[_body.Length-3]==0x72 && _body[_body.Length-2]==0x75 && _body[_body.Length-1]==0x65;
            AreaPollExperiment.LogPoll(client, "CMsgF96DCDB0", _component, _body, "sub=" + sub + " trueTail=" + tail);
            if (client == null)
            {
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "no-client");
                return;
            }
            if (client.AreaServiceID == 0)
            {
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "no-area-service");
                return;
            }

            // The client's own script RPC request. Body = [Int32 len][name bytes]
            // (+ args); the reference server reads it as count+bytes. Answer with
            // SMSG_RESULTS (0xD5280283) so the pending script call can complete.
            var mode = RpcReply.GetMode();
            if (mode == RpcReply.Mode.Mirror || mode == RpcReply.Mode.Results)
            {
                RpcReply.SendResults(client, 0x65B3, client.AreaServiceID, "CMsgF96DCDB0", _body);
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "sms-results-sent");
            }
            else if (mode == RpcReply.Mode.Echo)
            {
                client.SendPacket(new AreaRPCPollAck(client.AreaServiceID, _body));
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "echo-reply-sent");
            }
            else if (mode == RpcReply.Mode.Ack)
            {
                client.SendPacket(new AreaRPCPollAck(client.AreaServiceID, new byte[0]));
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "empty-ack-sent");
            }
            else
            {
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "swallowed");
            }
        }

        public override PacketType GetType()
        {
            return PacketType.CMsgF96DCDB0;
        }
    }
}
'''

io.open(PATH, 'w', encoding='utf-8', newline='\n').write(CONTENT)
print('rewrote CMsgF96DCDB0.cs (%d chars)' % len(CONTENT))
