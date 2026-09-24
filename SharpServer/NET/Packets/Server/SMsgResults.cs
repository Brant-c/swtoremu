using System;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// SMSG_RESULTS (0xD5280283) — the reply to a client→server RPC request.
    ///
    /// The client's inbound handler (client RVA 0x25214E -> handler 0x2521A4)
    /// reads, in order:
    ///     string (0x97D270) — result name / key
    ///     string (0x97D270) — result value
    /// then performs the end-of-message check (0x97D020) and dispatches both
    /// strings to the scripting layer.
    ///
    /// The client fires CMsgF96DCDB0 (area pair) and CMsg4A765897 (game-systems
    /// pair) as its own script RPC calls; this reply goes back on the same
    /// The result itself is delivered through OmegaClientObject on the base
    /// Omega proxy route, regardless of which service originated the RPC.
    ///
    /// Two payload forms are supported:
    ///   * text  — WriteString(name) + WriteString(value), i.e.
    ///             Int32(len+1) + bytes + 0x00 per string.
    ///   * raw   — the exact byte blobs, written as Int32(len) + bytes (no
    ///             terminator), which is the encoding the client itself uses for
    ///             the RPC name inside its CMsgF96DCDB0 body.
    /// </summary>
    class SMsgResults : TORGameServerPacket
    {
        private byte _module;
        private UInt16 _sourceHandle;
        private UInt16 _clientServiceID;
        private string _name;
        private string _value;
        private byte[] _rawName;
        private byte[] _rawValue;

        public SMsgResults(string Name, string Value, UInt16 SourceHandle, UInt16 ClientServiceID)
        {
            _name = Name ?? string.Empty;
            _value = Value ?? string.Empty;
            _sourceHandle = SourceHandle;
            _clientServiceID = ClientServiceID;
        }

        public SMsgResults(byte[] RawName, byte[] RawValue, UInt16 SourceHandle, UInt16 ClientServiceID)
        {
            _rawName = RawName ?? new byte[0];
            _rawValue = RawValue ?? new byte[0];
            _sourceHandle = SourceHandle;
            _clientServiceID = ClientServiceID;
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            // Server-to-client routing is destination(client service) in the
            // high word and source(server handle) in the low word.
            WriteUInt32(((UInt32)_clientServiceID << 16) | _sourceHandle);

            if (_rawName != null || _rawValue != null)
            {
                WriteInt32(_rawName == null ? 0 : _rawName.Length);
                if (_rawName != null && _rawName.Length > 0) WriteBytes(_rawName);
                WriteInt32(_rawValue == null ? 0 : _rawValue.Length);
                if (_rawValue != null && _rawValue.Length > 0) WriteBytes(_rawValue);
            }
            else
            {
                WriteString(_name);
                WriteString(_value);
            }
        }

        public override PacketType GetType()
        {
            return PacketType.SMsgResults;
        }

        public override void SetModule(byte inMod)
        {
            _module = inMod;
        }

        public override byte GetModule()
        {
            return _module;
        }
    }
}
