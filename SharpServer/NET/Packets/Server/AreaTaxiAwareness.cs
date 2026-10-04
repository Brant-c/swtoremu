using System;
using System.IO;
using System.Reflection;

namespace NexusToRServer.NET.Packets.Server
{
    // Captured awareness family and compact taxi schema 66. Placement is the
    // authored taxi pad anchor read from the area instance row
    // spn.location.tython.taxi.taxi_poi01_jediretreat_pad1.spn_c (-535,-1255,-77),
    // not a vendor offset. The record also carries the captured vendor's
    // appearance/identity tail (chrCreatureTypeList, cbtFaction,
    // chrTemplateVisualIndex, cbtCreatureType, brkResourceName, chrClass,
    // _characterSpecification, ablContainer, chrLevel), which the earlier
    // health-only record omitted.
    class AreaTaxiAwareness : TORAreaServerPacket
    {
        private byte _module;
        private readonly byte[] _payload;
        private const int FixtureBytes = 675;
        // Authored anchor; must match PLACEMENT in Generate-Taxi.py.
        public const string Placement = "(-53.5,-7.7,-125.5)";
        private static readonly int[] Offsets = { 6,108,114,120,126,484,500,529,536,552,582,598,628,644 };
        private static readonly int[] Slots = { 0,1,2,3,4,1,0,0,2,0,3,0,4,0 };
        public AreaTaxiAwareness(UInt64[] nodes)
        {
            _payload = BuildPayload(nodes);
        }
        /// <summary>
        /// Builds the taxi object-list payload: the five embedded records with
        /// their placeholder identities substituted for this session's nodes.
        /// Shared with the startup awareness merge, which appends the same
        /// records into the payload the client already builds its object map
        /// from, rather than sending a second late awareness packet.
        /// </summary>
        internal static byte[] BuildPayload(UInt64[] nodes)
        {
            byte[] payload;
            if (nodes == null || nodes.Length != 5) throw new ArgumentException("Five taxi identities required");
            for (int i=0;i<nodes.Length;i++) for(int j=0;j<i;j++)
                if(nodes[i]==nodes[j]) throw new ArgumentException("Taxi identities must be distinct");
            using (Stream resource = Assembly.GetExecutingAssembly().GetManifestResourceStream("taxi.awareness"))
            {
                if (resource == null || resource.Length != FixtureBytes) throw new InvalidDataException("Taxi awareness fixture missing or changed");
                payload = new byte[FixtureBytes];
                int offset = 0, count;
                while ((count = resource.Read(payload, offset, payload.Length-offset)) > 0) offset += count;
                if (offset != payload.Length) throw new InvalidDataException("Truncated taxi awareness fixture");
            }
            for (int i=0; i<Offsets.Length; i++)
            {
                int slot=Slots[i], offset=Offsets[i];
                byte[] expected=AreaReplicationDestroy.PackNode(0x1AC7001000UL+(UInt64)slot);
                byte[] replacement=AreaReplicationDestroy.PackNode(nodes[slot]);
                if (nodes[slot] == 0 || replacement.Length != expected.Length) throw new ArgumentException("Taxi identity width mismatch");
                for (int j=0; j<expected.Length; j++)
                    if (payload[offset+j] != expected[j]) throw new InvalidDataException("Taxi fixture patch mismatch");
                Buffer.BlockCopy(replacement,0,payload,offset,replacement.Length);
            }
            // Self-identifying so a run log always proves which fixture ran. The
            // caller's log line previously carried a hardcoded position string
            // that kept naming the superseded vendor offset.
            using (System.Security.Cryptography.SHA256 sha =
                   System.Security.Cryptography.SHA256.Create())
                Log.Write(LogLevel.Warning,
                    "AreaTaxiAwareness: fixture sha256={0} bytes={1} placement={2} npc=0x{3:X16} containers=0x{4:X16}/0x{5:X16}/0x{6:X16}/0x{7:X16}",
                    BitConverter.ToString(sha.ComputeHash(payload)).Replace("-", ""),
                    payload.Length, Placement, nodes[0], nodes[1], nodes[2], nodes[3], nodes[4]);
            return payload;
        }
        /// <summary>Number of object records in the embedded taxi payload.</summary>
        internal const int RecordCount = 5;
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); WriteAreaComponent(); WriteBytes(_payload);
        }
        public override PacketType GetType() { return PacketType.AreaAwarenessEntered; }
        public override void SetModule(byte mod) { _module=mod; }
        public override byte GetModule() { return _module; }
    }
}
