using System;
using System.IO;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    class AreaModulesList : TORGameClientPacket
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
            AreaPollExperiment.LogPoll(client, "AreaModulesList", _component, _body, "");
            if (client == null)
            {
                AreaPollExperiment.LogDecision(client, "AreaModulesList", "no-client");
                return;
            }
            if (client.AreaServiceID == 0)
            {
                AreaPollExperiment.LogDecision(client, "AreaModulesList", "no-area-service");
                return;
            }

            var mode = AreaPollExperiment.GetMode("AreaModulesList");
            if (mode == AreaPollExperiment.ReplyMode.Echo)
            {
                client.SendPacket(new AreaModulesListAck(client.AreaServiceID, _body));
                AreaPollExperiment.LogDecision(client, "AreaModulesList", "echo-reply-sent");
            }
            else if (mode == AreaPollExperiment.ReplyMode.Ack)
            {
                client.SendPacket(new AreaModulesListAck(client.AreaServiceID, new byte[0]));
                AreaPollExperiment.LogDecision(client, "AreaModulesList", "empty-ack-sent");
            }
            else
            {
                AreaPollExperiment.LogDecision(client, "AreaModulesList", "swallowed");
            }

            if (!client.AreaStartupPacketsSent)
            {
                client.AreaStartupPacketsSent = true;
                AreaStartupBundle.Send(client);
                Log.Write(LogLevel.Client, "AreaModulesList: startup bundle sent (startupSent={0}).", client.AreaStartupPacketsSent);
            }
            else
            {
                Log.Write(LogLevel.Client, "AreaModulesList: startup bundle already sent; skipped.");
            }
        }

        public override PacketType GetType()
        {
            return PacketType.AreaModulesList;
        }
    }
}
