using System;
using System.IO;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    class CMsgCCACB51D : TORGameClientPacket
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
            AreaPollExperiment.LogPoll(client, "CMsgCCACB51D", _component, _body, "");
            if (client == null)
            {
                AreaPollExperiment.LogDecision(client, "CMsgCCACB51D", "no-client");
                return;
            }
            if (client.AreaServiceID == 0)
            {
                AreaPollExperiment.LogDecision(client, "CMsgCCACB51D", "no-area-service");
                return;
            }

            var mode = AreaPollExperiment.GetMode("CMsgCCACB51D");
            if (mode == AreaPollExperiment.ReplyMode.Echo)
            {
                client.SendPacket(new AreaVectorPollAck(client.AreaServiceID, _body));
                AreaPollExperiment.LogDecision(client, "CMsgCCACB51D", "echo-reply-sent");
            }
            else if (mode == AreaPollExperiment.ReplyMode.Ack)
            {
                client.SendPacket(new AreaVectorPollAck(client.AreaServiceID, new byte[0]));
                AreaPollExperiment.LogDecision(client, "CMsgCCACB51D", "empty-ack-sent");
            }
            else
            {
                AreaPollExperiment.LogDecision(client, "CMsgCCACB51D", "swallowed");
            }
        }

        public override PacketType GetType()
        {
            return PacketType.CMsgCCACB51D;
        }
    }
}
