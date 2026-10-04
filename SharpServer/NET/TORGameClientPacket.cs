using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace NexusToRServer.NET
{
    public abstract class TORGameClientPacket : IPacket
    {

        public abstract void RunImplementation();
        public abstract void ReadImplementation();
        public abstract PacketType GetType();

        private UInt32 _component;

        public UInt32 Component
        {
            get { return _component; }
            set { _component = value; }
        }

        public override bool Read()
        {
            try
            {
                ReadImplementation();
                return true;
            }
            catch (Exception ex)
            {
                var decode = ex as Protocol.PacketDecodeException;
                long offset = decode != null ? decode.Offset : (_stream == null ? 0 : _stream.Position);
                string component = _buffer != null && _buffer.Length >= 8
                    ? "0x" + BitConverter.ToUInt32(_buffer, 4).ToString("X8") : "unavailable";
                Log.Write(LogLevel.Error, "Rejected decode opcode=0x{0:X8} component={1} length={2} offset={3} reason={4}",
                    (uint)GetType(), component, _buffer == null ? 0 : _buffer.Length, offset, ex.Message);
            }
            return false;
        }

        public override void Run()
        {
            try
            {
                RunImplementation();

                // TODO: Possibly spawn protection
            }
            catch(Exception e)
            {
                Log.Write(LogLevel.Error, "Failed running '{0}'\n{1}", GetType().ToString(), e);

                // TODO: Check if the error occured when the player was entering the world
                // If so, kick him out of the game
            }
        }
    }
}
