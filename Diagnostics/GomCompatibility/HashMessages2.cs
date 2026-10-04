using System;
using Hero.EasyMyp;

class HashMessages2 {
    static void Main(string[] args) {
        string[] names = new string[] {
            "HackPackFromArea", "SetCharacter", "InstanceCreated", "AssetCreated",
            "ClientReplicationTransaction", "AwarenessEntered", "TeleportCharacter",
            "SetCharacterRendezvousPoint", "ChangeCharacterState", "SendToArea",
        };
        foreach (string name in names) {
            foreach (uint seed in new uint[] { 0, 0xdeadbeef }) {
                var h = new Hasher(Hasher.HasherType.TOR);
                h.Hash(name, seed);
                Console.WriteLine("{0,-32} seed=0x{1:X8} sh=0x{2:X8} ph=0x{3:X8}", name, seed, h.sh, h.ph);
            }
        }
    }
}
