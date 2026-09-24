using System;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// SMSG_CHARACTER_CHANGE_STATE (0xADEAFCA3) — server→client character state
    /// change. The client's receive handler (0x6501DD in the client
    /// disassembly) reads, in order:
    ///     u64    (0x97C510)  — character id
    ///     string (0x97D270, vtable 0x0111DCD4 — the same string object used by
    ///                       TravelPending's mapName/mapId, which the client
    ///                       already parses correctly)
    /// followed by an end-of-message check (0x97D020).
    /// </summary>
    class CharacterChangeState : TORAreaServerPacket
    {
        private byte _module;
        private UInt64 _chID;
        private string _state;

        public CharacterChangeState(UInt64 CharID, string State)
        {
            _chID = CharID;
            _state = State ?? string.Empty;
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); // Packet Type
            WriteAreaComponent();

            WriteUInt64(_chID);
            WriteString(_state);
        }

        public override PacketType GetType()
        {
            return PacketType.CharacterChangeState;
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
