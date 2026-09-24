using System;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// SMSG_CHARACTER_SET_RENDEZVOUS_POINT (0x2B4792AE) — the area server's
    /// "your arrival point" message. The client's receive handler (0x64F4BC in
    /// the client disassembly) reads, in order:
    ///     u64   (0x97C510)  — character id
    ///     u32   (0x97C4C0)  — placement type / map qualifier
    ///     vec3  (0xA7FD40)  — position
    ///     vec3  (0xA7FD40)  — rotation
    ///     u8    (0x97C580)  — flag
    /// followed by an end-of-message check (0x97D020), so the body must be
    /// exactly 8 + 4 + 12 + 12 + 1 = 37 bytes. The shape mirrors
    /// AreaTeleportCharacter (u64 + u32 + 6 floats + u8), so the teleport's
    /// placement values are reused for the rendezvous point.
    /// </summary>
    class CharacterSetRendezvousPoint : TORAreaServerPacket
    {
        private byte _module;
        private UInt64 _chID;
        private UInt32 _type;
        private Single _x1, _y1, _z1, _x2, _y2, _z2;
        private Byte _flag;

        public CharacterSetRendezvousPoint(UInt64 CharID, UInt32 Type, Single X1, Single Y1, Single Z1, Single X2, Single Y2, Single Z2, Byte Flag)
        {
            _chID = CharID;
            _type = Type;
            _x1 = X1;
            _y1 = Y1;
            _z1 = Z1;
            _x2 = X2;
            _y2 = Y2;
            _z2 = Z2;
            _flag = Flag;
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); // Packet Type
            WriteAreaComponent();

            WriteUInt64(_chID);
            WriteUInt32(_type);
            WriteFloat(_x1);
            WriteFloat(_y1);
            WriteFloat(_z1);
            WriteFloat(_x2);
            WriteFloat(_y2);
            WriteFloat(_z2);
            WriteByte(_flag);
        }

        public override PacketType GetType()
        {
            return PacketType.CharacterSetRendezvousPoint;
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
