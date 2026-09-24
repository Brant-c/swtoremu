using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    class SelectCharacterRequest : TORGameClientPacket
    {
        UInt16 _unk01, _unk02;

        public override void ReadImplementation()
        {
            ReadUInt32();
            _unk01 = ReadUInt16();
            _unk02 = ReadUInt16();
            UInt64 CharID = ReadUInt64();
            GetClient().ActiveCharacter = new TOR.Character(CharID);
            Log.Write(LogLevel.Client, "SelectCharacterRequest: selected char={0} routing content=0x{1:X4} transport=0x{2:X4}", CharID, _unk01, _unk02);
        }

        public override void RunImplementation()
        {
            GetClient().SendPacket(new SelectCharacterReply(_unk02, _unk01));
            GetClient().SendPacket(new WorldTravelPending(_unk02, _unk01));
            GetClient().SendPacket(new WorldTravelStatus(_unk02, _unk01));
            GetClient().SendPacket(new WorldSendToArea(_unk02, _unk01));
        }

        public override PacketType GetType()
        {
            return PacketType.SelectCharacterRequest;
        }
    }
}
