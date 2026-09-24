using System;
using System.IO;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    // April client A6BB10: opcode, component, uint64 cached revision.
    class RepositorySyncRequest : TORGameClientPacket
    {
        private UInt64 _cachedRevision;

        public override void ReadImplementation()
        {
            ReadUInt32();
            ReadUInt32();
            _cachedRevision = ReadUInt64();
            if (_stream.Position != _stream.Length)
                throw new InvalidDataException("Unexpected repository synchronization payload length.");
        }

        public override void RunImplementation()
        {
            if (GetClient().RepositoryServiceID == 0)
                throw new InvalidOperationException("Repository service has not attached.");
            // This emulator serves a fixed local archive set, with no remote
            // repository deltas. Complete the native synchronization handshake.
            GetClient().SendPacket(new RepositorySyncReply(GetClient().RepositoryServiceID));
            Log.Write(LogLevel.Client,
                "Repository synchronization acknowledged: cached revision={0}, static local archives; this does not verify asset completeness.",
                _cachedRevision);
        }

        public override PacketType GetType() { return PacketType.RepositorySyncRequest; }
    }
}
