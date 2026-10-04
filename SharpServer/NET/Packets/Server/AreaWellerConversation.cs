using System;
using System.IO;
using System.Text;

namespace NexusToRServer.NET.Packets.Server
{
    // Opt-in first conversation: captured CRT1 structures 60 and 59.
    // cnvControllerSingle.OnReplicationNodeCreate loads the tree and starts it.
    class AreaWellerConversation : TORAreaServerPacket
    {
        internal const string ConversationName = "cnv.location.tython.class.jedi_knight_new.derrin_weller";
        private byte _module;
        private readonly UInt64 _instance, _controller, _owner;
        private readonly int _endStage;
        public AreaWellerConversation(UInt64 instance, UInt64 controller, UInt64 owner)
            : this(instance, controller, owner, 0) { }
        public AreaWellerConversation(UInt64 instance, UInt64 controller, UInt64 owner, int endStage)
        {
            if (instance == 0 || controller == 0 || owner == 0 || instance == controller)
                throw new ArgumentException("Invalid conversation identities");
            if (endStage < 0 || endStage > 2) throw new ArgumentException("Invalid conversation removal stage");
            _instance = instance; _controller = controller; _owner = owner;
            _endStage = endStage;
        }
        internal static void Packed(Stream output, UInt64 value)
        {
            byte[] bytes = AreaReplicationDestroy.PackNode(value);
            output.Write(bytes, 0, bytes.Length);
        }
        internal static byte[] CreateRecord(UInt64 node, UInt64 classId, byte structure, byte[] values, byte states)
        {
            using (MemoryStream record = new MemoryStream())
            using (MemoryStream body = new MemoryStream())
            {
                Packed(body, structure); Packed(body, (UInt64)values.Length);
                body.Write(values, 0, values.Length); body.WriteByte(states);
                Packed(record, node); record.WriteByte(classId == 0 ? (byte)0x09 : (byte)0x8A);
                if (classId != 0) Packed(record, classId);
                record.WriteByte(5); record.WriteByte(8);
                Packed(record, (UInt64)body.Length);
                byte[] data = body.ToArray(); record.Write(data, 0, data.Length);
                return record.ToArray();
            }
        }
        internal static byte[] BuildRecords(UInt64 instance, UInt64 controller, UInt64 owner)
        {
            using (MemoryStream result = new MemoryStream())
            using (MemoryStream values = new MemoryStream())
            {
                Packed(values, owner);
                byte[] name = Encoding.ASCII.GetBytes(ConversationName);
                Packed(values, (UInt64)name.Length); values.Write(name, 0, name.Length);
                byte[] instanceRecord = CreateRecord(instance, 0x4000000F69261DB2UL, 60, values.ToArray(), 0x50);
                result.Write(instanceRecord, 0, instanceRecord.Length);
                byte[] controllerRecord = CreateRecord(controller, 0x4000000F69261DB0UL, 59, AreaReplicationDestroy.PackNode(instance), 0x40);
                result.Write(controllerRecord, 0, controllerRecord.Length);
                return result.ToArray();
            }
        }
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); WriteAreaComponent();
            WriteUInt32(AreaAbilityEffectReplication.NextStreamID()); WriteUInt32(0);
            if (_endStage == 0)
            {
                WriteByte(1); WriteByte(2);
                WriteBytes(BuildRecords(_instance, _controller, _owner));
            }
            else
            {
                // Separate ordered transactions: the controller's destroy
                // callback still needs a live instance for UninitConversation.
                // Reaffirm only this object's fields, then remove that object.
                WriteByte(3); WriteByte(1);
                UInt64 removed = _endStage == 1 ? _controller : _instance;
                byte[] values;
                using (MemoryStream buffer = new MemoryStream())
                {
                    Packed(buffer, _endStage == 1 ? _instance : _owner);
                    if (_endStage == 2)
                    {
                        byte[] name = Encoding.ASCII.GetBytes(ConversationName);
                        Packed(buffer, (UInt64)name.Length); buffer.Write(name, 0, name.Length);
                    }
                    values = buffer.ToArray();
                }
                WriteBytes(CreateRecord(removed, 0, _endStage == 1 ? (byte)59 : (byte)60,
                    values, _endStage == 1 ? (byte)0x40 : (byte)0x50));
                WriteByte(1); WriteBytes(AreaReplicationDestroy.PackNode(removed));
            }
        }
        public override PacketType GetType() { return PacketType.AreaClientReplicationTransaction; }
        public override void SetModule(byte mod) { _module = mod; }
        public override byte GetModule() { return _module; }
    }
}
