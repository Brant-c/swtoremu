using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// Creates one server-authoritative positive effEffect instance and puts it
    /// in the player's captured positive-effect container.
    ///
    /// The record shape is copied from the smaller of the two real effEffect
    /// creates in Tython CRT2. Timed effects additionally carry effStartTime
    /// and effEndTime in the same FILETIME-millisecond representation as the
    /// captured Safe Login effect. The container replacement uses the same
    /// accepted style-8 form as AreaSafeLoginRemoval.
    /// </summary>
    class AreaAbilityEffectReplication : TORAreaServerPacket
    {
        private const UInt64 PositiveContainerNode = 0x0000001AC6F6DC0EUL;
        private const UInt64 CapturedSlotOneNode = 0x0000001AC6F6DC17UL;
        private const UInt64 StackLimitComponent = 0x40000004B0ACC610UL;

        private static Int32 _nextStreamID = 0x001B502D;
        internal static UInt32 NextStreamID() { return unchecked((UInt32)Interlocked.Increment(ref _nextStreamID)); }
        private static Int32 _nextNodeSuffix;
        internal static UInt64 NextNodeID()
        {
            return 0x0000001AC7000000UL + unchecked((UInt32)Interlocked.Increment(ref _nextNodeSuffix));
        }

        private byte _module;
        private readonly UInt32 _streamID;
        private readonly UInt64 _nodeID;
        private readonly UInt64 _oldNodeID;
        private readonly UInt64 _effectSpecID;
        private readonly UInt64 _characterID;
        private readonly UInt64 _startTime;
        private readonly UInt64 _endTime;
        private readonly SortedDictionary<byte, UInt64> _containerEffects;
        private readonly UInt64[] _modalActiveSpecs;
        private readonly SortedDictionary<UInt64,
            SortedDictionary<UInt64, float>> _sharedMetaStats;
        private readonly SortedDictionary<UInt64, float> _computedStats;
        private readonly SortedDictionary<UInt64,
            SortedDictionary<UInt64, float>> _fixedModifiers;
        private readonly SortedDictionary<UInt64,
            SortedDictionary<UInt64, float>> _percentModifiers;
        private readonly UInt64[] _affectedModifierStats;
        private readonly bool _isRemoval;
        private readonly bool _isStatRefresh;
        private readonly bool? _fightingState;

        public AreaAbilityEffectReplication(UInt64 characterID,
            UInt64 effectSpecID, Int64 durationMilliseconds,
            UInt64 oldNodeID, byte slot,
            IDictionary<byte, UInt64> retainedEffects,
            IEnumerable<UInt64> modalActiveSpecs,
            IDictionary<UInt64, IDictionary<UInt64, float>> sharedMetaStats,
            IDictionary<UInt64, float> computedStats,
            IDictionary<UInt64, float> fixedModifiers,
            IDictionary<UInt64, float> percentOfCurrent)
        {
            if (durationMilliseconds < 0)
                throw new ArgumentOutOfRangeException("durationMilliseconds");
            _characterID = characterID;
            _effectSpecID = effectSpecID;
            _oldNodeID = oldNodeID;
            if (durationMilliseconds > 0)
            {
                _startTime = AreaUpdateTimeSource.GetFileTimeMillisecondsUtc();
                _endTime = checked(_startTime +
                    (UInt64)durationMilliseconds);
            }
            _streamID = unchecked((UInt32)Interlocked.Increment(ref _nextStreamID));

            // Stay in the capture's five-byte node-ID magnitude so every size
            // asserted below remains stable. The server is restarted per trace
            // run, and a suffix is never reused during that process.
            _nodeID = NextNodeID();

            _containerEffects = new SortedDictionary<byte, UInt64>();
            if (retainedEffects != null)
                foreach (KeyValuePair<byte, UInt64> entry in retainedEffects)
                    _containerEffects[entry.Key] = entry.Value;
            _containerEffects[slot] = _nodeID;
            _modalActiveSpecs = modalActiveSpecs == null ? null :
                modalActiveSpecs.Distinct().OrderBy(value => value).ToArray();
            _sharedMetaStats = CopySharedMetaStats(sharedMetaStats);
            _computedStats = CopyStats(computedStats);
            _fixedModifiers = CreateSingleSourceModifiers(fixedModifiers,
                _nodeID);
            _percentModifiers = CreateSingleSourceModifiers(percentOfCurrent,
                _nodeID);
            _affectedModifierStats = _fixedModifiers.Keys.Concat(
                _percentModifiers.Keys).Distinct().OrderBy(value => value)
                .ToArray();
        }

        private AreaAbilityEffectReplication(UInt64 characterID,
            UInt64 removedNodeID,
            IDictionary<byte, UInt64> retainedEffects,
            IEnumerable<UInt64> modalActiveSpecs,
            IDictionary<UInt64, float> recomputedStats,
            IDictionary<UInt64, IDictionary<UInt64, float>> fixedModifiers,
            IDictionary<UInt64, IDictionary<UInt64, float>> percentModifiers,
            IEnumerable<UInt64> affectedModifierStats)
        {
            if (removedNodeID == 0)
                throw new ArgumentOutOfRangeException("removedNodeID");
            _characterID = characterID;
            _oldNodeID = removedNodeID;
            _streamID = unchecked((UInt32)Interlocked.Increment(
                ref _nextStreamID));
            _containerEffects = new SortedDictionary<byte, UInt64>();
            if (retainedEffects != null)
                foreach (KeyValuePair<byte, UInt64> entry in retainedEffects)
                    _containerEffects[entry.Key] = entry.Value;
            _modalActiveSpecs = modalActiveSpecs == null ? new UInt64[0] :
                modalActiveSpecs.Distinct().OrderBy(value => value).ToArray();
            _sharedMetaStats = new SortedDictionary<UInt64,
                SortedDictionary<UInt64, float>>();
            _computedStats = CopyStats(recomputedStats);
            _fixedModifiers = CopyModifierMaps(fixedModifiers);
            _percentModifiers = CopyModifierMaps(percentModifiers);
            _affectedModifierStats = affectedModifierStats == null ?
                new UInt64[0] : affectedModifierStats.Distinct()
                    .OrderBy(value => value).ToArray();
            _isRemoval = true;
        }

        public static AreaAbilityEffectReplication CreateRemoval(
            UInt64 characterID, UInt64 removedNodeID,
            IDictionary<byte, UInt64> retainedEffects,
            IEnumerable<UInt64> modalActiveSpecs,
            IDictionary<UInt64, float> recomputedStats,
            IDictionary<UInt64, IDictionary<UInt64, float>> fixedModifiers,
            IDictionary<UInt64, IDictionary<UInt64, float>> percentModifiers,
            IEnumerable<UInt64> affectedModifierStats)
        {
            return new AreaAbilityEffectReplication(characterID,
                removedNodeID, retainedEffects, modalActiveSpecs,
                recomputedStats, fixedModifiers, percentModifiers,
                affectedModifierStats);
        }

        private AreaAbilityEffectReplication(UInt64 characterID,
            bool fightingState, IDictionary<UInt64, float> recomputedStats,
            IDictionary<UInt64, IDictionary<UInt64, float>> fixedModifiers,
            IDictionary<UInt64, IDictionary<UInt64, float>> percentModifiers,
            IEnumerable<UInt64> affectedModifierStats)
        {
            _characterID = characterID;
            _streamID = unchecked((UInt32)Interlocked.Increment(
                ref _nextStreamID));
            _containerEffects = new SortedDictionary<byte, UInt64>();
            _modalActiveSpecs = new UInt64[0];
            _sharedMetaStats = new SortedDictionary<UInt64,
                SortedDictionary<UInt64, float>>();
            _computedStats = CopyStats(recomputedStats);
            _fixedModifiers = CopyModifierMaps(fixedModifiers);
            _percentModifiers = CopyModifierMaps(percentModifiers);
            _affectedModifierStats = affectedModifierStats == null ?
                new UInt64[0] : affectedModifierStats.Distinct()
                    .OrderBy(value => value).ToArray();
            _fightingState = fightingState;
            _isStatRefresh = true;
        }

        public static AreaAbilityEffectReplication CreateStatRefresh(
            UInt64 characterID, bool fightingState,
            IDictionary<UInt64, float> recomputedStats,
            IDictionary<UInt64, IDictionary<UInt64, float>> fixedModifiers,
            IDictionary<UInt64, IDictionary<UInt64, float>> percentModifiers,
            IEnumerable<UInt64> affectedModifierStats)
        {
            return new AreaAbilityEffectReplication(characterID,
                fightingState, recomputedStats, fixedModifiers,
                percentModifiers, affectedModifierStats);
        }

        public UInt64 NodeID { get { return _nodeID; } }
        public UInt32 StreamID { get { return _streamID; } }

        internal static byte[] BuildPayload(UInt32 streamID, UInt64 nodeID,
            UInt64 oldNodeID, UInt64 effectSpecID, UInt64 characterID,
            UInt64 startTime, UInt64 endTime,
            IDictionary<byte, UInt64> containerEffects,
            IEnumerable<UInt64> modalActiveSpecs,
            SortedDictionary<UInt64,
                SortedDictionary<UInt64, float>> sharedMetaStats,
            IDictionary<UInt64, float> computedStats,
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>>
                fixedModifiers,
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>>
                percentModifiers)
        {
            var output = new List<byte>(128);
            UInt64[] modalSpecs = modalActiveSpecs == null ? null :
                modalActiveSpecs.Distinct().OrderBy(value => value).ToArray();
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>> stats =
                sharedMetaStats ?? new SortedDictionary<UInt64,
                    SortedDictionary<UInt64, float>>();
            SortedDictionary<UInt64, float> computed = CopyStats(computedStats);
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>> fixedMap =
                CopyModifierMaps(fixedModifiers);
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>> percent =
                CopyModifierMaps(percentModifiers);
            WriteUInt32Little(output, streamID);
            WriteUInt32Little(output, 0); // no schema definitions
            output.Add(oldNodeID == 0 ? (byte)0x01 : (byte)0x03);
            output.Add((byte)(2 + (modalSpecs == null ? 0 : 1) +
                (stats.Count == 0 ? 0 : 1) +
                (computed.Count == 0 && fixedMap.Count == 0 &&
                    percent.Count == 0 ? 0 : 1)));

            // The effect action reads its computed parameters from field 100
            // (modMetaStatComputed_Shared). Populate that per-spec cache before
            // the effect object is created so PostContainerAdd can execute the
            // action with the same values as the original server.
            if (stats.Count != 0)
                WriteSharedMetaStatsUpdate(output, characterID, stats);
            if (computed.Count != 0 || fixedMap.Count != 0 ||
                percent.Count != 0)
                WriteActiveStatMutation(output, characterID, computed,
                    fixedMap, percent, fixedMap.Keys.Concat(percent.Keys),
                    true, null);
            WriteContainerUpdate(output, containerEffects);
            WriteEffectCreate(output, nodeID, effectSpecID, characterID,
                startTime, endTime);
            if (modalSpecs != null)
                WriteModalActiveSpecsUpdate(output, characterID, modalSpecs);

            if (oldNodeID != 0)
            {
                output.Add(0x01);
                WritePackedUnsigned(output, oldNodeID);
            }
            return output.ToArray();
        }

        private static SortedDictionary<UInt64,
            SortedDictionary<UInt64, float>> CopySharedMetaStats(
            IDictionary<UInt64, IDictionary<UInt64, float>> source)
        {
            var result = new SortedDictionary<UInt64,
                SortedDictionary<UInt64, float>>();
            if (source == null)
                return result;
            foreach (KeyValuePair<UInt64, IDictionary<UInt64, float>> entry
                in source)
            {
                if (entry.Value == null || entry.Value.Count == 0)
                    continue;
                result[entry.Key] = new SortedDictionary<UInt64, float>(
                    entry.Value);
            }
            return result;
        }

        private static SortedDictionary<UInt64, float> CopyStats(
            IDictionary<UInt64, float> source)
        {
            return source == null ? new SortedDictionary<UInt64, float>() :
                new SortedDictionary<UInt64, float>(source);
        }

        private static SortedDictionary<UInt64,
            SortedDictionary<UInt64, float>> CreateSingleSourceModifiers(
            IDictionary<UInt64, float> source, UInt64 sourceNodeID)
        {
            var result = new SortedDictionary<UInt64,
                SortedDictionary<UInt64, float>>();
            if (source == null)
                return result;
            foreach (KeyValuePair<UInt64, float> entry in source)
                result[entry.Key] = new SortedDictionary<UInt64, float> {
                    { sourceNodeID, entry.Value }
                };
            return result;
        }

        private static SortedDictionary<UInt64,
            SortedDictionary<UInt64, float>> CopyModifierMaps(
            IDictionary<UInt64, IDictionary<UInt64, float>> source)
        {
            var result = new SortedDictionary<UInt64,
                SortedDictionary<UInt64, float>>();
            if (source == null)
                return result;
            foreach (KeyValuePair<UInt64, IDictionary<UInt64, float>> entry
                in source)
                result[entry.Key] = entry.Value == null ?
                    new SortedDictionary<UInt64, float>() :
                    new SortedDictionary<UInt64, float>(entry.Value);
            return result;
        }

        private static SortedDictionary<UInt64,
            SortedDictionary<UInt64, float>> CopyModifierMaps(
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>> source)
        {
            var result = new SortedDictionary<UInt64,
                SortedDictionary<UInt64, float>>();
            if (source == null)
                return result;
            foreach (KeyValuePair<UInt64, SortedDictionary<UInt64, float>>
                entry in source)
                result[entry.Key] = entry.Value == null ?
                    new SortedDictionary<UInt64, float>() :
                    new SortedDictionary<UInt64, float>(entry.Value);
            return result;
        }

        /// <summary>
        /// Replicates the server-calculated output of an active stat action.
        /// The April client does not recompute modStatComputed from modifier
        /// maps: Replication_Update only raises OnModifiersChanged for fields
        /// 136/137 and raises OnComputedStatChanged separately for field 52.
        /// Both layers must therefore travel together.
        /// </summary>
        private static void WriteActiveStatMutation(List<byte> output,
            UInt64 characterID,
            SortedDictionary<UInt64, float> computedStats,
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>>
                fixedModifiers,
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>>
                percentModifiers,
            IEnumerable<UInt64> affectedModifierStats,
            bool sparseInnerMaps, bool? fightingState)
        {
            UInt64[] affected = affectedModifierStats == null ?
                new UInt64[0] : affectedModifierStats.Distinct()
                    .OrderBy(value => value).ToArray();
            var body = new List<byte>();

            if (fightingState.HasValue)
                body.Add(fightingState.Value ? (byte)1 : (byte)0);

            if (computedStats.Count != 0)
            {
                WritePackedUnsigned(body,
                    (UInt64)(computedStats.Count * 2 + 1));
                foreach (KeyValuePair<UInt64, float> entry in computedStats)
                {
                    WritePackedUnsigned(body, entry.Key);
                    body.AddRange(BitConverter.GetBytes(entry.Value));
                }
            }

            bool hasFixedField = fixedModifiers.Count != 0;
            bool hasPercentField = percentModifiers.Count != 0;
            if (hasFixedField)
                WriteModifierMap(body, fixedModifiers, sparseInnerMaps);
            if (hasPercentField)
                WriteModifierMap(body, percentModifiers, sparseInnerMaps);

            const int stateSize = 54;
            int innerSize = body.Count;
            int outerSize = 1 + PackedSize((UInt64)innerSize) + innerSize +
                stateSize;
            if (innerSize >= 0xC0 || outerSize >= 0xC0)
                throw new InvalidOperationException(
                    "Active stat mutation exceeded one-byte framing.");

            WritePackedUnsigned(output, characterID);
            output.Add(0x09);
            output.Add(0x05);
            output.Add(0x08);
            output.Add((byte)outerSize);
            output.Add(0x1A);
            output.Add((byte)innerSize);
            output.AddRange(body);

            byte[] states = new byte[stateSize];
            if (fightingState.HasValue)
                states[1] |= 0x04; // field 6, staFighting
            if (computedStats.Count != 0)
                states[13] = 0x40; // field 52, modStatComputed
            if (hasFixedField)
                states[34] |= 0x40; // field 136, modStat_Fixed
            if (hasPercentField)
                states[34] |= 0x10; // field 137, modStat_PercentOfCurrent
            output.AddRange(states);
        }

        private static void WriteModifierMap(List<byte> body,
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>> values,
            bool sparseInnerMaps)
        {
            UInt64[] statKeys = values.Keys.OrderBy(value => value).ToArray();
            WritePackedUnsigned(body, (UInt64)(statKeys.Length * 2 + 1));
            foreach (UInt64 stat in statKeys)
            {
                WritePackedUnsigned(body, stat);
                SortedDictionary<UInt64, float> sources;
                if (!values.TryGetValue(stat, out sources))
                    sources = new SortedDictionary<UInt64, float>();
                WritePackedUnsigned(body, (UInt64)(sources.Count * 2 +
                    (sparseInnerMaps && sources.Count != 0 ? 1 : 0)));
                foreach (KeyValuePair<UInt64, float> source in sources)
                {
                    WritePackedUnsigned(body, source.Key);
                    body.AddRange(BitConverter.GetBytes(source.Value));
                }
            }
        }

        /// <summary>
        /// Sparse-merges computed effect/ability stats into structure-26 field
        /// 100, modMetaStatComputed_Shared. Its schema is
        /// Map&lt;Integer, Map&lt;modStatEnum, Float&gt;&gt;; both style-8 maps use the
        /// native odd count form (entryCount * 2 + 1). Captured CRT16/17 values
        /// establish that the outer keys are effect/ability spec IDs and the
        /// inner keys are the real April-2012 modStatEnum ordinals.
        /// </summary>
        private static void WriteSharedMetaStatsUpdate(List<byte> output,
            UInt64 characterID,
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>> stats)
        {
            var body = new List<byte>();
            WritePackedUnsigned(body, (UInt64)(stats.Count * 2 + 1));
            foreach (KeyValuePair<UInt64, SortedDictionary<UInt64, float>> spec
                in stats)
            {
                WritePackedUnsigned(body, spec.Key);
                WritePackedUnsigned(body,
                    (UInt64)(spec.Value.Count * 2 + 1));
                foreach (KeyValuePair<UInt64, float> value in spec.Value)
                {
                    WritePackedUnsigned(body, value.Key);
                    body.AddRange(BitConverter.GetBytes(value.Value));
                }
            }

            const int stateSize = 54;
            int innerSize = body.Count;
            int outerSize = 1 + PackedSize((UInt64)innerSize) + innerSize +
                stateSize;
            if (innerSize >= 0xC0 || outerSize >= 0xC0)
                throw new InvalidOperationException(
                    "Shared meta-stat update exceeded one-byte framing.");

            WritePackedUnsigned(output, characterID);
            output.Add(0x09); // update + value
            output.Add(0x05);
            output.Add(0x08); // style 8 structured update
            output.Add((byte)outerSize);
            output.Add(0x1A); // structure 26, chrPlayerCharacter
            output.Add((byte)innerSize);
            output.AddRange(body);

            byte[] states = new byte[stateSize];
            // Field 100 starts at bit 200. The style-8 state-1 code is 01,
            // which occupies the high pair of byte 25.
            states[25] = 0x40;
            output.AddRange(states);
        }

        internal static byte[] BuildRemovalPayload(UInt32 streamID,
            UInt64 removedNodeID, UInt64 characterID,
            IDictionary<byte, UInt64> retainedEffects,
            IEnumerable<UInt64> modalActiveSpecs,
            IDictionary<UInt64, float> recomputedStats,
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>>
                fixedModifiers,
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>>
                percentModifiers,
            IEnumerable<UInt64> affectedModifierStats)
        {
            if (removedNodeID == 0)
                throw new ArgumentOutOfRangeException("removedNodeID");
            var output = new List<byte>(96);
            UInt64[] modalSpecs = modalActiveSpecs == null ? new UInt64[0] :
                modalActiveSpecs.Distinct().OrderBy(value => value).ToArray();
            SortedDictionary<UInt64, float> recomputed =
                CopyStats(recomputedStats);
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>> fixedMap =
                CopyModifierMaps(fixedModifiers);
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>> percentMap =
                CopyModifierMaps(percentModifiers);
            UInt64[] affected = affectedModifierStats == null ?
                new UInt64[0] : affectedModifierStats.Distinct()
                    .OrderBy(value => value).ToArray();
            WriteUInt32Little(output, streamID);
            WriteUInt32Little(output, 0); // no schema definitions
            output.Add(0x03); // records and removals both present
            output.Add((byte)(2 +
                (recomputed.Count == 0 && affected.Length == 0 ? 0 : 1)));
            if (recomputed.Count != 0 || affected.Length != 0)
                WriteActiveStatMutation(output, characterID, recomputed,
                    fixedMap, percentMap, affected, false, null);
            // The odd style-8 sequence form used by activation is a sparse
            // merge. Omitting an old entry therefore cannot remove it. Use the
            // serializer's even-count full-value form here so the retained
            // snapshots actually replace both collections.
            WriteContainerReplacement(output, retainedEffects);
            WriteModalActiveSpecsReplacement(output, characterID, modalSpecs);
            output.Add(0x01);
            WritePackedUnsigned(output, removedNodeID);
            return output.ToArray();
        }

        internal static byte[] BuildStatRefreshPayload(UInt32 streamID,
            UInt64 characterID, bool fightingState,
            IDictionary<UInt64, float> recomputedStats,
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>>
                fixedModifiers,
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>>
                percentModifiers,
            IEnumerable<UInt64> affectedModifierStats)
        {
            var output = new List<byte>(160);
            SortedDictionary<UInt64, float> recomputed =
                CopyStats(recomputedStats);
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>> fixedMap =
                CopyModifierMaps(fixedModifiers);
            SortedDictionary<UInt64, SortedDictionary<UInt64, float>> percentMap =
                CopyModifierMaps(percentModifiers);
            UInt64[] affected = affectedModifierStats == null ?
                new UInt64[0] : affectedModifierStats.Distinct()
                    .OrderBy(value => value).ToArray();
            WriteUInt32Little(output, streamID);
            WriteUInt32Little(output, 0);
            output.Add(0x01);
            output.Add(0x01);
            WriteActiveStatMutation(output, characterID, recomputed,
                fixedMap, percentMap, affected, false, fightingState);
            return output.ToArray();
        }

        private static void WriteContainerReplacement(List<byte> output,
            IDictionary<byte, UInt64> effectNodes)
        {
            WriteContainerValue(output, effectNodes, false);
        }

        private static void WriteContainerUpdate(List<byte> output,
            IDictionary<byte, UInt64> effectNodes)
        {
            WriteContainerValue(output, effectNodes, true);
        }

        private static void WriteContainerValue(List<byte> output,
            IDictionary<byte, UInt64> effectNodes, bool sparseUpdate)
        {
            var entries = new SortedDictionary<byte, UInt64>();
            entries[1] = CapturedSlotOneNode;
            if (effectNodes != null)
                foreach (KeyValuePair<byte, UInt64> entry in effectNodes)
                {
                    if (entry.Key <= 1)
                        throw new ArgumentOutOfRangeException("effectNodes");
                    entries[entry.Key] = entry.Value;
                }

            int innerSize = 1;
            foreach (KeyValuePair<byte, UInt64> entry in entries)
                innerSize += 1 + PackedSize(entry.Value);
            int outerSize = 1 + PackedSize((UInt64)innerSize) + innerSize + 1;
            if (entries.Count > 95 || innerSize >= 0xC0 || outerSize >= 0xC0)
                throw new InvalidOperationException(
                    "Experimental effect container exceeded one-byte framing.");

            WritePackedUnsigned(output, PositiveContainerNode);
            output.Add(0x09); // update + value
            output.Add(0x05); // field version
            output.Add(0x08); // style 8 structured update
            output.Add((byte)outerSize);
            output.Add(0x0D); // structure 13, effContainer
            output.Add((byte)innerSize);
            // SerializeLookupList writes the even entryCount*2 form for a full
            // value. Native replication uses the odd form for sparse updates;
            // that is why omission from our old removal packet retained the
            // client's old slot.
            output.Add((byte)(entries.Count * 2 +
                (sparseUpdate ? 1 : 0)));
            foreach (KeyValuePair<byte, UInt64> entry in entries)
            {
                output.Add(entry.Key);
                WritePackedUnsigned(output, entry.Value);
            }
            output.Add(0x78); // only conContents is present
        }

        private static void WriteModalActiveSpecsUpdate(List<byte> output,
            UInt64 characterID, UInt64[] modalActiveSpecs)
        {
            WriteModalActiveSpecsValue(output, characterID, modalActiveSpecs,
                true);
        }

        private static void WriteModalActiveSpecsReplacement(
            List<byte> output, UInt64 characterID,
            UInt64[] modalActiveSpecs)
        {
            WriteModalActiveSpecsValue(output, characterID, modalActiveSpecs,
                false);
        }

        private static void WriteModalActiveSpecsValue(List<byte> output,
            UInt64 characterID, UInt64[] modalActiveSpecs,
            bool sparseUpdate)
        {
            int innerSize = 1;
            for (int index = 0; index < modalActiveSpecs.Length; ++index)
                innerSize += PackedSize(sparseUpdate ?
                    (UInt64)(((index + 1) << 1) | 1) : (UInt64)index) +
                    PackedSize(modalActiveSpecs[index]);
            const int stateSize = 54; // 215 structure-26 fields, two bits each
            int outerSize = 1 + PackedSize((UInt64)innerSize) + innerSize +
                stateSize;
            if (modalActiveSpecs.Length > 95 || innerSize >= 0xC0 ||
                outerSize >= 0xC0)
                throw new InvalidOperationException(
                    "Modal ability list exceeded one-byte framing.");

            WritePackedUnsigned(output, characterID);
            output.Add(0x09); // update + value
            output.Add(0x05);
            output.Add(0x08);
            output.Add((byte)outerSize);
            output.Add(0x1A); // structure 26, chrPlayerCharacter
            output.Add((byte)innerSize);
            // Sparse native updates use the captured odd form with one-based
            // odd indexes (05 03 <v> 05 <v>). SerializeList's full-value form
            // is even and writes explicit zero-based indexes because style 8
            // has Flags[2]. The latter is required to clear omitted entries.
            output.Add((byte)(modalActiveSpecs.Length * 2 +
                (sparseUpdate ? 1 : 0)));
            for (int index = 0; index < modalActiveSpecs.Length; ++index)
            {
                WritePackedUnsigned(output, sparseUpdate ?
                    (UInt64)(((index + 1) << 1) | 1) : (UInt64)index);
                WritePackedUnsigned(output, modalActiveSpecs[index]);
            }

            byte[] states = new byte[stateSize];
            // Structure-26 field 175 is ablUserModalActiveSpecs. Its two-bit
            // state-1 code starts at bit 350, the final two bits of byte 43.
            states[43] = 0x01;
            output.AddRange(states);
        }

        private static void WriteEffectCreate(List<byte> output, UInt64 nodeID,
            UInt64 effectSpecID, UInt64 characterID, UInt64 startTime,
            UInt64 endTime)
        {
            bool isTimed = startTime != 0 || endTime != 0;
            if (isTimed && (startTime == 0 || endTime <= startTime))
                throw new ArgumentOutOfRangeException("endTime");

            WritePackedUnsigned(output, nodeID);
            output.Add(0x7A); // create: template + parent + metadata + value
            WritePackedUnsigned(output, effectSpecID);
            WritePackedUnsigned(output, PositiveContainerNode);

            // Captured metadata: one additional-class component,
            // effStackLimitComponent.
            output.Add(0x01);
            WriteUInt32Little(output, 1);
            WriteUInt64Little(output, StackLimitComponent);

            output.Add(0x05); // field version
            output.Add(0x08); // style 8 structured value
            output.Add(isTimed ? (byte)0x26 : (byte)0x18);
            output.Add(0x28); // structure 40, effEffect
            output.Add(isTimed ? (byte)0x21 : (byte)0x13);
            output.Add(0x18); // effSlotType from captured positive effects
            WritePackedUnsigned(output, characterID); // effTargetDefaultId
            if (isTimed)
            {
                WritePackedUnsigned(output, endTime); // effEndTime
                WritePackedUnsigned(output, startTime); // effStartTime
            }
            WritePackedUnsigned(output, characterID); // effCasterId
            output.Add(isTimed ? (byte)0x59 : (byte)0x5A);
            output.Add(isTimed ? (byte)0x6A : (byte)0xAA);
            output.Add(0x40); // fields 0, 1 and 8 present
        }

        private static void WritePackedUnsigned(List<byte> output, UInt64 value)
        {
            if (value < 0xC0)
            {
                output.Add((byte)value);
                return;
            }

            int length = 0;
            UInt64 remaining = value;
            do
            {
                ++length;
                remaining >>= 8;
            }
            while (remaining != 0);
            if (length > 8)
                throw new ArgumentOutOfRangeException("value");

            output.Add((byte)(0xC7 + length));
            for (int shift = (length - 1) * 8; shift >= 0; shift -= 8)
                output.Add((byte)(value >> shift));
        }

        private static int PackedSize(UInt64 value)
        {
            if (value < 0xC0)
                return 1;
            int magnitude = 0;
            do
            {
                ++magnitude;
                value >>= 8;
            }
            while (value != 0);
            return 1 + magnitude;
        }

        private static void WriteUInt32Little(List<byte> output, UInt32 value)
        {
            output.AddRange(BitConverter.GetBytes(value));
        }

        private static void WriteUInt64Little(List<byte> output, UInt64 value)
        {
            output.AddRange(BitConverter.GetBytes(value));
        }

        public override void WriteImplementation()
        {
            WriteUInt32((UInt32)GetType());
            WriteAreaComponent();
            if (_isStatRefresh)
            {
                WriteBytes(BuildStatRefreshPayload(_streamID, _characterID,
                    _fightingState.Value, _computedStats, _fixedModifiers,
                    _percentModifiers, _affectedModifierStats));
                Log.Write(LogLevel.Client,
                    "AreaAbilityEffectReplication: stream=0x{0:X8} target=0x{1:X16} fighting={2} statRefresh=1 recomputedStats={3} fixedStats={4} percentStats={5}",
                    _streamID, _characterID, _fightingState.Value,
                    _computedStats.Count, _fixedModifiers.Count,
                    _percentModifiers.Count);
            }
            else if (_isRemoval)
            {
                WriteBytes(BuildRemovalPayload(_streamID, _oldNodeID,
                    _characterID, _containerEffects, _modalActiveSpecs,
                    _computedStats, _fixedModifiers, _percentModifiers,
                    _affectedModifierStats));
                Log.Write(LogLevel.Client,
                    "AreaAbilityEffectReplication: stream=0x{0:X8} container=0x{1:X16} nodes={2} removed=0x{3:X16} target=0x{4:X16} modalSpecs={5} recomputedStats={6} affectedModifierStats={7}",
                    _streamID, PositiveContainerNode,
                    _containerEffects.Count, _oldNodeID, _characterID,
                    _modalActiveSpecs.Length, _computedStats.Count,
                    _affectedModifierStats.Length);
            }
            else
            {
                WriteBytes(BuildPayload(_streamID, _nodeID, _oldNodeID,
                    _effectSpecID, _characterID, _startTime, _endTime,
                    _containerEffects, _modalActiveSpecs, _sharedMetaStats,
                    _computedStats, _fixedModifiers, _percentModifiers));
                Log.Write(LogLevel.Client,
                    "AreaAbilityEffectReplication: stream=0x{0:X8} container=0x{1:X16} nodes={2} node=0x{3:X16} old=0x{4:X16} effect=0x{5:X16} target=0x{6:X16} modalSpecs={7} start={8} end={9} metaSpecs={10} computedStats={11} fixedStats={12} percentStats={13}",
                    _streamID, PositiveContainerNode,
                    _containerEffects.Count, _nodeID, _oldNodeID,
                    _effectSpecID, _characterID,
                    _modalActiveSpecs == null ? "unchanged" :
                        _modalActiveSpecs.Length.ToString(), _startTime,
                    _endTime, _sharedMetaStats.Count, _computedStats.Count,
                    _fixedModifiers.Count, _percentModifiers.Count);
            }
        }

        public override PacketType GetType()
        {
            return PacketType.AreaClientReplicationTransaction;
        }

        public override void SetModule(byte inMod) { _module = inMod; }
        public override byte GetModule() { return _module; }
    }
}
