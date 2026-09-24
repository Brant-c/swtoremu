using System;
using NexusToRServer.NET;

namespace NexusToRServer.NET.Packets.Client
{
    class CMsgC586BD22 : TORGameClientPacket
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
            string hex = _body == null ? "(null)" : BitConverter.ToString(_body);
            Log.Write(LogLevel.Client, "CMsgC586BD22: component=0x{0:X8} len={1} body={2}", _component, _body == null ? 0 : _body.Length, hex);
            if (client == null) { Log.Write(LogLevel.Warning, "CMsgC586BD22: no client; cannot place character."); return; }
            if (client.AreaServiceID == 0) { Log.Write(LogLevel.Warning, "CMsgC586BD22: area-service not attached; Body={0} bytes hex={1}", _body == null ? 0 : _body.Length, _body == null ? "(null)" : BitConverter.ToString(_body)); return; }
            Log.Write(LogLevel.Client, "CMsgC586BD22: observed area message; no synthetic response sent.");
        }

        public override PacketType GetType()
        {
            return PacketType.CMsgC586BD22;
        }
    }
}
