using System;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    class AreaTaxiInteraction : TORAreaServerPacket
    {
        internal const UInt64 RetreatTerminal=0xE000DC42A2436F58UL;
        internal const UInt64 GnarlsTerminal=0xE0009C95E5C2E162UL;
        private byte _module;
        private readonly UInt64 _player, _taxi;
        private readonly bool _interaction;
        public AreaTaxiInteraction(UInt64 player, UInt64 taxi, bool interaction)
        {
            if (player == 0) throw new ArgumentException("Taxi interaction requires a player");
            _player=player; _taxi=taxi; _interaction=interaction;
        }
        internal static byte[] BuildRecord(UInt64 player, UInt64 taxi, bool interaction)
        {
            // Captured player schema 26: known terminals 42, current interaction
            // 51 and interaction type 60. April GOM enum Taxi=3, None=1.
            const int fields=215;
            byte[] states=new byte[(fields*2+7)/8];
            states[42/4] |= (byte)(1 << (6-2*(42%4)));
            if (interaction)
            {
                states[51/4] |= (byte)(1 << (6-2*(51%4)));
                states[60/4] |= (byte)(1 << (6-2*(60%4)));
            }
            using (MemoryStream values=new MemoryStream())
            using (MemoryStream body=new MemoryStream())
            using (MemoryStream record=new MemoryStream())
            {
                // Style 8 lookup-list count is doubled; preserve other known
                // destinations rather than using the replacement flag.
                values.WriteByte(4);
                AreaWellerConversation.Packed(values,RetreatTerminal); values.WriteByte(1);
                AreaWellerConversation.Packed(values,GnarlsTerminal); values.WriteByte(1);
                if (interaction) { AreaWellerConversation.Packed(values,taxi); values.WriteByte(taxi==0 ? (byte)1 : (byte)3); }
                AreaWellerConversation.Packed(body,26); AreaWellerConversation.Packed(body,(UInt64)values.Length);
                byte[] bytes=values.ToArray(); body.Write(bytes,0,bytes.Length); body.Write(states,0,states.Length);
                AreaWellerConversation.Packed(record,player); record.WriteByte(9); record.WriteByte(5); record.WriteByte(8);
                AreaWellerConversation.Packed(record,(UInt64)body.Length); bytes=body.ToArray(); record.Write(bytes,0,bytes.Length);
                return record.ToArray();
            }
        }
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); WriteAreaComponent();
            WriteUInt32(AreaAbilityEffectReplication.NextStreamID()); WriteUInt32(0);
            WriteByte(1); WriteByte(1); WriteBytes(BuildRecord(_player,_taxi,_interaction));
        }
        public override PacketType GetType() { return PacketType.AreaClientReplicationTransaction; }
        public override void SetModule(byte mod) { _module=mod; }
        public override byte GetModule() { return _module; }
    }
}
