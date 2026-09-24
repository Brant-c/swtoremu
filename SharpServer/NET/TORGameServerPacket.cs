using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;
using System.Security.Cryptography;
using ComponentAce.Compression.Libs.zlib;

namespace NexusToRServer.NET
{
    public abstract class TORGameServerPacket : SPacket
    {
        protected Boolean _invisible = false;
        private Boolean _enc = true;
        private Boolean _def = true;

        public abstract void WriteImplementation();
        public void RunImplementation() { }

        /// <summary>
        /// Prevent packets from 'invisible' players from being broadcasted
        /// </summary>
        public Boolean Invisible
        {
            get { return _invisible; }
            set { _invisible = value; }
        }

        public Boolean Encrypted
        {
            get { return _enc; }
            set { _enc = value; }
        }

        public Boolean Deflated
        {
            get { return _def; }
            set { _def = value; }
        }

        /// <summary>
        /// True when this packet must not be transmitted at all. Used by the area
        /// replication packet so that 'send no packet' can be distinguished from
        /// 'send an empty packet' while diagnosing world entry, because a
        /// zero-length replication transaction is itself malformed.
        /// </summary>
        public virtual Boolean SuppressSend
        {
            get { return false; }
        }

        public override void Write()
        {
            try
            {
                WriteImplementation();
            }
            catch
            {
                Log.Write(LogLevel.Error, "Failed writing '{0}'", GetType().ToString());
            }
        }

        public byte[] Construct(IStreamCipher encryptor, ZStream dStream)
        {
            Log.Write(LogLevel.Client, "Constructing Packet [{0}]", GetType().ToString());

            byte[] cData = _stream.ToArray();

            // Opt-in diagnostics at the plaintext serialization boundary.
            // Do not include login/repository traffic or unbounded payloads.
            if (this is TORAreaServerPacket &&
                Environment.GetEnvironmentVariable("SWTOR_TRACE_AREA_PAYLOADS") == "1")
            {
                int prefixLength = Math.Min(cData.Length, 256);
                Log.Write(LogLevel.Client,
                    "AREA-PAYLOAD type={0} bytes={1} prefixBytes={2} hex={3}",
                    GetType().ToString(), cData.Length, prefixLength,
                    BitConverter.ToString(cData, 0, prefixLength));
            }

            if (this is Packets.Server.SMsgResults)
            {
                Log.Write(LogLevel.Client,
                    "SMSG-RESULTS-PLAINTEXT bytes={0} hex={1}",
                    cData.Length, BitConverter.ToString(cData));
            }

            if (_def)
            {
                MemoryStream lStream = new MemoryStream();

                dStream.avail_in = cData.Length;
                dStream.next_in = cData;
                dStream.next_in_index = 0;

                byte[] dData = new byte[cData.Length * 2];

                dStream.avail_out = cData.Length * 2;
                dStream.next_out = dData;
                dStream.next_out_index = 0;

                dStream.deflate(2);

                lStream.Write(dData, 0, (cData.Length * 2) - dStream.avail_out);
                cData = lStream.ToArray();
                lStream.Dispose();
            }

            MemoryStream oStream = new MemoryStream();
            EndianBinaryWriter oWriter = new EndianBinaryWriter(MiscUtil.Conversion.EndianBitConverter.Little, oStream);

            oWriter.Write((byte)GetModule());
            oWriter.Write((UInt32)cData.Length + 2);
            oWriter.Write((byte)GenerateChecksum(oStream.ToArray()));
            oWriter.Write(cData, 0, cData.Length - 4);

            byte[] fData = oStream.ToArray();

            if (_enc)
            {
                byte[] eData = new byte[fData.Length];
                encryptor.ProcessBytes(fData, 0, fData.Length, eData, 0);
                fData = eData;
            }

            return fData;
        }

        public abstract PacketType GetType();
        public abstract void SetModule(byte inMod);
        public abstract byte GetModule();
    }
}
