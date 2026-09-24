using System;
using System.Text;

namespace NexusToRServer.NET
{
    /// <summary>
    /// Decodes packets this server has no handler for, so a single run produces
    /// a definitive record of what the client actually sent and whether it is
    /// related to the area service.
    ///
    /// Observed framing for the unhandled opcodes seen during world entry
    /// (C586BD22, F96DCDB0, 4A765897):
    ///     [uint32 packetType][uint32 routing][uint32 length][length bytes]
    /// where 'routing' packs the source service in the high 16 bits and the
    /// destination in the low 16 bits, e.g. 08 00 B3 65 -> source 0x65B3
    /// (AreaServer), destination 0x0008 (the client).
    /// </summary>
    internal static class UnknownPacketTrace
    {
        /// <summary>Area service id observed on area-bound traffic.</summary>
        private const uint AreaServiceId = 0x65B3;

        public static string Describe(byte[] data)
        {
            if (data == null || data.Length == 0)
                return "  decode: (no payload)";

            StringBuilder sb = new StringBuilder();
            sb.AppendFormat("  decode: bytes={0} type=0x{1:X8}", data.Length, ReadUInt32(data, 0));

            if (data.Length < 8)
            {
                sb.AppendFormat(" tail={0}", Hex(data, 0, data.Length));
                return sb.ToString();
            }

            uint routing = ReadUInt32(data, 4);
            uint source = routing >> 16;
            uint destination = routing & 0xFFFF;
            sb.AppendFormat(" routing=0x{0:X8} source=0x{1:X4} destination=0x{2:X4} sourceIsAreaServer={3}",
                routing, source, destination, source == AreaServiceId ? "yes" : "no");

            if (data.Length < 12)
            {
                sb.AppendFormat(" tail={0}", Hex(data, 8, data.Length - 8));
                return sb.ToString();
            }

            // 'declaredLength' is the field at offset 8. 'body' is what actually
            // followed the 12-byte header. Reporting the signed difference shows
            // directly whether the length field counts the trailing checksum byte
            // or not, which is not yet established for these opcodes.
            uint declared = ReadUInt32(data, 8);
            int body = data.Length - 12;
            sb.AppendFormat(" declaredLength={0} bodyBytes={1} delta={2}",
                declared, body, body - (long)declared);
            if (body > 0)
                sb.AppendFormat(" body({0})={1}", body, Hex(data, 12, body));

            return sb.ToString();
        }

        private static uint ReadUInt32(byte[] data, int offset)
        {
            return (uint)(data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16) | (data[offset + 3] << 24));
        }

        private static string Hex(byte[] data, int offset, int count)
        {
            StringBuilder sb = new StringBuilder(count * 3);
            for (int i = 0; i < count; i++)
                sb.Append(data[offset + i].ToString("x2")).Append(' ');
            return sb.ToString().TrimEnd();
        }
    }
}
