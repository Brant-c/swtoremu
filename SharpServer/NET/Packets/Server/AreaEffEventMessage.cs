using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    class AreaEffEventMessage : TORAreaServerPacket
    {
        private byte _module;
        private byte[] _aeff;

        public AreaEffEventMessage(String Area, String AreaID, String AreaCode, int EffectID)
            : this(Area, AreaID, AreaCode, EffectID, 0)
        {
        }

        public AreaEffEventMessage(String Area, String AreaID, String AreaCode, int EffectID, UInt64 CharacterID)
        {
            //
            _aeff = CapturedCharacterRemap.Apply(
                AreaServer.EffectEvents.Get(Area, AreaID, AreaCode, EffectID), CharacterID,
                "effect " + EffectID.ToString());
        }

        private AreaEffEventMessage(byte[] payload)
        {
            _aeff = payload;
        }

        /// <summary>
        /// Builds the first deliberately dynamic effect-event experiment from
        /// the zero-length-action safe-login capture. The JP effEvent metadata and
        /// msg_area_eff_event_message.h agree on the optional-field mapping:
        /// bit 0x02 is effEventActivateRequestId (UInt16), bit 0x08 is
        /// effEventEffectSpec, and bit 0x20 is effEventExpiration.
        ///
        /// Capture byte 8 is the action enum (AddEffect), and bytes 9..12 are
        /// its UInt32 string length. They are ordinary action fields, not a
        /// CheckedFrame header, and must remain untouched.
        /// </summary>
        public static AreaEffEventMessage CreateAbilityExperiment(String Area,
            String AreaID, String AreaCode, UInt64 characterID,
            UInt64 effectSpecID, UInt16 requestID, byte subEffectNumber)
        {
            byte[] captured = CapturedCharacterRemap.Apply(
                AreaServer.EffectEvents.Get(Area, AreaID, AreaCode, 1),
                characterID, "ability effect template");
            if (captured == null || captured.Length != 86 || captured[57] != 0x28)
                throw new InvalidDataException(
                    "Ability effect template is not the expected 86-byte action-free event.");

            byte[] payload = new byte[captured.Length + 2];
            Buffer.BlockCopy(captured, 0, payload, 0, 58);
            Buffer.BlockCopy(captured, 58, payload, 60, captured.Length - 58);

            payload[54] = subEffectNumber;
            payload[55] = 7;       // effTrigger_OnApply
            payload[56] = 1;       // effResultOk
            payload[57] = 0x2A;    // request ID + effect spec + expiration
            WriteUInt16(payload, 58, requestID);
            WriteUInt64(payload, 60, effectSpecID);

            // Give each request distinct transaction/effect-instance IDs so a
            // second cast cannot alias the first event in the client maps.
            UInt64 eventBase = 0x00001AC700000000UL + ((UInt64)requestID << 4);
            WriteUInt64(payload, 30, eventBase + 1);
            WriteUInt64(payload, 46, eventBase + 2);
            return new AreaEffEventMessage(payload);
        }

        /// <summary>
        /// Builds an action-bearing effect event from capture 2. Byte 8 is the
        /// action enum and bytes 9..12 are the UInt32 length (19) of the decimal
        /// character-ID action value at bytes 13..31. Optional request/called-by
        /// fields are inserted before the effect specification in schema order.
        /// </summary>
        public static AreaEffEventMessage CreateAbilityActionExperiment(
            String Area, String AreaID, String AreaCode, UInt64 characterID,
            UInt64 effectSpecID, UInt16 requestID, byte subEffectNumber,
            byte action, UInt64 calledByTransactionID, UInt64 sequence,
            out UInt64 transactionID)
        {
            byte[] captured = CapturedCharacterRemap.Apply(
                AreaServer.EffectEvents.Get(Area, AreaID, AreaCode, 2),
                characterID, "ability action template");
            if (captured == null || captured.Length != 104 ||
                captured[8] != 44 || BitConverter.ToUInt32(captured, 9) != 19 ||
                captured[75] != 0x28)
                throw new InvalidDataException(
                    "Ability action template is not the expected 104-byte event.");

            string actionValue = characterID.ToString(
                System.Globalization.CultureInfo.InvariantCulture);
            if (actionValue.Length != 19)
                throw new InvalidDataException(
                    "Ability action template requires a 19-digit character ID.");

            bool hasRequest = requestID != 0;
            bool hasCalledBy = calledByTransactionID != 0;
            if (hasRequest && hasCalledBy)
                throw new InvalidDataException(
                    "Ability action event cannot carry both request and dependency IDs.");

            int inserted = hasCalledBy ? 8 : hasRequest ? 2 : 0;
            byte[] payload = new byte[captured.Length + inserted];
            Buffer.BlockCopy(captured, 0, payload, 0, 76);
            Buffer.BlockCopy(captured, 76, payload, 76 + inserted,
                captured.Length - 76);

            payload[8] = action;
            byte[] actionBytes = Encoding.ASCII.GetBytes(actionValue);
            Buffer.BlockCopy(actionBytes, 0, payload, 13, actionBytes.Length);
            payload[32] = 1;       // effEventActionDetailsResult = effResultOk
            payload[46] = 1;       // effEventTargetDetailsResult = effResultOk
            payload[72] = subEffectNumber;
            payload[73] = 7;       // effTrigger_OnApply
            payload[74] = 1;       // effEventResult = effResultOk

            UInt64 eventBase = 0x00001AC700000000UL + (sequence << 4);
            WriteUInt64(payload, 48, eventBase + 1); // target effect instance
            transactionID = eventBase + 2;
            WriteUInt64(payload, 64, transactionID);

            int effectOffset = 76;
            if (hasRequest)
            {
                payload[75] = 0x2A; // request ID + effect spec + expiration
                WriteUInt16(payload, effectOffset, requestID);
                effectOffset += 2;
            }
            else if (hasCalledBy)
            {
                payload[75] = 0x2C; // called-by + effect spec + expiration
                WriteUInt64(payload, effectOffset, calledByTransactionID);
                effectOffset += 8;
            }
            else
            {
                payload[75] = 0x28; // effect spec + expiration
            }
            WriteUInt64(payload, effectOffset, effectSpecID);
            return new AreaEffEventMessage(payload);
        }

        /// <summary>
        /// Builds the dependent persistent effect from capture 1's native
        /// AddEffect action. Unlike AbilityActivate, AddEffect has an empty
        /// action value (UInt32 length zero), so retaining the activation
        /// template's 19-byte character string would change its semantics.
        /// </summary>
        public static AreaEffEventMessage CreateAbilityAddEffectExperiment(
            String Area, String AreaID, String AreaCode, UInt64 characterID,
            UInt64 effectSpecID, UInt64 calledByTransactionID, UInt64 sequence,
            out UInt64 transactionID)
        {
            byte[] captured = CapturedCharacterRemap.Apply(
                AreaServer.EffectEvents.Get(Area, AreaID, AreaCode, 1),
                characterID, "ability add-effect template");
            if (captured == null || captured.Length != 86 ||
                captured[8] != 87 || BitConverter.ToUInt32(captured, 9) != 0 ||
                captured[57] != 0x28)
                throw new InvalidDataException(
                    "Ability AddEffect template is not the expected 86-byte event.");

            byte[] payload = new byte[captured.Length + 8];
            Buffer.BlockCopy(captured, 0, payload, 0, 58);
            Buffer.BlockCopy(captured, 58, payload, 66, captured.Length - 58);

            UInt64 eventBase = 0x00001AC700000000UL + (sequence << 4);
            WriteUInt64(payload, 30, eventBase + 1); // target effect instance
            transactionID = eventBase + 2;
            WriteUInt64(payload, 46, transactionID);

            payload[54] = 0;
            payload[55] = 7;       // effTrigger_OnApply
            payload[56] = 1;       // effEventResult = effResultOk
            payload[57] = 0x2C;    // called-by + effect spec + expiration
            WriteUInt64(payload, 58, calledByTransactionID);
            WriteUInt64(payload, 66, effectSpecID);
            return new AreaEffEventMessage(payload);
        }

        private static void WriteUInt16(byte[] output, int offset, UInt16 value)
        {
            byte[] bytes = BitConverter.GetBytes(value);
            Buffer.BlockCopy(bytes, 0, output, offset, bytes.Length);
        }

        private static void WriteUInt32(byte[] output, int offset, UInt32 value)
        {
            byte[] bytes = BitConverter.GetBytes(value);
            Buffer.BlockCopy(bytes, 0, output, offset, bytes.Length);
        }

        private static void WriteUInt64(byte[] output, int offset, UInt64 value)
        {
            byte[] bytes = BitConverter.GetBytes(value);
            Buffer.BlockCopy(bytes, 0, output, offset, bytes.Length);
        }

        /// <summary>
        /// Writes and Constructs the specified Packet
        /// </summary>
        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType()); // Packet Type
            WriteAreaComponent();

            WriteInt32(_aeff.Length);
            WriteBytes(_aeff);
        }

        /// <summary>
        /// Returns the PacketType of the specified Packet
        /// </summary>
        /// <returns>PacketType of specified Packet</returns>
        public override PacketType GetType()
        {
            return PacketType.AreaEffEventMessage;
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
