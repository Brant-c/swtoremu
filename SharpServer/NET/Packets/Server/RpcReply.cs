using System;
using System.Text;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Answers the client's own script RPC requests (CMsgF96DCDB0 on the area
    /// service pair, CMsg4A765897 on the game-systems pair) with
    /// SMSG_RESULTS (0xD5280283).
    ///
    /// Rationale: the client's message dispatch handles 0xD5280283 inbound and
    /// reads (string, string) — the result of an RPC. The client re-fires the
    /// same requests forever while we swallow or echo them and the area/world
    /// entry never completes; an RPC request that never yields a result is the
    /// only remaining explanation consistent with every observed log.
    ///
    /// The client's request body is [Int32 len][len bytes] — the RPC name blob —
    /// so the reply's first string is that same name blob, letting the client
    /// match its pending call (mode "mirror", the default).
    ///
    /// Environment control (read at send time; restart the server to change):
    ///   SWTOR_RPC_REPLY_MODE   mirror (default) | results | echo | swallow | ack
    /// Complete is reserved for the independently parsed ability path.
    ///   SWTOR_RPC_RESULT_A     result name  (results mode; default "true")
    ///   SWTOR_RPC_RESULT_B     result value (both modes; default "true")
    /// </summary>
    static class RpcReply
    {
        // SMSG_RESULTS is handled by firestorm.omegafirestormclient.OmegaClientObject,
        // not by the area/game-system service that originated the RPC. The base
        // Omega server proxy is 0x65A7 and its client endpoint is component 0.
        private const UInt16 OmegaServerProxyHandle = 0x65A7;
        private const UInt16 OmegaClientHandle = 0x0000;

        public enum Mode { Mirror, Results, Echo, Swallow, Ack, Complete }

        public static Mode GetMode()
        {
            string env = Environment.GetEnvironmentVariable("SWTOR_RPC_REPLY_MODE");
            if (string.IsNullOrWhiteSpace(env)) return Mode.Mirror;
            Mode m;
            if (Enum.TryParse(env.Trim(), true, out m)) return m;
            return Mode.Mirror;
        }

        /// <summary>
        /// Sends the SMSG_RESULTS reply for a client RPC request.
        /// <paramref name="sourceHandle"/> is the server-side handle of the
        /// service pair the request arrived on (0x65B3 area, 0x65AC game systems).
        /// <paramref name="requestBody"/> is the client's raw body, i.e.
        /// [Int32 len][name bytes] (+ args).
        /// </summary>
        public static void SendResults(TORGameClient client, UInt16 sourceHandle, UInt16 clientServiceID, string opcodeName, byte[] requestBody)
        {
            if (client == null || clientServiceID == 0)
            {
                Log.Write(LogLevel.Client, "RpcReply: {0}: no client/service (svc={1}); result not sent.", opcodeName, clientServiceID);
                return;
            }

            Mode mode = GetMode();
            string a = Environment.GetEnvironmentVariable("SWTOR_RPC_RESULT_A");
            string b = Environment.GetEnvironmentVariable("SWTOR_RPC_RESULT_B");
            if (a == null) a = "true";
            if (b == null) b = "true";

            if (mode == Mode.Mirror)
            {
                // First string = the request's own name blob (as the client
                // encodes it: Int32 length + bytes, no terminator).
                byte[] nameBlob = ExtractNameBlob(requestBody);
                byte[] valueBlob = Encoding.UTF8.GetBytes(b);
                client.SendPacket(new SMsgResults(nameBlob, valueBlob, OmegaServerProxyHandle, OmegaClientHandle));
                Log.Write(LogLevel.Client,
                    "RpcReply: {0}: SMSG_RESULTS (mirror) sent via Omega 0x{1:X4}->0x{2:X4} for origin 0x{3:X4}->0x{4:X4} nameLen={5} value=\u0022{6}\u0022.",
                    opcodeName, OmegaServerProxyHandle, OmegaClientHandle,
                    sourceHandle, clientServiceID, nameBlob.Length, b);
                return;
            }

            client.SendPacket(new SMsgResults(a, b, OmegaServerProxyHandle, OmegaClientHandle));
            Log.Write(LogLevel.Client,
                "RpcReply: {0}: SMSG_RESULTS (text) sent via Omega 0x{1:X4}->0x{2:X4} for origin 0x{3:X4}->0x{4:X4} (\u0022{5}\u0022, \u0022{6}\u0022).",
                opcodeName, OmegaServerProxyHandle, OmegaClientHandle,
                sourceHandle, clientServiceID, a, b);
        }

        /// <summary>
        /// The client's CMsgF96DCDB0/4A765897 body is [Int32 len][len bytes]
        /// (the RPC name the reference server also reads as count+bytes).
        /// Returns the name bytes; falls back to the whole body.
        /// </summary>
        private static byte[] ExtractNameBlob(byte[] body)
        {
            if (body == null || body.Length == 0) return new byte[0];
            if (body.Length >= 4)
            {
                int len = BitConverter.ToInt32(body, 0);
                if (len >= 0 && 4 + len <= body.Length)
                {
                    byte[] name = new byte[len];
                    Array.Copy(body, 4, name, 0, len);
                    return name;
                }
            }
            return body;
        }
    }
}
