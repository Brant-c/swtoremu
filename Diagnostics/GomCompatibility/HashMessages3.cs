using System;
using Hero.EasyMyp;

class HashMessages3 {
    static void Main(string[] args) {
        string[] names = new string[] {
            "HackPackFromArea", "SetCharacter", "InstanceCreated", "AssetCreated",
            "ClientReplicationTransaction", "AwarenessEntered", "TeleportCharacter",
            "SetCharacterRendezvousPoint", "ChangeCharacterState", "SendToArea",
        };
        foreach (string name in names) {
            uint h1 = 0, h2 = 0;
            var h = new Hasher(Hasher.HasherType.TOR);
            h.Hash(name, ref h1, ref h2);
            Console.WriteLine("{0,-32} h1=0x{1:X8} h2=0x{2:X8}", name, h1, h2);
        }
    }
}
