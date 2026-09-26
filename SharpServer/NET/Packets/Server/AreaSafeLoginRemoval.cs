using System;
using System.IO;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Reproduces the server-side end of Safe Login Immunity. CRT2 creates
    /// effect 0x1AC6F6DC1C in slot 2 of positive effect container
    /// 0x1AC6F6DC0E. The client runs PostContainerRemove only when the
    /// container changes, so the container replacement and node removal must
    /// be delivered in the same replication transaction.
    /// </summary>
    class AreaSafeLoginRemoval : TORAreaServerPacket
    {
        private byte _module;
        private readonly UInt32 _streamID;

        public AreaSafeLoginRemoval(UInt32 streamID)
        {
            _streamID = streamID;
        }

        /// <summary>
        /// Removes the immobilizing /0/2 effect from the captured CRT2 source
        /// instead of trying to recreate its later server lifetime. The
        /// offsets and surrounding bytes are asserted against the captured
        /// fixture: slot 2 is removed from positive effContainer DC0E, then
        /// the final DC1C object record is omitted.
        /// </summary>
        internal static byte[] SuppressFromCapturedCreate(byte[] captured)
        {
            const int mapOuterSize = 0x826;
            const int mapInnerSize = 0x828;
            const int mapCount = 0x829;
            const int slotTwoStart = 0x831;
            const int slotTwoEnd = 0x838;
            const int effectRecordStart = 0x1943;

            byte[] slotTwo = new byte[] {
                0x02, 0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x1C
            };
            byte[] effectRecord = new byte[] {
                0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x1C, 0x7A,
                0xCF, 0xE0, 0x00, 0xB3, 0x1E, 0x6D, 0x66, 0x6C, 0x0F
            };

            if (captured.Length != 0x198F || captured[8] != 0x01 ||
                captured[9] != 0x55 || captured[mapOuterSize] != 0x24 ||
                captured[mapInnerSize] != 0x21 || captured[mapCount] != 0x02 ||
                !Matches(captured, slotTwoStart, slotTwo) ||
                !Matches(captured, effectRecordStart, effectRecord))
                throw new InvalidDataException(
                    "CRT2 no longer matches the verified Safe Login capture layout.");

            byte[] result = new byte[effectRecordStart - slotTwo.Length];
            Array.Copy(captured, 0, result, 0, slotTwoStart);
            Array.Copy(captured, slotTwoEnd, result, slotTwoStart,
                effectRecordStart - slotTwoEnd);

            result[9] = 0x54;              // 84 objects instead of 85
            result[mapOuterSize] = 0x1D;  // outer value shrank by seven
            result[mapInnerSize] = 0x1A;  // inner value shrank by seven
            result[mapCount] = 0x01;      // slot 1 remains
            return result;
        }

        private static bool Matches(byte[] data, int offset, byte[] expected)
        {
            if (offset < 0 || offset + expected.Length > data.Length)
                return false;
            for (int i = 0; i < expected.Length; i++)
                if (data[offset + i] != expected[i])
                    return false;
            return true;
        }

        /// <summary>
        /// Adds the lifecycle operation to captured CRT17, whose accepted
        /// transaction already contains both an object-update list and a
        /// removed-node list. The captured tail is one count byte followed by
        /// seventeen six-byte packed node IDs.
        /// </summary>
        internal static byte[] ApplyToFinalCapturedTransaction(byte[] captured)
        {
            const int capturedRemovalCount = 17;
            int removalStart = captured.Length - (1 + capturedRemovalCount * 6);
            if (captured.Length < 10 || captured[8] != 0x03 || captured[9] != 0x01 ||
                removalStart < 10 || captured[removalStart] != capturedRemovalCount)
                throw new InvalidDataException(
                    "CRT17 no longer matches its verified one-object/seventeen-removal framing.");

            byte[] containerUpdate = new byte[] {
                0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x0E,
                0x09,
                0x05, 0x08, 0x0B,
                0x0D, 0x08,
                0x03, 0x01,
                0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x17,
                0x78
            };
            byte[] removedEffect = new byte[] {
                0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x1C
            };

            using (MemoryStream result = new MemoryStream(
                captured.Length + containerUpdate.Length + removedEffect.Length))
            {
                result.Write(captured, 0, 9);
                result.WriteByte(0x02); // original player update + container update
                result.Write(captured, 10, removalStart - 10);
                result.Write(containerUpdate, 0, containerUpdate.Length);
                result.WriteByte(capturedRemovalCount + 1);
                result.Write(captured, removalStart + 1,
                    captured.Length - removalStart - 1);
                result.Write(removedEffect, 0, removedEffect.Length);
                return result.ToArray();
            }
        }

        /// <summary>
        /// Adds schema-derived staMobilityFree and chrPlayerLoaded=true fields
        /// to accepted CRT17.
        /// Structure 26 field 9 is staMobility, field 100 is the captured
        /// modMetaStatComputed_Shared map, and field 129 is chrPlayerLoaded. The
        /// ordered values are enum 0 (staMobilityFree), the byte-identical
        /// captured field-100 value, and Boolean true (chrPlayerLoaded).
        ///
        /// The field-state stream is generated, not hand-packed. This previously
        /// used a 7-byte run-length-encoded stream (DC E7 5D CB 2E 74 80) that
        /// decoded correctly in our own reader but was rejected by the client:
        /// chrPlayerLoaded stayed 0 and ablUserCacheIsFrozen stayed 1, behind a
        /// resolver validated by three passing control fields. The
        /// SWTOR_PLAYERLOADED_ONLY=1 differential then proved the record shape
        /// was the problem, because the same field with the same value DID apply
        /// when it was the only present field. The distinguishing feature is the
        /// stream encoding, so the stream is now emitted the way the generator
        /// proves it round-trips: two bits per field for all 215 fields, no run
        /// codes, 54 bytes. Larger than the captured stream, but the client walks
        /// it by field index, so length is not the constraint — and a stream we
        /// can regenerate and verify beats one tuned by hand.
        ///
        /// Verified offline: the 54 bytes decode to exactly fields 9, 100 and
        /// 129, consuming 53 of 54 bytes, and the whole record reconciles to
        /// outer = 4 + inner 602 + states 54 = 660 = 0x294.
        /// </summary>
        internal static byte[] ApplyMobilityFreeToFinalCapturedTransaction(byte[] captured)
        {
            const int bodyStart = 0x1D;
            const int capturedInnerSize = 600;   // field 100's captured value
            const int stateStart = 0x275;        // captured field-state offset
            const int removalStart = 0x279;
            const int outerSize = 0x294;         // 4 + 602 + 54
            const int innerSize = 0x25A;         // 600 + staMobility + chrPlayerLoaded
            byte[] capturedState = new byte[] { 0xCF, 0x0B, 0x9E, 0xF0 };
            if (captured.Length != 0x2E0 || captured[8] != 0x03 ||
                captured[9] != 0x01 || captured[0x16] != 0xC9 ||
                captured[0x17] != 0x02 || captured[0x18] != 0x60 ||
                captured[0x19] != 0x1A || captured[0x1A] != 0xC9 ||
                captured[0x1B] != 0x02 || captured[0x1C] != 0x58 ||
                !Matches(captured, stateStart, capturedState) ||
                captured[removalStart] != 17)
                throw new InvalidDataException(
                    "CRT17 no longer matches its verified one-object/seventeen-removal framing.");

            // Two bits per field, MSB first, for all 215 fields. State 1 is the
            // two-bit code 01. Only three fields are present, so only three
            // bytes are non-zero: 9 * 2 = 18 bits (byte 2), 100 * 2 = 200 bits
            // (byte 25), 129 * 2 = 258 bits (byte 32).
            byte[] mergedState = new byte[54];
            mergedState[2] = 0x10;   // field 9    staMobility
            mergedState[25] = 0x40;  // field 100  modMetaStatComputed_Shared
            mergedState[32] = 0x10;  // field 129  chrPlayerLoaded

            using (MemoryStream result = new MemoryStream(
                bodyStart + innerSize + mergedState.Length +
                (captured.Length - removalStart)))
            {
                result.Write(captured, 0, bodyStart);
                result.WriteByte(0x00); // staMobilityFree enum value
                result.Write(captured, bodyStart, capturedInnerSize);
                result.WriteByte(0x01); // chrPlayerLoaded=true
                result.Write(mergedState, 0, mergedState.Length);
                result.Write(captured, removalStart,
                    captured.Length - removalStart);
                byte[] merged = result.ToArray();
                // Outer value 0x260 -> 0x294; inner value 0x258 -> 0x25A. Both
                // stay three bytes wide so body_start remains 0x1D.
                merged[0x18] = 0x94;
                merged[0x1C] = 0x5A;
                return merged;
            }
        }

        /// <summary>
        /// Diagnostic differential, enabled with SWTOR_PLAYERLOADED_ONLY=1.
        ///
        /// The three-field merge above is the baseline, but it changes two other
        /// things at the same time as the load flag, so a null result cannot say
        /// whether the merge is malformed or whether the client simply never
        /// applies field 129. This variant changes exactly one thing: it emits a
        /// record whose only present field is 129 (chrPlayerLoaded = true), and
        /// therefore whose only value byte is that Boolean.
        ///
        /// Consequences to be aware of before reading a result:
        ///   - field 9 (staMobility) is not delivered, so this is NOT a movement
        ///     fix and the run may be immobilised again;
        ///   - field 100 (modMetaStatComputed_Shared) is not delivered either, so
        ///     the stat map that the captured CRT17 carried is skipped. That is
        ///     the price of a genuinely minimal record.
        ///
        /// Framing. The three size words are variable-length packed integers, so
        /// writing 59 and 1 with fewer bytes than the captured 608 and 600 would
        /// shift every following offset. Both are therefore re-encoded at the
        /// captured width (c9 = two-byte big-endian payload) so body_start stays
        /// at 0x1D and the captured layout is preserved:
        ///   outer  = 4 (struct id + inner size) + inner 1 + states 54 = 59 = 0x3B
        ///   inner  = 1
        ///   states = 54 bytes, two bits per field for all 215 fields, no run
        ///           codes. The client walks the stream by field index, so an
        ///           uncompressed stream is valid; it is simply larger than the
        ///           captured one.
        ///
        /// The state stream was generated and round-tripped through
        /// Decode-Style7Replication.py: 54 bytes, decoding to exactly one present
        /// field, index 129, consuming 53 of 54 bytes.
        /// </summary>
        internal static byte[] ApplyPlayerLoadedOnlyToFinalCapturedTransaction(byte[] captured)
        {
            const int bodyStart = 0x1D;
            const int stateStart = 0x1E;      // bodyStart + inner 1
            const int removalStart = 0x279;
            const int outerSize = 0x3B;       // 4 + 1 + 54
            const int innerSize = 0x01;
            byte[] capturedState = new byte[] { 0xCF, 0x0B, 0x9E, 0xF0 };
            if (captured.Length != 0x2E0 || captured[8] != 0x03 ||
                captured[9] != 0x01 || captured[0x16] != 0xC9 ||
                captured[0x17] != 0x02 || captured[0x18] != 0x60 ||
                captured[0x19] != 0x1A || captured[0x1A] != 0xC9 ||
                captured[0x1B] != 0x02 || captured[0x1C] != 0x58 ||
                !Matches(captured, 0x275, capturedState) ||
                captured[removalStart] != 17)
                throw new InvalidDataException(
                    "CRT17 no longer matches its verified one-object/seventeen-removal framing.");

            // 54 bytes: thirty-two zero bytes, 0x10 at index 32, twenty-one
            // zero bytes. Only field 129 carries state 1; every other field is
            // state 0 (absent). 129 * 2 = 258 bits in, which is bit 2 of byte 32.
            byte[] states = new byte[54];
            states[32] = 0x10;

            using (MemoryStream result = new MemoryStream(
                stateStart + states.Length + (captured.Length - removalStart)))
            {
                result.Write(captured, 0, bodyStart);
                result.WriteByte(0x01); // chrPlayerLoaded = true, the only value
                result.Write(states, 0, states.Length);
                result.Write(captured, removalStart,
                    captured.Length - removalStart);

                byte[] merged = result.ToArray();
                // Outer value 0x260 -> 0x3B, kept three bytes wide.
                merged[0x16] = 0xC9;
                merged[0x17] = 0x00;
                merged[0x18] = (byte)outerSize;
                // Inner value 0x258 -> 0x01, kept three bytes wide.
                merged[0x1A] = 0xC9;
                merged[0x1B] = 0x00;
                merged[0x1C] = (byte)innerSize;
                return merged;
            }
        }

        /// <summary>
        /// Second diagnostic, SWTOR_MOBILITY_AND_LOADED=1. Emits a record whose
        /// only present fields are 9 (staMobilityFree) and 129 (chrPlayerLoaded).
        /// This is the bisect between the two shapes already observed:
        ///
        ///   {100}            captured, client accepts it, nothing changes
        ///   {129}            chrPlayerLoaded=1, frozen=0, abilities fire
        ///   {9, 100, 129}    chrPlayerLoaded=0, frozen=1, abilities greyed
        ///
        /// The three-field record delivers field 9 — movement is restored — so the
        /// state stream itself is now accepted; the failure is specific to having
        /// 100 and 129 in one record. Dropping 100 keeps mobility and the load
        /// flag together and tells us whether field 100's 600-byte value is what
        /// desynchronises the client's value stream, or whether field 9 is.
        ///
        /// Known cost: the stat map is not delivered, and the single-field run
        /// already suggested that matters — abilities fired but buffs did not
        /// land. So this is a bisect, not the destination. If it passes, the next
        /// question is how to carry field 100 without breaking alignment.
        ///
        /// Framing: inner 2 (one byte per field), states 54, so
        /// outer = 4 + 2 + 54 = 60 = 0x3C. Both size words stay three bytes wide
        /// so body_start remains 0x1D.
        /// </summary>
        internal static byte[] ApplyMobilityAndPlayerLoadedToFinalCapturedTransaction(byte[] captured)
        {
            const int bodyStart = 0x1D;
            const int stateStart = 0x275;        // captured field-state offset
            const int removalStart = 0x279;
            const int outerSize = 0x3C;          // 4 + 2 + 54
            const int innerSize = 0x02;          // staMobility + chrPlayerLoaded
            byte[] capturedState = new byte[] { 0xCF, 0x0B, 0x9E, 0xF0 };
            if (captured.Length != 0x2E0 || captured[8] != 0x03 ||
                captured[9] != 0x01 || captured[0x16] != 0xC9 ||
                captured[0x17] != 0x02 || captured[0x18] != 0x60 ||
                captured[0x19] != 0x1A || captured[0x1A] != 0xC9 ||
                captured[0x1B] != 0x02 || captured[0x1C] != 0x58 ||
                !Matches(captured, stateStart, capturedState) ||
                captured[removalStart] != 17)
                throw new InvalidDataException(
                    "CRT17 no longer matches its verified one-object/seventeen-removal framing.");

            byte[] mergedState = new byte[54];
            mergedState[2] = 0x10;   // field 9    staMobility
            mergedState[32] = 0x10;  // field 129  chrPlayerLoaded

            using (MemoryStream result = new MemoryStream(
                bodyStart + innerSize + mergedState.Length +
                (captured.Length - removalStart)))
            {
                result.Write(captured, 0, bodyStart);
                result.WriteByte(0x00); // staMobilityFree enum value
                result.WriteByte(0x01); // chrPlayerLoaded=true
                result.Write(mergedState, 0, mergedState.Length);
                result.Write(captured, removalStart,
                    captured.Length - removalStart);
                byte[] merged = result.ToArray();
                // 60 and 2 do not fit the captured 0x02xx payloads, so all three
                // bytes of each word are written, not just the low one.
                merged[0x17] = 0x00;
                merged[0x18] = (byte)outerSize;
                merged[0x1B] = 0x00;
                merged[0x1C] = (byte)innerSize;
                return merged;
            }
        }

        /// <summary>
        /// Third diagnostic, SWTOR_STATMAP_AND_LOADED=1. Emits {100, 129} — the
        /// captured stat map plus the load flag, no mobility. This is the one
        /// cell of the matrix that has not been measured:
        ///
        ///   {129}         chrPlayerLoaded=1, gate opens
        ///   {9, 129}      chrPlayerLoaded=0, movement restored
        ///   {9, 100, 129} chrPlayerLoaded=0, movement restored
        ///   {100, 129}    <- this one
        ///
        /// Since {9, 129} already fails, field 9 is implicated and the open
        /// question is whether it is field 9 specifically or any companion.
        /// Passing here means multi-field records are fine and staMobility is
        /// the poison field — which would point at staMobility being
        /// server-authoritative, so the fix is to deliver it in its own
        /// transaction rather than alongside the flag. Failing here means any
        /// second field breaks alignment, and the value-ordering model needs to
        /// be rebuilt from the captured bytes rather than bisected.
        ///
        /// Framing: inner 601 (600 captured + 1), states 54, so
        /// outer = 4 + 601 + 54 = 659 = 0x293. Both size words keep the
        /// captured 0x02xx payload width so body_start remains 0x1D.
        /// </summary>
        internal static byte[] ApplyStatMapAndPlayerLoadedToFinalCapturedTransaction(byte[] captured)
        {
            const int bodyStart = 0x1D;
            const int capturedInnerSize = 600;   // field 100's captured value
            const int stateStart = 0x275;        // captured field-state offset
            const int removalStart = 0x279;
            const int outerSize = 0x293;         // 4 + 601 + 54
            const int innerSize = 0x259;         // 600 + chrPlayerLoaded
            byte[] capturedState = new byte[] { 0xCF, 0x0B, 0x9E, 0xF0 };
            if (captured.Length != 0x2E0 || captured[8] != 0x03 ||
                captured[9] != 0x01 || captured[0x16] != 0xC9 ||
                captured[0x17] != 0x02 || captured[0x18] != 0x60 ||
                captured[0x19] != 0x1A || captured[0x1A] != 0xC9 ||
                captured[0x1B] != 0x02 || captured[0x1C] != 0x58 ||
                !Matches(captured, stateStart, capturedState) ||
                captured[removalStart] != 17)
                throw new InvalidDataException(
                    "CRT17 no longer matches its verified one-object/seventeen-removal framing.");

            byte[] mergedState = new byte[54];
            mergedState[25] = 0x40;  // field 100  modMetaStatComputed_Shared
            mergedState[32] = 0x10;  // field 129  chrPlayerLoaded

            using (MemoryStream result = new MemoryStream(
                bodyStart + innerSize + mergedState.Length +
                (captured.Length - removalStart)))
            {
                result.Write(captured, 0, bodyStart);
                result.Write(captured, bodyStart, capturedInnerSize);
                result.WriteByte(0x01); // chrPlayerLoaded=true
                result.Write(mergedState, 0, mergedState.Length);
                result.Write(captured, removalStart,
                    captured.Length - removalStart);
                byte[] merged = result.ToArray();
                // 659 and 601 exceed a byte, so the cast is explicitly unchecked;
                // only the low byte is stored and the captured 0x02 middle byte
                // is left in place, which is what 0x0293 and 0x0259 require.
                merged[0x18] = unchecked((byte)outerSize);
                merged[0x1C] = unchecked((byte)innerSize);
                return merged;
            }
        }

        /// <summary>
        /// Delivers staMobilityFree in CRT16 as a single-field record, leaving
        /// CRT17 free to carry {100, 129}.
        ///
        /// Why this exists: {9, 129} and {9, 100, 129} both leave chrPlayerLoaded
        /// at 0, while {129}, {100, 129} and the captured {100} all work. Field 9
        /// is the one field that poisons a shared record, so it has to travel
        /// alone. Rather than invent a second packet for the same transaction, it
        /// moves into CRT16, which is also a player-record update for the same
        /// node and whose captured shape is identical to CRT17's.
        ///
        /// CRT16 has flags 0x01 (object-update list only, no removed-node list) and
        /// its record runs to end of file, so the whole payload is replaced:
        ///
        ///   inner  = 1  (one value byte: enum 0, staMobilityFree)
        ///   states = 54, two bits per field, byte 2 set for field 9
        ///   outer  = 4 + 1 + 54 = 59 = 0x3B
        ///   total  = 0x1D + 1 + 54 = 0x54
        ///
        /// The captured field-100 stat map is dropped from CRT16; it is still
        /// delivered by CRT17, so the stat map is not lost. This is the same
        /// shape as the {129} record that was measured working.
        /// </summary>
        internal static byte[] ApplyMobilityFreeToCRT16(byte[] captured)
        {
            const int bodyStart = 0x1D;
            const int outerSize = 0x3B;         // 4 + 1 + 54
            const int innerSize = 0x01;
            byte[] capturedState = new byte[] { 0xCF, 0x0B, 0x9E, 0xF0 };
            // CRT16's record ends at end of file: 0x1D + 588 + 4 = 0x26D.
            if (captured.Length != 0x26D || captured[8] != 0x01 ||
                captured[9] != 0x01 || captured[0x16] != 0xC9 ||
                captured[0x17] != 0x02 || captured[0x18] != 0x54 ||
                captured[0x19] != 0x1A || captured[0x1A] != 0xC9 ||
                captured[0x1B] != 0x02 || captured[0x1C] != 0x4C ||
                !Matches(captured, 0x269, capturedState))
                throw new InvalidDataException(
                    "CRT16 no longer matches its verified one-object framing.");

            byte[] mergedState = new byte[54];
            mergedState[2] = 0x10;   // field 9  staMobility

            using (MemoryStream result = new MemoryStream(
                bodyStart + innerSize + mergedState.Length))
            {
                result.Write(captured, 0, bodyStart);
                result.WriteByte(0x00); // staMobilityFree enum value
                result.Write(mergedState, 0, mergedState.Length);
                byte[] merged = result.ToArray();
                merged[0x17] = 0x00;
                merged[0x18] = (byte)outerSize;
                merged[0x1B] = 0x00;
                merged[0x1C] = (byte)innerSize;
                return merged;
            }
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            WriteAreaComponent();

            WriteUInt32(_streamID);
            WriteUInt32(0); // no schema definitions
            WriteByte(0x03); // object-update list and removed-node list
            WriteByte(0x01); // one object update

            // Update positive effect container 0x1AC6F6DC0E. This is the
            // captured style-8 effContainer/conContents replacement form
            // seen on CRT4: one surviving entry, slot 1 -> 0x1AC6F6DC17.
            WriteBytes(new byte[] {
                0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x0E, // object node
                0x09,                               // update + value
                0x05, 0x08, 0x0B,                  // transport, style, outer size
                0x0D, 0x08,                        // effContainer structure, value size
                0x03, 0x01,                        // replace map; slot 1
                0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x17, // surviving effect node
                0x78                                // only conContents updated
            });

            WriteByte(0x01); // one removed node
            WriteBytes(new byte[] { 0xCC, 0x1A, 0xC6, 0xF6, 0xDC, 0x1C });

            Log.Write(LogLevel.Client,
                "AreaSafeLoginRemoval: stream=0x{0:X8} container=0x1AC6F6DC0E removed=0x1AC6F6DC1C",
                _streamID);
        }

        public override PacketType GetType()
        {
            return PacketType.AreaClientReplicationTransaction;
        }

        public override void SetModule(byte inMod) { _module = inMod; }
        public override byte GetModule() { return _module; }
    }
}
