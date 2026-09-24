using System;
using System.IO;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    class ModulesList : TORGameClientPacket
    {
        private byte[] _body;

        public override void ReadImplementation()
        {
            ReadUInt32();
            ReadUInt32();
            int remaining = (int)(_stream.Length - _stream.Position);
            _body = remaining > 0 ? ReadBytes(remaining) : new byte[0];
        }

        public override void RunImplementation()
        {
            TORGameClient client = GetClient();
            if (client == null) { Log.Write(LogLevel.Warning, "ModulesList: no client."); return; }
            string hex = _body == null ? "(null)" : BitConverter.ToString(_body);
            int n = _body == null ? 0 : _body.Length;
            Log.Write(LogLevel.Client, "ModulesList: len={0} startupSent={1} hex={2}", n, client.StartupPacketsSent, hex);
            if (client.StartupPacketsSent) return;
            client.SendPacket(new WorldNotifyGauntletVersion(client.WorldServiceID));
            client.SendPacket(new WorldShouldSendScriptErrors(true, client.WorldServiceID));
            client.SendPacket(new TrackingServerInit(client.TrackingServiceID));
            client.SendPacket(new GameSystemNotifyID(client.GameSystemsServiceID));
            client.SendPacket(new WorldHackPack(client.WorldServiceID));
            client.SendPacket(new WorldRequestRPC(client.WorldServiceID));
            client.StartupPacketsSent = true;
            Log.Write(LogLevel.Client, "Sent deferred world startup packets after ModulesList readiness.");
        }

        public override PacketType GetType()
        {
            return PacketType.ModulesList;
        }
    }
}
