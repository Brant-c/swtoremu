using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    class CMsg7CB9A193 : TORGameClientPacket
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
            AreaPollExperiment.LogPoll(client, "CMsg7CB9A193", _component, _body, "");
            if (client == null)
            {
                AreaPollExperiment.LogDecision(client, "CMsg7CB9A193", "no-client");
                return;
            }

            var mode = AreaPollExperiment.GetMode("CMsg7CB9A193");
            if (mode == AreaPollExperiment.ReplyMode.Echo)
            {
                client.SendPacket(new CMsg7CB9A193Ack(_component, _body));
                AreaPollExperiment.LogDecision(client, "CMsg7CB9A193", "echo-reply-sent");
            }
            else if (mode == AreaPollExperiment.ReplyMode.Ack)
            {
                client.SendPacket(new CMsg7CB9A193Ack(_component, new byte[0]));
                AreaPollExperiment.LogDecision(client, "CMsg7CB9A193", "empty-ack-sent");
            }
            else
            {
                AreaPollExperiment.LogDecision(client, "CMsg7CB9A193", "swallowed");
            }
        }

        public override PacketType GetType()
        {
            return PacketType.CMsg7CB9A193;
        }
    }
}
