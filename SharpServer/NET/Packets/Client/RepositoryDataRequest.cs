using System;
using System.IO;
using System.Text;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    // April A6B5E0: request ID followed by a terminated byte string.
    class RepositoryDataRequest : TORGameClientPacket
    {
        private UInt32 _requestId;
        private string _path;
        public override void ReadImplementation()
        {
            ReadUInt32();
            Component = ReadUInt32();
            _requestId = ReadUInt32();
            UInt32 length = ReadUInt32();
            if (length == 0 || length > _stream.Length - _stream.Position)
                throw new InvalidDataException("Invalid repository resource path length.");
            byte[] path = ReadBytes((int)length);
            if (path[path.Length - 1] != 0)
                throw new InvalidDataException("Repository resource path is not terminated.");
            _path = Encoding.UTF8.GetString(path, 0, path.Length - 1);
            if (_stream.Position != _stream.Length)
                throw new InvalidDataException("Unexpected repository data request length.");
        }
        public override void RunImplementation()
        {
            // Local archives are authoritative. There is no remote asset store;
            // silence here strands an outstanding native resource request.
            byte[] data;
            UInt64 uncompressedSize;
            UInt32 crc;
            if (TorArchive.TryRead(_path, out data, out uncompressedSize, out crc))
            {
                GetClient().SendPacket(new RepositoryDataReply(Component, _requestId, _path, data, uncompressedSize, crc));
                Log.Write(LogLevel.Client, "Repository asset served: request={0}, path='{1}', bytes={2}.",
                    _requestId, _path, data.Length);
                return;
            }
            GetClient().SendPacket(new RepositoryDataNotFound(Component, _requestId, _path));
            Log.Write(LogLevel.Client, "Repository asset unavailable: request={0}, path='{1}'. Returned FQN NOT FOUND; verify the matching local archives.", _requestId, _path);
        }
        public override PacketType GetType() { return PacketType.RepositoryDataRequest; }
    }
}
