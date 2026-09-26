using System;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// The archived Tython fixtures were captured for character GOM node
    /// 0x4000010E218A839C. The emulator's selected character has its own node
    /// id, so every reference to the captured player must be rewritten as one
    /// unit before the payload reaches the client. Leaving the captured id in
    /// CRTs while SetCharacter/ChangeState use the selected id creates two
    /// identities; the client then cannot find the selected character in its
    /// replicated-object map.
    /// </summary>
    static class CapturedCharacterRemap
    {
        public const UInt64 CapturedCharacterID = 0x4000010E218A839CUL;

        public static byte[] Apply(byte[] source, UInt64 selectedCharacterID, string label)
        {
            if (source == null) return new byte[0];
            byte[] result = (byte[])source.Clone();
            if (selectedCharacterID == 0 || selectedCharacterID == CapturedCharacterID)
                return result;

            byte[] packedFrom = Packed(CapturedCharacterID);
            byte[] packedTo = Packed(selectedCharacterID);
            byte[] littleFrom = BitConverter.GetBytes(CapturedCharacterID);
            byte[] littleTo = BitConverter.GetBytes(selectedCharacterID);
            int packed = Replace(result, packedFrom, packedTo);
            int little = Replace(result, littleFrom, littleTo);
            if (packed != 0 || little != 0)
                Log.Write(LogLevel.Info,
                    "Character fixture remap [{0}]: {1} packed + {2} little-endian references, {3:X16}->{4:X16}.",
                    label, packed, little, CapturedCharacterID, selectedCharacterID);
            return result;
        }

        private static byte[] Packed(UInt64 value)
        {
            byte[] result = new byte[9];
            result[0] = 0xCF;
            for (int i = 0; i < 8; i++)
                result[i + 1] = (byte)(value >> (56 - i * 8));
            return result;
        }

        private static int Replace(byte[] data, byte[] from, byte[] to)
        {
            int replacements = 0;
            for (int i = 0; i <= data.Length - from.Length; i++)
            {
                bool match = true;
                for (int j = 0; j < from.Length; j++)
                    if (data[i + j] != from[j]) { match = false; break; }
                if (!match) continue;
                Buffer.BlockCopy(to, 0, data, i, to.Length);
                replacements++;
                i += from.Length - 1;
            }
            return replacements;
        }
    }
}
