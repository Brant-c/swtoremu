using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace NexusToRServer.AreaServer
{
    public static class CRT
    {
        /// <summary>
        /// When SWTOR_TRACE_AREA_PAYLOADS=1 the exact bytes handed to the area
        /// replication packet are logged, so a captured run can be compared
        /// byte-for-byte against the on-disk .acrt fixture.
        /// </summary>
        private static readonly bool TraceEmit =
            Environment.GetEnvironmentVariable("SWTOR_TRACE_AREA_PAYLOADS") == "1";

        public static byte[] Get(string Area, string AreaID, string AreaCode, int AwarenessID)
        {
            // TODO (?)
            String FileName = String.Format(@"{0}-{1}-{2}.{3}.acrt", Area, AreaID, AreaCode, AwarenessID);
            String FilePath = @"AreaServer\CRT\" + FileName;
            String OverrideDirectory = Environment.GetEnvironmentVariable("SWTOR_CRT_OVERRIDE_DIRECTORY");
            if (!String.IsNullOrEmpty(OverrideDirectory))
            {
                String OverridePath = Path.Combine(OverrideDirectory, FileName);
                if (File.Exists(OverridePath))
                {
                    byte[] OverrideData = File.ReadAllBytes(OverridePath);
                    Log.Write(LogLevel.Warning,
                        "CRT diagnostic override [{0}] path=[{1}] bytes={2} sha256={3}",
                        FileName, OverridePath, OverrideData.Length, Sha256(OverrideData));
                    if (TraceEmit)
                        Log.Write(LogLevel.Client, "CRT bytes [{0}] {1}", FileName, Hex(OverrideData));
                    return OverrideData;
                }
            }

            if (File.Exists(FilePath))
            {
                byte[] Data = File.ReadAllBytes(FilePath);
                Log.Write(LogLevel.Info, "CRT emit [{0}] bytes={1} sha256={2}", FileName, Data.Length, Sha256(Data));
                if (TraceEmit)
                    Log.Write(LogLevel.Client, "CRT bytes [{0}] {1}", FileName, Hex(Data));
                return Data;
            }

            Log.Write(LogLevel.Warning,
                "Could not find AreaCRT [{0}] -> emitting 0 bytes. Set SWTOR_CRT_MISSING_MODE=skip to omit the whole AreaClientReplicationTransaction packet instead of sending an empty one.",
                FileName);
            return (new byte[] { });
        }

        /// <summary>
        /// True when the fixture (or an override of it) exists on disk, without
        /// reading it. Lets a caller decide "drop-in present" vs "emit nothing"
        /// before constructing a replication transaction, so a missing room
        /// stream never becomes a malformed zero-length packet.
        /// </summary>
        public static bool Has(string Area, string AreaID, string AreaCode, int AwarenessID)
        {
            String FileName = String.Format(@"{0}-{1}-{2}.{3}.acrt", Area, AreaID, AreaCode, AwarenessID);
            String OverrideDirectory = Environment.GetEnvironmentVariable("SWTOR_CRT_OVERRIDE_DIRECTORY");
            if (!String.IsNullOrEmpty(OverrideDirectory))
            {
                String OverridePath = Path.Combine(OverrideDirectory, FileName);
                if (File.Exists(OverridePath))
                    return true;
            }
            return File.Exists(@"AreaServer\CRT\" + FileName);
        }

        /// <summary>
        /// True when SWTOR_CRT_MISSING_MODE=skip. A missing .acrt then
        /// suppresses the entire AreaClientReplicationTransaction packet
        /// instead of sending a zero-length one. This separates 'no packet'
        /// from 'empty packet' while diagnosing world entry, because the client
        /// does not treat those two cases the same way.
        /// </summary>
        public static bool SuppressMissingCrt
        {
            get
            {
                return String.Equals(
                    Environment.GetEnvironmentVariable("SWTOR_CRT_MISSING_MODE"),
                    "skip",
                    StringComparison.OrdinalIgnoreCase);
            }
        }

        private static string Sha256(byte[] Data)
        {
            using (SHA256 Alg = SHA256.Create())
            {
                byte[] Hash = Alg.ComputeHash(Data);
                StringBuilder Sb = new StringBuilder(Hash.Length * 2);
                for (int i = 0; i < Hash.Length; i++)
                    Sb.Append(Hash[i].ToString("x2"));
                return Sb.ToString();
            }
        }

        private static string Hex(byte[] Data)
        {
            StringBuilder Sb = new StringBuilder(Data.Length * 3);
            for (int i = 0; i < Data.Length; i++)
                Sb.Append(Data[i].ToString("x2")).Append(' ');
            return Sb.ToString().TrimEnd();
        }
    }
}
