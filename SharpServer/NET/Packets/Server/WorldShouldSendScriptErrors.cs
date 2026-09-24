using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    class WorldShouldSendScriptErrors : TORGameServerPacket
    {
        private byte _module;
        private bool _send;
        private UInt16 _serviceID;

        public WorldShouldSendScriptErrors(Boolean Send, UInt16 ServiceID = 0x0003)
        {
            _send = Send;
            _serviceID = ServiceID;
        }

        /// <summary>
        /// Writes and Constructs the specified Packet
        /// </summary>
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); // Packet Type
            WriteUInt32(((UInt32)_serviceID << 16) | 0x65AB); // Packet Component
            WriteBoolean(_send);
        }

        /// <summary>
        /// Returns the PacketType of the specified Packet
        /// </summary>
        /// <returns>PacketType of specified Packet</returns>
        public override PacketType GetType()
        {
            return PacketType.WorldShouldSendScriptErrors;
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
