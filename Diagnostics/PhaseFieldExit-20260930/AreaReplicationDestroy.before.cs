using System;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Emits a one-node replication removal transaction. Replication framing
    /// has separate object-update (bit 0) and removed-node (bit 1) lists; a
    /// removal is not an object record carrying an operation flag.
    /// </summary>
    class AreaReplicationDestroy : TORAreaServerPacket
    {
        private byte _module;
        private readonly UInt32 _streamID;
        private readonly UInt64 _nodeID;

        public AreaReplicationDestroy(UInt32 streamID, UInt64 nodeID)
        {
            _streamID = streamID;
            _nodeID = nodeID;
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            WriteAreaComponent();

            WriteUInt32(_streamID);
            WriteUInt32(0);       // no schema definitions
            // flags 0x03 = object-update list AND removed-node list. Every
            // verified removal in this tree (AreaSafeLoginRemoval, CRT17, the
            // ability-effect removal) pairs the removed-node list with at least
            // one object update; a bare removal was never proven to be accepted
            // by the client. So emit a benign style-8 update (re-affirm the
            // captured positive-effect container's slot-1 entry) alongside the
            // removed node.
            WriteByte(0x03);
            WriteByte(0x01);      // one object update
            WriteBytes(new byte[] {
                0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x0E, // container 0x1AC6F6DC0E
                0x09,                               // update + value
                0x05, 0x08, 0x0B,                  // transport, style, outer size
                0x0D, 0x08,                        // effContainer structure, value size
                0x03, 0x01,                        // replace map; slot 1
                0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x17, // slot-1 effect 0x1AC6F6DC17
                0x78                                // only conContents updated
            });
            WriteByte(0x01);      // one removed node
            WriteBytes(PackNode(_nodeID));
            Log.Write(LogLevel.Client,
                "AreaReplicationDestroy: stream=0x{0:X8} node=0x{1:X16}",
                _streamID, _nodeID);
        }

        /// <summary>
        /// Packed unsigned encoding (0xC7 + byte-length prefix, then big-endian
        /// bytes), matching AreaAbilityEffectReplication.WritePackedUnsigned and
        /// the reader's packed(). For a five-byte node id this yields the 0xCC
        /// prefix seen in CRT2/CRT4 (e.g. 0x0000001AC6F6DC1F -> CC 1A C6 F6 DC 1F).
        /// </summary>
        internal static byte[] PackNode(UInt64 id)
        {
            if (id < 0xC0)
                return new byte[] { (byte)id };

            int length = 0;
            UInt64 remaining = id;
            do
            {
                ++length;
                remaining >>= 8;
            }
            while (remaining != 0);

            byte[] result = new byte[1 + length];
            result[0] = (byte)(0xC7 + length);
            for (int shift = (length - 1) * 8, i = 1; shift >= 0; shift -= 8, i++)
                result[i] = (byte)(id >> shift);
            return result;
        }

        public override PacketType GetType()
        {
            return PacketType.AreaClientReplicationTransaction;
        }

        public override void SetModule(byte inMod) { _module = inMod; }
        public override byte GetModule() { return _module; }
    }
}
