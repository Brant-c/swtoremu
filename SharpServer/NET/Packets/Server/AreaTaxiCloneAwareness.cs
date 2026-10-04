using System;
using System.IO;
using System.Reflection;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// CONTROL EXPERIMENT. Sends the captured medcenter droid record byte-for-byte,
    /// changing nothing but the node identity.
    ///
    /// Purpose: the generated taxi record has produced three consecutive behavioural
    /// no-ops, while the captured medcenter droid -- which this generator never
    /// produced and the client demonstrably renders a model for -- arrives
    /// unmodified in the real initial payload. Sending that exact record from the
    /// same position in the startup bundle separates OUR synthesis and delivery from
    /// the taxi's CONTENT:
    ///   renders  -> generator path is sound; the fault is taxi-specific content.
    ///   no model -> the generator assembly or delivery position is at fault, and
    ///               every content experiment so far was uninterpretable.
    ///
    /// Opt-in via SWTOR_TAXI_CLONE_CONTROL=1, which suppresses the taxi payload so
    /// exactly one NPC object is introduced. It does not touch any captured
    /// .aaw/.acrt fixture.
    /// </summary>
    class AreaTaxiCloneAwareness : TORAreaServerPacket
    {
        private byte _module;
        private readonly byte[] _payload;
        private const int FixtureBytes = 478;
        private const int NodeOffset = 6;
        private const UInt64 Placeholder = 0x1AC7001000UL;

        public AreaTaxiCloneAwareness(UInt64 node)
        {
            _payload = BuildPayload(node);
        }

        private static byte[] BuildPayload(UInt64 node)
        {
            if (node == 0) throw new ArgumentException("Clone identity required");
            byte[] payload;
            using (Stream resource = Assembly.GetExecutingAssembly().GetManifestResourceStream("taxi.clone"))
            {
                if (resource == null || resource.Length != FixtureBytes)
                    throw new InvalidDataException("Taxi clone fixture missing or changed");
                payload = new byte[FixtureBytes];
                int offset = 0, count;
                while ((count = resource.Read(payload, offset, payload.Length - offset)) > 0) offset += count;
                if (offset != payload.Length) throw new InvalidDataException("Truncated taxi clone fixture");
            }
            byte[] expected = AreaReplicationDestroy.PackNode(Placeholder);
            byte[] replacement = AreaReplicationDestroy.PackNode(node);
            if (replacement.Length != expected.Length)
                throw new ArgumentException("Clone identity width mismatch");
            for (int j = 0; j < expected.Length; j++)
                if (payload[NodeOffset + j] != expected[j])
                    throw new InvalidDataException("Clone fixture patch mismatch");
            Buffer.BlockCopy(replacement, 0, payload, NodeOffset, replacement.Length);
            using (System.Security.Cryptography.SHA256 sha =
                   System.Security.Cryptography.SHA256.Create())
                Log.Write(LogLevel.Warning,
                    "AreaTaxiCloneAwareness: CONTROL clone of captured medcenter droid sha256={0} bytes={1} npc=0x{2:X16}; only the identity differs.",
                    BitConverter.ToString(sha.ComputeHash(payload)).Replace("-", ""),
                    payload.Length, node);
            return payload;
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); WriteAreaComponent(); WriteBytes(_payload);
        }
        public override PacketType GetType() { return PacketType.AreaAwarenessEntered; }
        public override void SetModule(byte mod) { _module = mod; }
        public override byte GetModule() { return _module; }
    }
}