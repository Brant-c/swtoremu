using System;
using System.IO;
using NexusToRServer.AreaServer;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;
using NexusToRServer.NET.Protocol;

namespace NexusToRServer.NET.Packets.Client
{
    class CMsg61116AD5 : TORGameClientPacket
    {
        private UInt32 _component;
        private byte[] _body;
        private float _heading, _x, _y, _z;
        private byte[] _opaqueTail;

        public override void ReadImplementation()
        {
            var cursor = new PacketCursor(_buffer);
            uint opcode, variant;
            if (!cursor.TryReadUInt32(out opcode)) throw cursor.Error();
            if (opcode != (uint)PacketType.CMsg61116AD5)
            { cursor.Reject(0, "unexpected movement opcode"); throw cursor.Error(); }
            if (!cursor.TryReadUInt32(out _component) || !cursor.TryReadUInt32(out variant)) throw cursor.Error();
            if (variant != 0xC5)
            { cursor.Reject(8, "unsupported movement variant 0x" + variant.ToString("X8")); throw cursor.Error(); }
            // Captured: 36-byte C5 body, including 16 opaque trailing bytes.
            // Evidence: Diagnostics/DecoderBaseline-20260930/movement-source.txt.
            // Heading/XYZ interpretation is inherited; tail semantics are unresolved.
            if (!cursor.TryReadSingle(out _heading) || !cursor.TryReadSingle(out _x) ||
                !cursor.TryReadSingle(out _y) || !cursor.TryReadSingle(out _z) ||
                !cursor.TryReadBytes(16, out _opaqueTail) || !cursor.TryEnd()) throw cursor.Error();
            _body = new byte[36];
            Array.Copy(_buffer, 8, _body, 0, _body.Length);
            _stream.Position = cursor.Offset;
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

            PhaseExit.OnMove(client, _x, _y, _z);

            if (mode == AreaPollExperiment.ReplyMode.Echo)
                AreaEnterSignals.Fire(client);

        }

        public override PacketType GetType()
        {
            return PacketType.CMsg61116AD5;
        }
    }
}
