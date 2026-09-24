using System;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Echo reply for the client's CMsgC26464A9 poll.
    /// Body is the exact byte blob the client sent after its type/routing header.
    /// </summary>
    class CMsgC26464A9Ack : TORGameServerPacket
    {
        private byte _module;
        private UInt32 _component;
        private byte[] _body;

        public CMsgC26464A9Ack(UInt32 component, byte[] body)
        {
            _component = component;
            _body = body ?? new byte[0];
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            WriteUInt32(_component);
            WriteBytes(_body);
        }

        public override PacketType GetType()
        {
            return PacketType.CMsgC26464A9;
        }

        public override void SetModule(byte inMod)
        {
            _module = inMod;
        }

        public override byte GetModule()
        {
            return _module;
        }
    }
}
