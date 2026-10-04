using System;
using System.IO;

namespace NexusToRServer.NET.Protocol
{
    // Bounded reads; offsets are relative to the supplied plaintext packet.
    // Hero packed support is deliberately limited to transport version 5.
    public sealed class PacketCursor
    {
        private readonly byte[] bytes;
        public int Offset { get; private set; }
        public int Remaining { get { return bytes.Length - Offset; } }
        public int FailureOffset { get; private set; }
        public string FailureReason { get; private set; }

        public PacketCursor(byte[] bytes)
        {
            this.bytes = bytes ?? new byte[0];
            FailureOffset = -1;
        }

        public bool Reject(int offset, string reason)
        {
            if (FailureReason == null) { FailureOffset = offset; FailureReason = reason; }
            return false;
        }

        private bool Require(int count)
        {
            if (FailureReason != null) return false;
            return count >= 0 && count <= Remaining || Reject(Offset, "truncated field: need " + count + ", remaining " + Remaining);
        }

        public bool TryReadUInt32(out uint value)
        {
            value = 0;
            if (!Require(4)) return false;
            for (int i = 0; i < 4; i++) value |= (uint)bytes[Offset + i] << (8 * i);
            Offset += 4;
            return true;
        }

        public bool TryReadSingle(out float value)
        {
            uint bits;
            value = 0;
            if (!TryReadUInt32(out bits)) return false;
            value = BitConverter.ToSingle(BitConverter.GetBytes(bits), 0);
            return true;
        }

        public bool TryReadBytes(int count, out byte[] value)
        {
            value = null;
            if (!Require(count)) return false;
            value = new byte[count];
            Array.Copy(bytes, Offset, value, 0, count);
            Offset += count;
            return true;
        }

        // Local reference: Tools/Hero/Hero/PackedStream.cs Read/Write(ulong/long).
        // Multi-byte magnitudes are big endian, unlike fixed movement fields.
        private bool TryReadPacked(bool signed, out ulong magnitude, out bool negative)
        {
            magnitude = 0;
            negative = false;
            if (!Require(1)) return false;
            int start = Offset;
            byte token = bytes[start];
            if (token < 0xC0) { magnitude = token; Offset++; return true; }
            if (signed && token == 0xD0) { magnitude = 0x8000000000000000UL; negative = true; Offset++; return true; }
            int count;
            if (token >= 0xC8 && token <= 0xCF) count = token - 0xC7;
            else if (signed && token <= 0xC7) { count = token - 0xBF; negative = true; }
            else return Reject(start, "invalid Hero v5 packed token");
            if (!Require(1 + count)) return false;
            for (int i = 1; i <= count; i++) magnitude = (magnitude << 8) | bytes[start + i];
            if (signed && magnitude > (negative ? 0x8000000000000000UL : 0x7FFFFFFFFFFFFFFFUL))
                return Reject(start, "Hero signed magnitude overflow");
            Offset += count + 1;
            return true;
        }

        public bool TryReadPackedUnsigned(out ulong value)
        {
            bool negative;
            return TryReadPacked(false, out value, out negative);
        }

        public bool TryReadPackedSigned(out long value)
        {
            ulong magnitude;
            bool negative;
            value = 0;
            if (!TryReadPacked(true, out magnitude, out negative)) return false;
            value = negative ? unchecked(-(long)magnitude) : (long)magnitude;
            return true;
        }

        public bool TryEnd()
        {
            if (FailureReason != null) return false;
            return Remaining == 0 || Reject(Offset, "unexpected trailing bytes: " + Remaining);
        }

        public PacketDecodeException Error() { return new PacketDecodeException(FailureOffset, FailureReason); }
    }

    public sealed class PacketDecodeException : IOException
    {
        public int Offset { get; private set; }
        public PacketDecodeException(int offset, string reason) : base(reason) { Offset = offset; }
    }
}
