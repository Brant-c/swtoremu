using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    class AreaClientReplicationTransaction : TORAreaServerPacket
    {
        private byte _module;
        private byte[] _acrt;
        private bool _suppress;

        public AreaClientReplicationTransaction(String Area, String AreaID, String AreaCode, int CRTID)
        {
            //
            _acrt = AreaServer.CRT.Get(Area, AreaID, AreaCode, CRTID);

            // An empty payload is not equivalent to no packet. When the fixture is
            // missing and SWTOR_CRT_MISSING_MODE=skip, omit the whole transaction
            // instead of emitting a malformed zero-length one.
            _suppress = _acrt.Length == 0 && AreaServer.CRT.SuppressMissingCrt;
            if (_suppress)
                Log.Write(LogLevel.Warning,
                    "Suppressing empty AreaClientReplicationTransaction (area code {0}, CRT {1})", AreaCode, CRTID);
        }

        public override Boolean SuppressSend
        {
            get { return _suppress; }
        }

        /// <summary>
        /// Writes and Constructs the specified Packet
        /// </summary>
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); // Packet Type
            WriteAreaComponent();

            WriteBytes(_acrt);
        }

        /// <summary>
        /// Returns the PacketType of the specified Packet
        /// </summary>
        /// <returns>PacketType of specified Packet</returns>
        public override PacketType GetType()
        {
            return PacketType.AreaClientReplicationTransaction;
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
