using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;

namespace $rootnamespace$
{
    class $safeitemname$ : TORGameServerPacket
    {
		private byte _module;
	
        public $safeitemname$()
        {
            //
        }

        /// <summary>
        /// Writes and Constructs the specified Packet
        /// </summary>
        public override void  WriteImplementation()
        {
			WriteUInt32((UInt32)GetType()); // Packet Type
            WriteUInt32(0x00000000); // Packet Component
        }

        /// <summary>
        /// Returns the PacketType of the specified Packet
        /// </summary>
        /// <returns>PacketType of specified Packet</returns>
        public override PacketType GetType()
        {
            return PacketType.$safeitemname$;
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
