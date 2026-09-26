using System;
using System.IO;
using System.Text;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    // Matches C++ Session::HandleUnk8EB28DE9.
    class WorldByteReport : TORGameClientPacket
    {
        private UInt32 _length;
        private byte[] _body;
        public override void ReadImplementation()
        {
            ReadUInt32();
            Component = ReadUInt32();
            _length = ReadUInt32();
            if (_length != _stream.Length - _stream.Position)
                throw new InvalidDataException("World byte report length does not match payload.");
            _body = new BinaryReader(_stream).ReadBytes((int)_length);
        }

        public override void RunImplementation()
        {
            // This packet is not the authoritative world-travel completion handshake.
            // The original server flow acknowledges travel through the character-select
            // sequence and sends the travel status/status-to-area packets from that path.
            // Treating this report as a synthetic completion ack can stall the client in
            // the world-entry load loop.
            // Preserve the report for diagnosis.  The reference server treats this
            // opcode as a no-op, but the client emits it repeatedly during the
            // unresolved post-travel loading state.  Logging its complete, small
            // body lets us distinguish an unchanged heartbeat from a readiness bit
            // or counter transition without inventing a response packet.
            string hex = _body == null ? "(null)" : BitConverter.ToString(_body);
            string words = "";
            if (_body != null && (_body.Length % 4) == 0)
            {
                StringBuilder builder = new StringBuilder();
                for (int offset = 0; offset < _body.Length; offset += 4)
                {
                    if (builder.Length != 0) builder.Append(',');
                    builder.Append(BitConverter.ToUInt32(_body, offset).ToString("X8"));
                }
                words = builder.ToString();
            }
            Log.Write(LogLevel.Client,
                "World report 8EB28DE9: component=0x{0:X8} bytes={1} words=[{2}] hex={3}; no synthetic WorldTravelStatus reply sent.",
                Component, _length, words, hex);
        }

        public override PacketType GetType() { return PacketType.WorldByteReport; }
    }
}
