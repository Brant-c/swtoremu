using System;
using System.IO;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    /// <summary>
    /// Traceable area-poll dispatcher.  Lets us switch between echo, swallow, and
    /// experimental ack replies for the periodic area opcodes without touching
    /// every handler.  Controlled by environment variables so a single build can
    /// be re-run under different modes.
    /// </summary>
    static class AreaPollExperiment
    {
        public enum ReplyMode { Echo, Swallow, Ack }

        public static ReplyMode GetMode(string opcodeName)
        {
            string env = Environment.GetEnvironmentVariable("SWTOR_AREA_POLL_MODE");
            if (string.IsNullOrWhiteSpace(env))
                return ReplyMode.Echo; // default: preserve current behavior

            // Per-opcode override wins: "CMsgF96DCDB0=Swallow;CMsg61116AD5=Ack"
            foreach (string part in env.Split(';', ','))
            {
                string trimmed = part.Trim();
                if (string.IsNullOrEmpty(trimmed)) continue;
                int eq = trimmed.IndexOf('=');
                if (eq < 0) continue;
                string key = trimmed.Substring(0, eq).Trim();
                string val = trimmed.Substring(eq + 1).Trim();
                if (key.Equals(opcodeName, StringComparison.OrdinalIgnoreCase))
                {
                    ReplyMode m;
                    if (Enum.TryParse(val, true, out m))
                        return m;
                }
            }

            // Global shorthand: "Swallow" or "Ack" applies to all tracked opcodes.
            ReplyMode global;
            if (Enum.TryParse(env, true, out global))
                return global;

            return ReplyMode.Echo;
        }

        public static void LogPoll(TORGameClient client, string opcodeName, UInt32 component, byte[] body, string extra)
        {
            string svc = client == null ? "no-client" : client.AreaServiceID.ToString();
            string placed = (client == null || client.ActiveCharacter == null) ? "none" : client.ActiveCharacter._id.ToString();
            string hex = body == null ? "(null)" : BitConverter.ToString(body);
            Log.Write(LogLevel.Client,
                "AREA-POLL {0}: component=0x{1:X8} len={2} placed={3} areaSvc={4} mode={5}{6} body={7}",
                opcodeName, component, body == null ? 0 : body.Length, placed, svc,
                GetMode(opcodeName), string.IsNullOrEmpty(extra) ? "" : " " + extra, hex);
        }

        public static void LogDecision(TORGameClient client, string opcodeName, string decision)
        {
            Log.Write(LogLevel.Client, "AREA-POLL {0}: decision={1}", opcodeName, decision);
        }
    }
}
