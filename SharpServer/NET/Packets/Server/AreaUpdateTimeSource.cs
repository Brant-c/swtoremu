using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    class AreaUpdateTimeSource : TORAreaServerPacket
    {
        private static readonly DateTime UnixEpochUtc =
            new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);
        private byte _module;

        public AreaUpdateTimeSource()
        {
            //
        }

        /// <summary>
        /// Writes and Constructs the specified Packet
        /// </summary>
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); // Packet Type
            WriteAreaComponent();

            // The second captured value is Unix time in milliseconds.  The
            // old fixture was 2012-04-13T09:57:12.943Z, which made newly
            // replicated timed effects disagree with the client's clock.
            // Unknown1 is retained verbatim until its purpose is known.
            WriteUInt64(0x05557892);
            WriteUInt64(GetUnixTimeMillisecondsUtc());
        }

        internal static UInt64 GetUnixTimeMillisecondsUtc()
        {
            return checked((UInt64)((DateTime.UtcNow - UnixEpochUtc).Ticks /
                TimeSpan.TicksPerMillisecond));
        }

        internal static UInt64 GetFileTimeMillisecondsUtc()
        {
            return checked((UInt64)(DateTime.UtcNow.ToFileTimeUtc() /
                TimeSpan.TicksPerMillisecond));
        }

        /// <summary>
        /// Returns the PacketType of the specified Packet
        /// </summary>
        /// <returns>PacketType of specified Packet</returns>
        public override PacketType GetType()
        {
            return PacketType.AreaUpdateTimeSource;
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
