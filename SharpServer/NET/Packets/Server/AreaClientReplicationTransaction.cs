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
            : this(Area, AreaID, AreaCode, CRTID, 0)
        {
        }

        public AreaClientReplicationTransaction(String Area, String AreaID, String AreaCode, int CRTID, UInt64 CharacterID)
        {
            //
            _acrt = CapturedCharacterRemap.Apply(
                AreaServer.CRT.Get(Area, AreaID, AreaCode, CRTID), CharacterID,
                "CRT " + CRTID.ToString());
            if (CRTID == 2 &&
                Environment.GetEnvironmentVariable("SWTOR_REMOVE_SAFE_LOGIN_EFFECT") == "1")
            {
                _acrt = AreaSafeLoginRemoval.SuppressFromCapturedCreate(_acrt);
                Log.Write(LogLevel.Warning,
                    "CRT2: suppressed captured Safe Login Immunity /0/2 container slot and object record.");
            }
            if (CRTID == 16 &&
                Environment.GetEnvironmentVariable("SWTOR_MOBILITY_IN_CRT16") == "1")
            {
                // staMobility travels alone: it is the one field that poisons a
                // shared record, so CRT16 carries it and CRT17 keeps {100, 129}.
                _acrt = AreaSafeLoginRemoval.ApplyMobilityFreeToCRT16(_acrt);
                Log.Write(LogLevel.Warning,
                    "CRT16: single-field staMobilityFree record; the captured field-100 stat map is dropped here and still delivered by CRT17.");
            }
            if (CRTID == 17 &&
                Environment.GetEnvironmentVariable("SWTOR_REMOVE_SAFE_LOGIN_EFFECT") == "1")
            {
                // Two mutually exclusive shapes of the same transaction.
                // SWTOR_PLAYERLOADED_ONLY=1 emits a record whose only present
                // field is chrPlayerLoaded, so a null result isolates that field
                // from the three-field merge. It deliberately stops delivering
                // staMobility and the stat map, so it is a diagnostic, not a fix.
                if (Environment.GetEnvironmentVariable("SWTOR_STATMAP_AND_LOADED") == "1")
                {
                    // Third bisect: stat map and load flag, no mobility.
                    _acrt = AreaSafeLoginRemoval.ApplyStatMapAndPlayerLoadedToFinalCapturedTransaction(_acrt);
                    Log.Write(LogLevel.Warning,
                        "CRT17: DIAGNOSTIC statmap variant, modMetaStatComputed_Shared and chrPlayerLoaded=true only; staMobility is NOT delivered.");
                }
                else if (Environment.GetEnvironmentVariable("SWTOR_MOBILITY_AND_LOADED") == "1")
                {
                    // Second bisect: mobility and the load flag, no stat map.
                    _acrt = AreaSafeLoginRemoval.ApplyMobilityAndPlayerLoadedToFinalCapturedTransaction(_acrt);
                    Log.Write(LogLevel.Warning,
                        "CRT17: DIAGNOSTIC two-field variant, staMobilityFree and chrPlayerLoaded=true only; modMetaStatComputed_Shared is NOT delivered.");
                }
                else if (Environment.GetEnvironmentVariable("SWTOR_PLAYERLOADED_ONLY") == "1")
                {
                    _acrt = AreaSafeLoginRemoval.ApplyPlayerLoadedOnlyToFinalCapturedTransaction(_acrt);
                    Log.Write(LogLevel.Warning,
                        "CRT17: DIAGNOSTIC single-field variant, only chrPlayerLoaded=true present; staMobility and modMetaStatComputed_Shared are NOT delivered.");
                }
                else
                {
                    _acrt = AreaSafeLoginRemoval.ApplyMobilityFreeToFinalCapturedTransaction(_acrt);
                    Log.Write(LogLevel.Warning,
                        "CRT17: integrated schema-derived staMobilityFree and chrPlayerLoaded=true update into accepted stream 0x001B502D.");
                }
            }

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
