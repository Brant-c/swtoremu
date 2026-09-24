using System;
using System.IO;
using System.Text;

namespace NexusToRServer.NET.Packets.Client
{
    class SendScriptError : TORGameClientPacket
    {
        private string _message, _trace;
        private UInt64 _characterId, _areaId;

        private string ReadErrorText()
        {
            UInt32 length = ReadUInt32();
            if (length > _stream.Length - _stream.Position) throw new InvalidDataException("Script error text exceeds packet length.");
            byte[] bytes = ReadBytes((int)length);
            int count = bytes.Length;
            if (count > 0 && bytes[count - 1] == 0) count--;
            return Encoding.UTF8.GetString(bytes, 0, count);
        }

        public override void ReadImplementation()
        {
            ReadUInt32();
            ReadUInt32();
            _message = ReadErrorText();
            _trace = ReadErrorText();
            _characterId = ReadUInt64();
            _areaId = ReadUInt64();
        }

        public override void RunImplementation()
        {
            Log.Write(LogLevel.Warning, "Client script error: msg=[{0}] trace=[{1}] char={2} area={3}", _message, _trace, _characterId, _areaId);
        }

        public override PacketType GetType() { return PacketType.SendScriptError; }
    }
}
