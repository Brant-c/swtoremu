using System;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Sends awareness set 1 with the control-clone record APPENDED, as a single
    /// object list, so nothing is superseded.
    ///
    /// Evidence this is the shape the client needs: in clone mode the client
    /// produced ZERO script errors (against six in taxi mode), proving our
    /// assembly and delivery are sound and the taxi's content is what fails. But
    /// the clone never appeared, and the run log shows awareness set 1 is sent
    /// AFTER our packet (idx 1022 ours, idx 1062 set 1) with the client never
    /// referencing our node afterwards. That is the replacement-semantics
    /// signature: the client appears to treat each A1D9E226 as replacing the
    /// awareness list, so our object must ride in the same packet as the 77.
    ///
    /// The earlier merge broke the working NPCs. The properties that would cause
    /// that are checked offline by Diagnostics/TaxiDevelopment-20261001/
    /// Verify-SingleListMerge.py before this ships:
    ///   - append-only; the captured 13488 bytes are preserved verbatim
    ///   - count byte 77 -&gt; 78 (one-byte packed encoding retained)
    ///   - merged list re-parses to exactly 78 records, walking to its own end
    ///   - captured records 0..76 unmoved; the clone lands last
    /// Notably the clone's parent 0x1AC688BE1E is absent from set 1, but so is the
    /// parent of the CAPTURED MEDCENTER DROID -- the same dangling parent the
    /// client already accepts -- so a missing parent is not the hazard here.
    ///
    /// Opt-in via SWTOR_TAXI_CLONE_CONTROL=1. No captured fixture is modified;
    /// the merge happens in memory only.
    /// </summary>
    class AreaMergedAwareness : TORAreaServerPacket
    {
        /// <summary>
        /// CONTROL: appends the selected LADDER rung into awareness set 1.
        ///
        /// The rung fixtures are byte splices of the CAPTURED medcenter droid record,
        /// verified by Diagnostics/TaxiDevelopment-20261001/Verify-TaxiLadder.py:
        /// rung 0 is byte-identical to the capture apart from the node identity and a
        /// 5 m X offset, and each later rung changes only its own token window(s).
        /// Because the baseline is captured, a rung-0 render proves transport,
        /// framing and placement, and the first rung that brings the six script
        /// errors back names the offending field.
        /// </summary>
        private byte _module;
            private readonly byte[] _payload;

            // Captured awareness set 1 object-list header: LE u32 pad, flags 0x01,
            // one-byte packed count. Recovered and asserted offline, not assumed.
            private const int CountOffset = 5;
            private const byte CapturedCount = 77;

            // rung 0 = the shipped taxi payload; rung 1 = the same record with only
            // _characterSpecification reverted to the captured donor value. Both are
            // five-object taxi payloads, so each contributes 5 records to the merge.
            private static readonly string[] RungResources =
                { "taxi.awareness", "taxi.record1" };
            private static readonly int[] RungBytes = { 675, 677 };
            private static readonly byte[] RungObjects = { 5, 5 };

            public enum AreaTaxiRung { Shipped = 0, DonorCharSpec = 1 }

            /// <summary>
            /// CONTROL: appends the selected taxi experiment payload into awareness
            /// set 1, replacing the separate-packet path.
            ///
            /// rung 0 is the shipped taxi record (known to raise six script errors);
            /// rung 1 reverts ONLY _characterSpecification to the captured donor value
            /// -- an 8-byte change out of 675 that keeps the taxi template,
            /// taxTerminalSpec and position intact. Both are the real taxi, not a
            /// stand-in, so a clean rung 1 is a working terminal rather than a proxy.
            /// </summary>
            public static AreaTaxiRung SelectedRung
            {
                get
                {
                    Int32 r;
                    return Int32.TryParse(Environment.GetEnvironmentVariable("SWTOR_TAXI_RUNG"),
                                          out r) && r >= 0 && r <= RungResources.Length - 1
                           ? (AreaTaxiRung)r : AreaTaxiRung.Shipped;
                }
            }

        public AreaMergedAwareness(String Area, String AreaID, String AreaCode,
                                   int AwarenessID, UInt64[] nodes, AreaTaxiRung rung)
        {
            _payload = BuildPayload(Area, AreaID, AreaCode, AwarenessID, nodes, rung);
        }

        private static byte[] BuildPayload(String Area, String AreaID, String AreaCode,
                                          int AwarenessID, UInt64[] nodes, AreaTaxiRung rung)
        {
            int r = (int)rung;
            if (nodes == null || nodes.Length != 5)
                throw new ArgumentException("Five taxi identities required");
            for (int i = 0; i < nodes.Length; i++)
                for (int j = 0; j < i; j++)
                    if (nodes[i] == nodes[j]) throw new ArgumentException("Taxi identities must be distinct");
            // Awareness lives in the NexusToRServer.AreaServer namespace; this file is in
            // ...NET.Packets.Server, so qualify it explicitly.
            byte[] captured = NexusToRServer.AreaServer.Awareness.Get(Area, AreaID, AreaCode, AwarenessID);
            if (captured.Length == 0)
                throw new InvalidDataException("Captured awareness set is missing");
            if (captured[4] != 0x01)
                throw new InvalidDataException("Unexpected awareness flags 0x" + captured[4].ToString("X2"));
            if (captured[CountOffset] != CapturedCount)
                throw new InvalidDataException("Captured count is " + captured[CountOffset] +
                                               ", expected " + CapturedCount);

            // Each rung is a FIVE-object taxi payload: LE u32 pad, flags, one-byte
            // count, then 5 records. The count byte is consumed here and the records
            // are appended verbatim, so the merged list gains 5 objects, not 1.
            int expected = RungBytes[r];
            int objects = RungObjects[r];
            byte[] records;
            using (Stream resource = Assembly.GetExecutingAssembly()
                                       .GetManifestResourceStream(RungResources[r]))
            {
                if (resource == null || resource.Length != expected)
                    throw new InvalidDataException("Taxi rung " + r + " fixture missing or changed");
                byte[] whole = new byte[expected];
                int read = 0, count;
                while ((count = resource.Read(whole, read, whole.Length - read)) > 0) read += count;
                if (read != whole.Length) throw new InvalidDataException("Truncated taxi fixture");
                if (whole[4] != 0x01 || whole[5] != objects)
                    throw new InvalidDataException("Taxi fixture is not a " + objects + "-object list");
                records = new byte[whole.Length - 6];
                Buffer.BlockCopy(whole, 6, records, 0, records.Length);
            }

            // Substitute all five identities, mirroring AreaTaxiAwareness's offsets:
            // the NPC record plus four attached effect containers.
            int[] Slots = { 0, 1, 2, 3, 4, 1, 0, 0, 2, 0, 3, 0, 4, 0 };
            int[] Offsets = { 6, 108, 114, 120, 126, 484, 500, 529, 536, 552, 582, 598, 628, 644 };
            for (int i = 0; i < Offsets.Length; i++)
            {
                byte[] expectedNode = AreaReplicationDestroy.PackNode(0x1AC7001000UL + (UInt64)Slots[i]);
                byte[] replacement = AreaReplicationDestroy.PackNode(nodes[Slots[i]]);
                if (replacement.Length != expectedNode.Length)
                    throw new ArgumentException("Taxi identity width mismatch");
                for (int j = 0; j < expectedNode.Length; j++)
                    if (records[Offsets[i] - 6 + j] != expectedNode[j])
                        throw new InvalidDataException("Taxi fixture patch mismatch at " + Offsets[i]);
                Buffer.BlockCopy(replacement, 0, records, Offsets[i] - 6, replacement.Length);
            }

            byte[] merged = new byte[captured.Length + records.Length];
            Buffer.BlockCopy(captured, 0, merged, 0, CountOffset);
            merged[CountOffset] = (byte)(CapturedCount + objects);  // 77 -> 82, one byte
            Buffer.BlockCopy(captured, CountOffset + 1, merged, CountOffset + 1,
                             captured.Length - CountOffset - 1);
            Buffer.BlockCopy(records, 0, merged, captured.Length, records.Length);

            // The merged payload must still contain every captured byte, with only the
            // one-byte count changed. This is the check that keeps a failed
            // experiment from taking the room's NPCs down with it.
            for (int i = 0; i < CountOffset; i++)
                if (merged[i] != captured[i])
                    throw new InvalidDataException("Merged header prefix altered");
            for (int i = CountOffset + 1; i < captured.Length; i++)
                if (merged[i] != captured[i])
                    throw new InvalidDataException("Captured payload altered");

            using (SHA256 sha = SHA256.Create())
                Log.Write(LogLevel.Warning,
                    "AreaMergedAwareness: MERGED taxi rung={0} sha256={1} bytes={2} captured={3} count={4}->{5} npc=0x{6:X16}; captured payload preserved verbatim.",
                    r, BitConverter.ToString(sha.ComputeHash(merged)).Replace("-", ""),
                    merged.Length, captured.Length, CapturedCount, CapturedCount + objects,
                    nodes[0]);
            return merged;
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