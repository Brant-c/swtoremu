using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    class GameSystemNotifyID : TORGameServerPacket
    {
        private byte _module;
        private UInt16 _serviceID;

        public GameSystemNotifyID(UInt16 ServiceID = 0x0005)
        {
            _serviceID = ServiceID;
        }

        /// <summary>
        /// Writes and Constructs the specified Packet
        /// </summary>
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); // Packet Type
            WriteUInt32(((UInt32)_serviceID << 16) | 0x65AC); // Packet Component
            WriteUInt64(0x00);
        }

        /// <summary>
        /// Returns the PacketType of the specified Packet
        /// </summary>
        /// <returns>PacketType of specified Packet</returns>
        public override PacketType GetType()
        {
            return PacketType.GameSystemNotifyID;
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
