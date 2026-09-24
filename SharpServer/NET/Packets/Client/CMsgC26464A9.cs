using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    class CMsgC26464A9 : TORGameClientPacket
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
            AreaPollExperiment.LogPoll(client, "CMsgC26464A9", _component, _body, "");
            if (client == null)
            {
                AreaPollExperiment.LogDecision(client, "CMsgC26464A9", "no-client");
                return;
            }

            var mode = AreaPollExperiment.GetMode("CMsgC26464A9");
            if (mode == AreaPollExperiment.ReplyMode.Echo)
            {
                client.SendPacket(new CMsgC26464A9Ack(_component, _body));
                AreaPollExperiment.LogDecision(client, "CMsgC26464A9", "echo-reply-sent");
            }
            else if (mode == AreaPollExperiment.ReplyMode.Ack)
            {
                client.SendPacket(new CMsgC26464A9Ack(_component, new byte[0]));
                AreaPollExperiment.LogDecision(client, "CMsgC26464A9", "empty-ack-sent");
            }
            else
            {
                AreaPollExperiment.LogDecision(client, "CMsgC26464A9", "swallowed");
            }
        }

        public override PacketType GetType()
        {
            return PacketType.CMsgC26464A9;
        }
    }
}
