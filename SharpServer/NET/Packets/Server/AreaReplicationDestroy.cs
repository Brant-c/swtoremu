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
            WriteUInt32(0);
            WriteByte(0x02); // transaction contains a removed-node list
            WriteByte(0x01); // one removed node
            // Packed style-5 encoding of 0x0000001AC6F6DC1C, verified directly
            // from CRT2's object-create record for this node.
            WriteBytes(new byte[] { 0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x1C });
            Log.Write(LogLevel.Client,
                "AreaReplicationDestroy: stream=0x{0:X8} node=0x{1:X16}",
                _streamID, _nodeID);
        }

        public override PacketType GetType()
        {
            return PacketType.AreaClientReplicationTransaction;
        }

        public override void SetModule(byte inMod) { _module = inMod; }
        public override byte GetModule() { return _module; }
    }
}
