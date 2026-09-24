using System;
using System.IO;

namespace NexusToRServer.NET.Packets.Client
{
    // Native63F1AB emits this after processing a resource reply. Matches the
    // existing C++ HandleUnkB4BF82C3; no response or remote transfer state exists.
    class RepositoryDataReceipt : TORGameClientPacket
    {
        private UInt32 _value;
        public override void ReadImplementation()
        {
            ReadUInt32();
            Component = ReadUInt32();
            _value = ReadUInt32();
            if (_stream.Position != _stream.Length)
                throw new InvalidDataException("Unexpected repository receipt length.");
        }
        public override void RunImplementation()
        {
            Log.Write(LogLevel.Client, "Repository resource receipt: value={0}.", _value);
        }
        public override PacketType GetType() { return PacketType.RepositoryDataReceipt; }
    }
}
