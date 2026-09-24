using System;
using System.IO;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    class CMsg61116AD5 : TORGameClientPacket
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
            string opcode = "CMsg61116AD5";
            AreaPollExperiment.LogPoll(client, opcode, _component, _body, "");
            if (client == null)
            {
                AreaPollExperiment.LogDecision(client, opcode, "no-client");
                return;
            }

            var mode = AreaPollExperiment.GetMode(opcode);
            if (mode == AreaPollExperiment.ReplyMode.Echo)
            {
                client.SendPacket(new CMsg61116AD5Ack(_component, _body));
                AreaPollExperiment.LogDecision(client, opcode, "echo-reply-sent");
            }
            else if (mode == AreaPollExperiment.ReplyMode.Ack)
            {
                client.SendPacket(new CMsg61116AD5Ack(_component, new byte[0]));
                AreaPollExperiment.LogDecision(client, opcode, "empty-ack-sent");
            }
            else
            {
                AreaPollExperiment.LogDecision(client, opcode, "swallowed");
            }

            if (mode == AreaPollExperiment.ReplyMode.Echo)
                AreaEnterSignals.Fire(client);

        }

        public override PacketType GetType()
        {
            return PacketType.CMsg61116AD5;
        }
    }
}