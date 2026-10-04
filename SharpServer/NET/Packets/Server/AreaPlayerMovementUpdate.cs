using System;
using System.IO;
namespace NexusToRServer.NET.Packets.Server
{
    // Client-derived style8 update of the captured structure26. Opt-in caller.
    class AreaPlayerMovementUpdate : TORAreaServerPacket
    {
        private byte _module;
        private readonly UInt64 _player;
        private readonly byte[] _value;
        private readonly bool _enterPhase;
        private static readonly byte[] PhaseInfoCreate = new byte[] { 0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x1F, 0xAA, 0xCF, 0x40, 0x00, 0x00, 0x11, 0x46, 0xCB, 0x71, 0xCB, 0xCC, 0x1A, 0xC6, 0x88, 0xC9, 0x7E, 0x05, 0x07, 0x17, 0x4B, 0x14, 0x01, 0x01, 0xCF, 0x40, 0x00, 0x01, 0x0E, 0x21, 0x8A, 0x83, 0x9C, 0xCF, 0x40, 0x00, 0x01, 0x0E, 0x21, 0x8A, 0x83, 0x9C, 0xC0 };
        public AreaPlayerMovementUpdate(UInt64 player, float x, float y, float z)
        {
            if (player == 0 || !Finite(x) || !Finite(y) || !Finite(z)) throw new ArgumentException("Invalid movement anchor");
            _player = player;
            using (MemoryStream ms = new MemoryStream()) using (BinaryWriter w = new BinaryWriter(ms))
            { w.Write(x); w.Write(y); w.Write(z); _value = ms.ToArray(); }
        }
        public AreaPlayerMovementUpdate(UInt64 player)
        {
            if (player == 0) throw new ArgumentException("Missing selected player");
            _player = player; _enterPhase = true;
            _value = AreaReplicationDestroy.PackNode(0x1AC6F6DC1FUL);
        }
        internal static bool Finite(float x) { return !Single.IsNaN(x) && !Single.IsInfinity(x); }
        internal static byte[] BuildRecord(UInt64 player, int index, byte[] value)
        {
            if (player == 0 || (index != 206 && index != 25) || value == null) throw new ArgumentException("Invalid movement/phase record");
            byte[] states = new byte[54];
            states[index / 4] = (byte)(1 << (6 - (index % 4) * 2));
            using (MemoryStream ms = new MemoryStream())
            {
                byte[] node = AreaReplicationDestroy.PackNode(player); ms.Write(node, 0, node.Length);
                ms.WriteByte(0x09); ms.WriteByte(5); ms.WriteByte(8);
                // structure1byte + fixed3byte inner-length + values + states.
                ms.WriteByte((byte)(4 + value.Length + states.Length)); ms.WriteByte(26);
                ms.WriteByte(0xC9); ms.WriteByte(0); ms.WriteByte((byte)value.Length);
                ms.Write(value, 0, value.Length); ms.Write(states, 0, states.Length);
                return ms.ToArray();
            }
        }
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); WriteAreaComponent();
            WriteUInt32(AreaAbilityEffectReplication.NextStreamID()); WriteUInt32(0);
            WriteByte(1); WriteByte(_enterPhase ? (byte)2 : (byte)1);
            if (_enterPhase) WriteBytes(CapturedCharacterRemap.Apply(PhaseInfoCreate, _player, "phase reentry node"));
            WriteBytes(BuildRecord(_player, _enterPhase ? 25 : 206, _value));
        }
        public override PacketType GetType() { return PacketType.AreaClientReplicationTransaction; }
        public override void SetModule(byte mod) { _module = mod; }
        public override byte GetModule() { return _module; }
    }
}
