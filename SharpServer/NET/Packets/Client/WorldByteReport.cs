using System;
using System.IO;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    // Matches C++ Session::HandleUnk8EB28DE9.
    class WorldByteReport : TORGameClientPacket
    {
        private UInt32 _length;
        public override void ReadImplementation()
        {
            ReadUInt32();
            Component = ReadUInt32();
            _length = ReadUInt32();
            if (_length != _stream.Length - _stream.Position)
                throw new InvalidDataException("World byte report length does not match payload.");
            _stream.Position = _stream.Length;
        }

        public override void RunImplementation()
        {
            // This packet is not the authoritative world-travel completion handshake.
            // The original server flow acknowledges travel through the character-select
            // sequence and sends the travel status/status-to-area packets from that path.
            // Treating this report as a synthetic completion ack can stall the client in
            // the world-entry load loop.
            Log.Write(LogLevel.Client, "World report 8EB28DE9: {0} bytes received; no synthetic WorldTravelStatus reply sent.", _length);
        }

        public override PacketType GetType() { return PacketType.WorldByteReport; }
    }
}
