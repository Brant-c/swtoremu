using System;
using System.IO;
using NexusToRServer.AreaServer;
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

            // Diagnostic: re-emit the captured phase-instance transaction later
            // in the session so phsPhasedInstance.OnReplicationNodeCreate runs
            // again after the room is fully loaded. Disabled by default.
            PhaseInstanceRetry.Tick(client);

            // This message is the client's move state. Its body is
            // [u32 0xC5][f32 heading][f32 x][f32 y][f32 z][...] with x/y/z at
            // offsets 8/12/16. Feed the position to the phase-exit tracker so a
            // walk out of the Masters' Retreat doorway triggers the server-side
            // exit (destroy of the phsPhaseInfo child).
            if (_body != null && _body.Length >= 20 && _body[0] == 0xC5)
            {
                float x = BitConverter.ToSingle(_body, 8);
                float y = BitConverter.ToSingle(_body, 12);
                float z = BitConverter.ToSingle(_body, 16);
                PhaseExit.OnMove(client, x, y, z);
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