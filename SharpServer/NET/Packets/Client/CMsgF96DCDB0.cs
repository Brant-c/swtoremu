using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    class CMsgF96DCDB0 : TORGameClientPacket
    {
        private static readonly object EffectReplicationLock = new object();
        private const UInt64 SprintAbilitySpecId = 0xE00081CEF00BAF68UL;
        private sealed class CombatExperimentState
        {
            public bool InCombat;
            public Timer ExitTimer;
        }
        private sealed class ReplicatedEffectState
        {
            public byte Slot;
            public UInt64 NodeID;
            public bool IsModal;
            public UInt64 CharacterID;
            public Dictionary<UInt64, float> BaseStats;
            public Dictionary<UInt64, float> FixedModifiers;
            public Dictionary<UInt64, float> PercentModifiers;
            public Timer ExpirationTimer;
            public bool Suppressed;
        }

        private static readonly Dictionary<TORGameClient,
            Dictionary<UInt64, ReplicatedEffectState>> ActiveReplicatedEffects =
            new Dictionary<TORGameClient,
                Dictionary<UInt64, ReplicatedEffectState>>();
        private static readonly Dictionary<TORGameClient,
            CombatExperimentState> CombatExperimentStates =
            new Dictionary<TORGameClient, CombatExperimentState>();

        private UInt32 _component;
        private byte[] _body;

        public override void ReadImplementation()
        {
            ReadUInt32();
            _component = ReadUInt32();
            int remaining = (int)(_stream.Length - _stream.Position);
            _body = remaining > 0 ? ReadBytes(remaining) : new byte[0];
        }

        public override void RunImplementation()
        {
            TORGameClient client = GetClient();
            string sub = (_body != null && _body.Length > 0) ? _body[0].ToString("X2") : "??";
            bool tail = _body != null && _body.Length >= 4 && _body[_body.Length-4]==0x74 && _body[_body.Length-3]==0x72 && _body[_body.Length-2]==0x75 && _body[_body.Length-1]==0x65;
            AreaPollExperiment.LogPoll(client, "CMsgF96DCDB0", _component, _body, "sub=" + sub + " trueTail=" + tail);
            if (client == null)
            {
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "no-client");
                return;
            }
            if (client.AreaServiceID == 0)
            {
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "no-area-service");
                return;
            }

            if (NexusToRServer.AreaServer.TythonTaxi.Handle(client, _component, _body))
                return;
            if (NexusToRServer.AreaServer.WellerConversation.Handle(client, _component, _body))
                return;

            var mode = RpcReply.GetMode();

            // Ability activations share this opcode with the periodic area
            // keepalive, so they get their own reply mode. Without this
            // split, changing the ability behaviour also changes the keepalive
            // and every bisect is ambiguous.
            //
            // The April SCPT function-address table and the native inbound
            // dispatcher identify the completion endpoint without relying on
            // the Beta RPC id: script hash 0x54058C0E, public function SID
            // 0xE7DC09C4. The earlier 0xD1DD59C2 candidate came from an
            // auxiliary symbol table and the client rejected it as a script
            // entry point. Style-5 RPC
            // streams prefix every argument with its Hero type, so the reply is
            // selector + (ID abilitySpec) + (Integer requestId) +
            // (Enum effResultOk). Keep it opt-in as "complete" until exercised.
            bool isAbilityActivation = _body != null && _body.Length >= 13 &&
                _body[4] == 0xC7 &&
                BitConverter.ToUInt32(_body, 5) == 0x1279C371 &&
                BitConverter.ToUInt32(_body, 9) == 0x001703D5;
            if (isAbilityActivation)
            {
                string abilityMode = Environment.GetEnvironmentVariable("SWTOR_ABILITY_REPLY_MODE");
                if (string.IsNullOrWhiteSpace(abilityMode))
                    abilityMode = mode.ToString();
                if (Enum.TryParse(abilityMode, true, out RpcReply.Mode abilityParsed))
                {
                    switch (abilityParsed)
                    {
                        case RpcReply.Mode.Swallow:
                            AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "ability:swallowed");
                            break;
                        case RpcReply.Mode.Mirror:
                        case RpcReply.Mode.Results:
                            RpcReply.SendResults(client, 0x65B3, client.AreaServiceID, "CMsgF96DCDB0", _body);
                            AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "ability:sms-results-sent");
                            break;
                        case RpcReply.Mode.Echo:
                            client.SendPacket(new AreaRPCPollAck(client.AreaServiceID, _body));
                            AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "ability:echo-reply-sent");
                            break;
                        case RpcReply.Mode.Ack:
                            client.SendPacket(new AreaRPCPollAck(client.AreaServiceID, new byte[0]));
                            AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "ability:empty-ack-sent");
                            break;
                        case RpcReply.Mode.Complete:
                            UInt64 targetId;
                            UInt64 abilitySpecId;
                            Int64 requestId;
                            string parseFailure;
                            if (!TryParseAbilityActivation(_body, out targetId,
                                out abilitySpecId, out requestId, out parseFailure))
                            {
                                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                                    "ability:completion-not-sent:" + parseFailure);
                                break;
                            }
                            byte[] resultBlob = BuildQueuedAbilityResult(abilitySpecId,
                                requestId);
                            client.SendPacket(new AreaRequestRPC(resultBlob));
                            AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                                string.Format(
                                    "ability:queued-result-sent selector=54058C0E:E7DC09C4 target=0x{0:X16} ability=0x{1:X16} request={2} effResultOk=1 bytes={3}",
                                    targetId, abilitySpecId, requestId,
                                    BitConverter.ToString(resultBlob).Replace('-', ' ')));
                            TrySendAbilityEffectExperiment(client, targetId,
                                abilitySpecId, requestId);
                            NoteHostileAbility(client, targetId);
                            break;
                    }
                }
                else
                {
                    AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "ability:bad-mode:" + abilityMode);
                }
                return;
            }

            // Once ablUserModalActiveSpecs is authoritative, a second press of
            // Sprint or a combat form no longer repeats RequestAbilityActivate.
            // It calls RequestAbilityDeactivate with only the ability spec.
            bool isAbilityDeactivation = _body != null && _body.Length >= 13 &&
                _body[4] == 0xC7 &&
                BitConverter.ToUInt32(_body, 5) == 0x1279C371 &&
                BitConverter.ToUInt32(_body, 9) == 0x9D1796F2;
            if (isAbilityDeactivation)
            {
                UInt64 abilitySpecId;
                string parseFailure;
                if (!TryParseAbilityDeactivation(_body, out abilitySpecId,
                    out parseFailure))
                {
                    AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                        "ability:deactivation-not-applied:" + parseFailure);
                    return;
                }
                TryRemoveReplicatedAbilityEffect(client, abilitySpecId);
                return;
            }

            // Positive buff icons invoke untrustedMethods:OnRequestEffectRemove
            // with (owner ID, runtime effect-node ID). The exact function SID
            // is build-specific, so recognize the typed request by matching
            // both IDs against an effect this server created. This cannot
            // consume an unrelated two-ID RPC unless it names that live node.
            UInt64 removalOwnerId;
            UInt64 removalNodeId;
            UInt32 removalFunctionSid;
            if (TryParseEffectRemovalRequest(_body, out removalOwnerId,
                out removalNodeId, out removalFunctionSid))
            {
                UInt64 removalAbilitySpecId = 0;
                lock (EffectReplicationLock)
                {
                    Dictionary<UInt64, ReplicatedEffectState> effects;
                    if (ActiveReplicatedEffects.TryGetValue(client, out effects))
                    {
                        KeyValuePair<UInt64, ReplicatedEffectState> match =
                            effects.FirstOrDefault(entry =>
                                entry.Value.CharacterID == removalOwnerId &&
                                entry.Value.NodeID == removalNodeId);
                        removalAbilitySpecId = match.Key;
                    }
                }
                if (removalAbilitySpecId != 0)
                {
                    AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                        String.Format(
                            "ability:right-click-remove selector=1279C371:{0:X8} owner=0x{1:X16} node=0x{2:X16} ability=0x{3:X16}",
                            removalFunctionSid, removalOwnerId, removalNodeId,
                            removalAbilitySpecId));
                    TryRemoveReplicatedAbilityEffect(client,
                        removalAbilitySpecId);
                    return;
                }
            }

            // The client's own script RPC request. Body = [Int32 len][name bytes]
            // (+ args); the reference server reads it as count+bytes. Answer with
            // SMSG_RESULTS (0xD5280283) so the pending script call can complete.
            if (mode == RpcReply.Mode.Mirror || mode == RpcReply.Mode.Results)
            {
                RpcReply.SendResults(client, 0x65B3, client.AreaServiceID, "CMsgF96DCDB0", _body);
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "sms-results-sent");
            }
            else if (mode == RpcReply.Mode.Echo)
            {
                client.SendPacket(new AreaRPCPollAck(client.AreaServiceID, _body));
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "echo-reply-sent");
            }
            else if (mode == RpcReply.Mode.Ack)
            {
                client.SendPacket(new AreaRPCPollAck(client.AreaServiceID, new byte[0]));
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "empty-ack-sent");
            }
            else
            {
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0", "swallowed");
            }
        }

        private static void TrySendAbilityEffectExperiment(TORGameClient client,
            UInt64 targetId, UInt64 abilitySpecId, Int64 requestId)
        {
            if (Environment.GetEnvironmentVariable("SWTOR_ABILITY_EFFECT_EXPERIMENT") != "1")
                return;
            if (requestId < 1 || requestId > UInt16.MaxValue)
            {
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                    "ability:effect-not-sent:request-out-of-uint16-range");
                return;
            }

            UInt64 rootEffectSpecId;
            UInt64 persistentEffectSpecId;
            Int64 persistentDurationMilliseconds;
            byte persistentSlot;
            bool isModal;
            IDictionary<UInt64, IDictionary<UInt64, float>> sharedMetaStats =
                null;
            IDictionary<UInt64, float> computedStats = null;
            IDictionary<UInt64, float> baseStats = null;
            IDictionary<UInt64, float> fixedModifiers = null;
            IDictionary<UInt64, float> percentOfCurrent = null;
            switch (abilitySpecId)
            {
                case 0xE00079A6400301F5UL: // abl.jedi_knight.shiicho_form
                    rootEffectSpecId = 0xE000C3452BFEEA1CUL; // /3/0, driver
                    persistentEffectSpecId = 0xE000C2452BFEE9AFUL; // /3/1, stance
                    persistentDurationMilliseconds = 0;
                    persistentSlot = 4;
                    isModal = true;
                    // Base-rank Shii-Cho applies fixed +3 percentage points to
                    // all four mitigation types and damage done. Higher ranks
                    // are conditional on talent abilities not present in this
                    // character fixture.
                    baseStats = new Dictionary<UInt64, float> {
                        { 0x15UL, 0.0f }, // elemental reduction
                        { 0x16UL, 0.0f }, // internal reduction
                        { 0x17UL, 0.0f }, // kinetic reduction
                        { 0x18UL, 0.0f }, // energy reduction
                        { 0x4FUL, 0.0f }  // damage done percentage
                    };
                    fixedModifiers = new Dictionary<UInt64, float> {
                        { 0x15UL, 0.03f },
                        { 0x16UL, 0.03f },
                        { 0x17UL, 0.03f },
                        { 0x18UL, 0.03f },
                        { 0x4FUL, 0.03f }
                    };
                    break;
                case SprintAbilitySpecId: // abl.player.sprint
                    rootEffectSpecId = 0xE00015A245BFAC89UL; // /3/0, driver
                    persistentEffectSpecId = 0xE00018A245BFA7A0UL; // /3/3, persistent speed
                    persistentDurationMilliseconds = 0;
                    persistentSlot = 3;
                    isModal = true;
                    // abl.player.sprint/3/3:
                    // effAction_ModifyMovementSpeed with
                    // effParam_AmountPercent=135. The April client enum ordinal
                    // for STAT_aiMoveSpeedModifier is 0x24.
                    sharedMetaStats = new Dictionary<UInt64,
                        IDictionary<UInt64, float>> {
                        { persistentEffectSpecId,
                            new Dictionary<UInt64, float> {
                                { 0x24UL, 135.0f }
                            }
                        }
                    };
                    // CRT2 establishes the character's unmodified locomotion
                    // values. ModifyMovementSpeed(135) contributes +35% of
                    // current to run, walk, and backwards-run speed.
                    baseStats = new Dictionary<UInt64, float> {
                        { 0x27UL, 0.60f },
                        { 0x28UL, 0.15f },
                        { 0x3AUL, 0.36f }
                    };
                    percentOfCurrent = new Dictionary<UInt64, float> {
                        { 0x27UL, 0.35f },
                        { 0x28UL, 0.35f },
                        { 0x3AUL, 0.35f }
                    };
                    break;
                case 0xE0009B0DF29A7BA2UL: // abl.jedi_knight.introspection
                    rootEffectSpecId = 0xE0008CAE3E2BB386UL; // /1/0, effect slot zero
                    persistentEffectSpecId = 0;
                    persistentDurationMilliseconds = 0;
                    persistentSlot = 0;
                    isModal = false;
                    break;
                case 0xE000A433E5152AA7UL: // abl.jedi_knight.force_might
                    rootEffectSpecId = 0xE000A38DCFFE7CC2UL; // /3/0, effect slot zero
                    persistentEffectSpecId = 0xE000A78DCFFE7716UL; // /3/4, one-hour buff
                    persistentDurationMilliseconds = GetTimedEffectDuration(
                        60L * 60L * 1000L);
                    persistentSlot = 2;
                    isModal = false;
                    baseStats = new Dictionary<UInt64, float> {
                        { 0x19UL, 2.0f },   // ranged damage bonus
                        { 0x1AUL, 10.8f },  // melee damage bonus
                        { 0x81UL, 26.04f }, // Force damage bonus
                        { 0x82UL, 2.0f },   // Tech damage bonus
                        { 0xDAUL, 0.0f },   // Tech healing power
                        { 0xDBUL, 8.16f }   // Force healing power
                    };
                    percentOfCurrent = new Dictionary<UInt64, float> {
                        { 0x19UL, 0.05f },
                        { 0x1AUL, 0.05f },
                        { 0x81UL, 0.05f },
                        { 0x82UL, 0.05f },
                        { 0xDAUL, 0.05f },
                        { 0xDBUL, 0.05f }
                    };
                    break;
                default:
                    AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                        String.Format("ability:effect-not-sent:no-map ability=0x{0:X16}",
                            abilitySpecId));
                    return;
            }

            try
            {
                UInt64 rootTransactionId;
                UInt64 sequence = ((UInt64)(UInt16)requestId << 1);
                AreaEffEventMessage rootPacket =
                    AreaEffEventMessage.CreateAbilityActionExperiment(
                        client._area ?? String.Empty,
                        client._areaID ?? String.Empty,
                        client._areaCode ?? String.Empty,
                        targetId, rootEffectSpecId, (UInt16)requestId,
                        0, 44, 0, sequence,
                        out rootTransactionId); // effAction_AbilityActivate
                client.SendPacket(rootPacket);
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                    String.Format(
                        "ability:root-effect-sent ability=0x{0:X16} effect=0x{1:X16} request={2} transaction=0x{3:X16} action=AbilityActivate actionValueLength=19",
                        abilitySpecId, rootEffectSpecId, requestId,
                        rootTransactionId));

                if (persistentEffectSpecId != 0)
                {
                    UInt64 childTransactionId;
                    AreaEffEventMessage buffPacket =
                        AreaEffEventMessage.CreateAbilityAddEffectExperiment(
                            client._area ?? String.Empty,
                            client._areaID ?? String.Empty,
                            client._areaCode ?? String.Empty,
                            targetId, persistentEffectSpecId,
                            rootTransactionId, sequence + 1,
                            out childTransactionId); // effAction_AddEffect
                    client.SendPacket(buffPacket);
                    AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                        String.Format(
                            "ability:buff-effect-sent effect=0x{0:X16} calledBy=0x{1:X16} transaction=0x{2:X16} action=AddEffect actionValueLength=0",
                            persistentEffectSpecId, rootTransactionId,
                            childTransactionId));

                    if (Environment.GetEnvironmentVariable(
                        "SWTOR_ABILITY_EFFECT_REPLICATION") == "1")
                    {
                        UInt64 oldNodeID;
                        AreaAbilityEffectReplication replication;
                        lock (EffectReplicationLock)
                        {
                            Dictionary<UInt64, ReplicatedEffectState> effects;
                            if (!ActiveReplicatedEffects.TryGetValue(client,
                                out effects))
                            {
                                effects = new Dictionary<UInt64,
                                    ReplicatedEffectState>();
                                ActiveReplicatedEffects[client] = effects;
                            }

                            ReplicatedEffectState prior;
                            oldNodeID = effects.TryGetValue(abilitySpecId,
                                out prior) ? prior.NodeID : 0;
                            var retained = effects
                                .Where(entry => entry.Key != abilitySpecId)
                                .ToDictionary(entry => entry.Value.Slot,
                                    entry => entry.Value.NodeID);
                            var modalSpecs = effects
                                .Where(entry => entry.Key != abilitySpecId &&
                                    entry.Value.IsModal)
                                .Select(entry => entry.Key)
                                .Concat(isModal ? new UInt64[] { abilitySpecId } :
                                    new UInt64[0]);
                            bool suppressForCombat = abilitySpecId ==
                                SprintAbilitySpecId && IsInCombat(client);
                            IDictionary<UInt64, float> appliedFixed =
                                suppressForCombat ? null : fixedModifiers;
                            IDictionary<UInt64, float> appliedPercent =
                                suppressForCombat ? null : percentOfCurrent;
                            computedStats = ComputeStats(effects
                                .Where(entry => entry.Key != abilitySpecId)
                                .Select(entry => entry.Value),
                                baseStats, appliedFixed, appliedPercent);
                            replication = new AreaAbilityEffectReplication(
                                targetId, persistentEffectSpecId,
                                persistentDurationMilliseconds, oldNodeID,
                                persistentSlot, retained, modalSpecs,
                                sharedMetaStats, computedStats,
                                appliedFixed, appliedPercent);
                            var state = new ReplicatedEffectState {
                                Slot = persistentSlot,
                                NodeID = replication.NodeID,
                                IsModal = isModal,
                                CharacterID = targetId,
                                BaseStats = CopyStats(baseStats),
                                FixedModifiers = CopyStats(fixedModifiers),
                                PercentModifiers = CopyStats(percentOfCurrent),
                                Suppressed = suppressForCombat
                            };
                            effects[abilitySpecId] = state;
                            if (persistentDurationMilliseconds > 0)
                            {
                                int dueTime = checked((int)Math.Min(
                                    persistentDurationMilliseconds,
                                    Int32.MaxValue));
                                state.ExpirationTimer = new Timer(_ =>
                                    ExpireReplicatedAbilityEffect(client,
                                        abilitySpecId), null, dueTime,
                                    Timeout.Infinite);
                            }
                        }
                        client.SendPacket(replication);
                        AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                            String.Format(
                                "ability:persistent-effect-replicated stream=0x{0:X8} slot={1} node=0x{2:X16} old=0x{3:X16} effect=0x{4:X16} target=0x{5:X16} modal={6} durationMs={7}",
                                replication.StreamID, persistentSlot,
                                replication.NodeID, oldNodeID,
                                persistentEffectSpecId, targetId, isModal,
                                persistentDurationMilliseconds));
                    }
                }
            }
            catch (Exception ex)
            {
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                    "ability:effect-not-sent:" + ex.Message);
            }
        }

        private static void TryRemoveReplicatedAbilityEffect(
            TORGameClient client, UInt64 abilitySpecId)
        {
            if (Environment.GetEnvironmentVariable(
                "SWTOR_ABILITY_EFFECT_REPLICATION") != "1")
            {
                AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                    String.Format(
                        "ability:deactivation-swallowed:replication-disabled ability=0x{0:X16}",
                        abilitySpecId));
                return;
            }

            AreaAbilityEffectReplication replication;
            ReplicatedEffectState removed;
            lock (EffectReplicationLock)
            {
                Dictionary<UInt64, ReplicatedEffectState> effects;
                if (!ActiveReplicatedEffects.TryGetValue(client, out effects) ||
                    !effects.TryGetValue(abilitySpecId, out removed))
                {
                    AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                        String.Format(
                            "ability:deactivation-no-active-effect ability=0x{0:X16}",
                            abilitySpecId));
                    return;
                }

                effects.Remove(abilitySpecId);
                if (removed.ExpirationTimer != null)
                {
                    removed.ExpirationTimer.Dispose();
                    removed.ExpirationTimer = null;
                }
                var retained = effects.ToDictionary(
                    entry => entry.Value.Slot,
                    entry => entry.Value.NodeID);
                var modalSpecs = effects
                    .Where(entry => entry.Value.IsModal)
                    .Select(entry => entry.Key);
                UInt64[] affectedStats = removed.BaseStats == null ?
                    new UInt64[0] : removed.BaseStats.Keys.OrderBy(value => value)
                        .ToArray();
                Dictionary<UInt64, float> recomputedStats = ComputeStats(
                    effects.Values, removed.BaseStats, null, null);
                Dictionary<UInt64, IDictionary<UInt64, float>> fixedMaps =
                    BuildModifierMaps(effects.Values,
                        removed.FixedModifiers == null ?
                            Enumerable.Empty<UInt64>() :
                            removed.FixedModifiers.Keys.AsEnumerable(), true);
                Dictionary<UInt64, IDictionary<UInt64, float>> percentMaps =
                    BuildModifierMaps(effects.Values,
                        removed.PercentModifiers == null ?
                            Enumerable.Empty<UInt64>() :
                            removed.PercentModifiers.Keys.AsEnumerable(),
                        false);
                replication = AreaAbilityEffectReplication.CreateRemoval(
                    removed.CharacterID, removed.NodeID, retained,
                    modalSpecs, recomputedStats, fixedMaps, percentMaps,
                    affectedStats);
                if (effects.Count == 0)
                    ActiveReplicatedEffects.Remove(client);
            }

            client.SendPacket(replication);
            AreaPollExperiment.LogDecision(client, "CMsgF96DCDB0",
                String.Format(
                    "ability:deactivated-effect-removed stream=0x{0:X8} slot={1} node=0x{2:X16} ability=0x{3:X16} target=0x{4:X16}",
                    replication.StreamID, removed.Slot, removed.NodeID,
                    abilitySpecId, removed.CharacterID));
        }

        private static Int64 GetTimedEffectDuration(Int64 normalDuration)
        {
            string configured = Environment.GetEnvironmentVariable(
                "SWTOR_ABILITY_TIMED_TEST_MS");
            Int64 duration;
            return Int64.TryParse(configured, out duration) && duration >= 1000 &&
                duration <= Int32.MaxValue ? duration : normalDuration;
        }

        private static void ExpireReplicatedAbilityEffect(TORGameClient client,
            UInt64 abilitySpecId)
        {
            try
            {
                AreaPollExperiment.LogDecision(client, "AbilityTimer",
                    String.Format("ability:timed-expiry ability=0x{0:X16}",
                        abilitySpecId));
                TryRemoveReplicatedAbilityEffect(client, abilitySpecId);
            }
            catch (Exception ex)
            {
                AreaPollExperiment.LogDecision(client, "AbilityTimer",
                    "ability:timed-expiry-failed:" + ex.Message);
            }
        }

        private static Dictionary<UInt64, float> CopyStats(
            IDictionary<UInt64, float> source)
        {
            return source == null ? new Dictionary<UInt64, float>() :
                new Dictionary<UInt64, float>(source);
        }

        private static Dictionary<UInt64, float> ComputeStats(
            IEnumerable<ReplicatedEffectState> activeEffects,
            IDictionary<UInt64, float> requestedBaseStats,
            IDictionary<UInt64, float> pendingFixed,
            IDictionary<UInt64, float> pendingPercent)
        {
            var result = new Dictionary<UInt64, float>();
            if (requestedBaseStats == null)
                return result;
            foreach (KeyValuePair<UInt64, float> stat in requestedBaseStats)
            {
                float fixedTotal = GetValue(pendingFixed, stat.Key);
                float percentTotal = GetValue(pendingPercent, stat.Key);
                if (activeEffects != null)
                    foreach (ReplicatedEffectState effect in activeEffects)
                    {
                        if (effect.Suppressed)
                            continue;
                        fixedTotal += GetValue(effect.FixedModifiers, stat.Key);
                        percentTotal += GetValue(effect.PercentModifiers,
                            stat.Key);
                    }
                float current = stat.Value + fixedTotal;
                result[stat.Key] = current + current * percentTotal;
            }
            return result;
        }

        private static float GetValue(IDictionary<UInt64, float> values,
            UInt64 stat)
        {
            float value;
            return values != null && values.TryGetValue(stat, out value) ?
                value : 0.0f;
        }

        private static Dictionary<UInt64, IDictionary<UInt64, float>>
            BuildModifierMaps(IEnumerable<ReplicatedEffectState> effects,
            IEnumerable<UInt64> affectedStats, bool fixedModifiers)
        {
            var result = new Dictionary<UInt64,
                IDictionary<UInt64, float>>();
            foreach (UInt64 stat in affectedStats)
            {
                var sources = new Dictionary<UInt64, float>();
                foreach (ReplicatedEffectState effect in effects)
                {
                    if (effect.Suppressed)
                        continue;
                    IDictionary<UInt64, float> values = fixedModifiers ?
                        effect.FixedModifiers : effect.PercentModifiers;
                    float amount;
                    if (values != null && values.TryGetValue(stat, out amount))
                        sources[effect.NodeID] = amount;
                }
                result[stat] = sources;
            }
            return result;
        }

        private static bool IsInCombat(TORGameClient client)
        {
            CombatExperimentState state;
            return CombatExperimentStates.TryGetValue(client, out state) &&
                state.InCombat;
        }

        private static void NoteHostileAbility(TORGameClient client,
            UInt64 targetId)
        {
            if (Environment.GetEnvironmentVariable(
                "SWTOR_ABILITY_COMBAT_EXPERIMENT") != "1" ||
                client == null || client.ActiveCharacter == null ||
                targetId == 0 || targetId == client.ActiveCharacter._id)
                return;
            SetCombatExperimentState(client, true);
        }

        private static void SetCombatExperimentState(TORGameClient client,
            bool inCombat)
        {
            AreaAbilityEffectReplication refresh = null;
            UInt64 characterId = client != null &&
                client.ActiveCharacter != null ? client.ActiveCharacter._id : 0;
            if (characterId == 0)
                return;

            lock (EffectReplicationLock)
            {
                CombatExperimentState combat;
                if (!CombatExperimentStates.TryGetValue(client, out combat))
                {
                    combat = new CombatExperimentState();
                    CombatExperimentStates[client] = combat;
                }
                if (combat.ExitTimer != null)
                {
                    combat.ExitTimer.Dispose();
                    combat.ExitTimer = null;
                }
                if (inCombat)
                    combat.ExitTimer = new Timer(_ =>
                        ExitCombatExperiment(client), null,
                        10000, Timeout.Infinite);
                if (combat.InCombat == inCombat)
                    return;
                combat.InCombat = inCombat;

                Dictionary<UInt64, ReplicatedEffectState> effects;
                if (!ActiveReplicatedEffects.TryGetValue(client, out effects))
                    effects = new Dictionary<UInt64, ReplicatedEffectState>();
                ReplicatedEffectState sprint;
                if (effects.TryGetValue(SprintAbilitySpecId, out sprint))
                    sprint.Suppressed = inCombat;

                UInt64[] affected = sprint == null ||
                    sprint.BaseStats == null ? new UInt64[0] :
                    sprint.BaseStats.Keys.OrderBy(value => value).ToArray();
                Dictionary<UInt64, float> recomputed = sprint == null ?
                    new Dictionary<UInt64, float>() : ComputeStats(
                        effects.Values, sprint.BaseStats, null, null);
                Dictionary<UInt64, IDictionary<UInt64, float>> fixedMaps =
                    sprint == null ? new Dictionary<UInt64,
                        IDictionary<UInt64, float>>() : BuildModifierMaps(
                            effects.Values, sprint.FixedModifiers.Keys, true);
                Dictionary<UInt64, IDictionary<UInt64, float>> percentMaps =
                    sprint == null ? new Dictionary<UInt64,
                        IDictionary<UInt64, float>>() : BuildModifierMaps(
                            effects.Values, sprint.PercentModifiers.Keys,
                            false);
                refresh = AreaAbilityEffectReplication.CreateStatRefresh(
                    characterId, inCombat, recomputed, fixedMaps, percentMaps,
                    affected);
            }

            client.SendPacket(refresh);
            AreaPollExperiment.LogDecision(client, "CombatExperiment",
                String.Format(
                    "ability:combat-state fighting={0} sprintSuppressed={1} exitAfterMs={2}",
                    inCombat ? 1 : 0, inCombat ? 1 : 0,
                    inCombat ? 10000 : 0));
        }

        private static void ExitCombatExperiment(TORGameClient client)
        {
            try
            {
                SetCombatExperimentState(client, false);
            }
            catch (Exception ex)
            {
                AreaPollExperiment.LogDecision(client, "CombatExperiment",
                    "ability:combat-exit-failed:" + ex.Message);
            }
        }

        // Request body: Int32 blob length, then the style-5 client RPC blob.
        // The client-side selector uses its outbound C7/u32/u32 form; the five
        // arguments are type-tagged values in RequestAbilityActivate order.
        private static bool TryParseAbilityActivation(byte[] body,
            out UInt64 targetId, out UInt64 abilitySpecId,
            out Int64 requestId, out string failure)
        {
            targetId = 0;
            abilitySpecId = 0;
            requestId = 0;
            failure = "malformed-request";
            if (body == null || body.Length < 13)
                return false;

            int blobLength = BitConverter.ToInt32(body, 0);
            if (blobLength < 9 || blobLength != body.Length - 4)
            {
                failure = "bad-blob-length";
                return false;
            }

            int offset = 4;
            if (body[offset] != 0xC7 ||
                BitConverter.ToUInt32(body, offset + 1) != 0x1279C371 ||
                BitConverter.ToUInt32(body, offset + 5) != 0x001703D5)
            {
                failure = "unexpected-activation-selector";
                return false;
            }
            offset += 9;

            UInt64 type;
            Int64 syncTime;
            UInt64 queued;
            if (!TryReadPackedUnsigned(body, ref offset, out type) || type != 1 ||
                !TryReadPackedUnsigned(body, ref offset, out targetId) ||
                !TryReadPackedUnsigned(body, ref offset, out type) || type != 1 ||
                !TryReadPackedUnsigned(body, ref offset, out abilitySpecId) ||
                !TryReadPackedUnsigned(body, ref offset, out type) || type != 21 ||
                !TryReadPackedSigned(body, ref offset, out syncTime) ||
                !TryReadPackedUnsigned(body, ref offset, out type) || type != 2 ||
                !TryReadPackedSigned(body, ref offset, out requestId) ||
                !TryReadPackedUnsigned(body, ref offset, out type) || type != 3 ||
                !TryReadPackedUnsigned(body, ref offset, out queued) ||
                offset != body.Length)
            {
                failure = "bad-typed-arguments";
                return false;
            }
            if (requestId < 0 || requestId > Int32.MaxValue || queued > 1)
            {
                failure = "invalid-argument-value";
                return false;
            }
            failure = null;
            return true;
        }

        private static bool TryParseAbilityDeactivation(byte[] body,
            out UInt64 abilitySpecId, out string failure)
        {
            abilitySpecId = 0;
            failure = "malformed-request";
            if (body == null || body.Length < 13)
                return false;

            int blobLength = BitConverter.ToInt32(body, 0);
            if (blobLength < 9 || blobLength != body.Length - 4)
            {
                failure = "bad-blob-length";
                return false;
            }

            int offset = 4;
            if (body[offset] != 0xC7 ||
                BitConverter.ToUInt32(body, offset + 1) != 0x1279C371 ||
                BitConverter.ToUInt32(body, offset + 5) != 0x9D1796F2)
            {
                failure = "unexpected-deactivation-selector";
                return false;
            }
            offset += 9;

            UInt64 type;
            if (!TryReadPackedUnsigned(body, ref offset, out type) ||
                type != 1 ||
                !TryReadPackedUnsigned(body, ref offset,
                    out abilitySpecId) ||
                offset != body.Length)
            {
                failure = "bad-typed-arguments";
                return false;
            }
            failure = null;
            return true;
        }

        private static bool TryParseEffectRemovalRequest(byte[] body,
            out UInt64 ownerId, out UInt64 effectNodeId,
            out UInt32 functionSid)
        {
            ownerId = 0;
            effectNodeId = 0;
            functionSid = 0;
            if (body == null || body.Length < 13)
                return false;
            int blobLength = BitConverter.ToInt32(body, 0);
            if (blobLength < 9 || blobLength != body.Length - 4 ||
                body[4] != 0xC7 ||
                BitConverter.ToUInt32(body, 5) != 0x1279C371)
                return false;

            functionSid = BitConverter.ToUInt32(body, 9);
            int offset = 13;
            UInt64 type;
            return TryReadPackedUnsigned(body, ref offset, out type) &&
                type == 1 &&
                TryReadPackedUnsigned(body, ref offset, out ownerId) &&
                TryReadPackedUnsigned(body, ref offset, out type) &&
                type == 1 &&
                TryReadPackedUnsigned(body, ref offset, out effectNodeId) &&
                offset == body.Length;
        }

        private static byte[] BuildQueuedAbilityResult(UInt64 abilitySpecId,
            Int64 requestId)
        {
            var bytes = new List<byte>();
            WritePackedUnsigned(bytes, 0x54058C0EE7DC09C4UL);
            WritePackedUnsigned(bytes, 1);             // HeroTypes.Id
            WritePackedUnsigned(bytes, abilitySpecId);
            WritePackedUnsigned(bytes, 2);             // HeroTypes.Integer
            WritePackedSigned(bytes, requestId);
            WritePackedUnsigned(bytes, 5);             // HeroTypes.Enum
            WritePackedUnsigned(bytes, 1);             // effResultOk (first enum value)
            return bytes.ToArray();
        }

        private static bool TryReadPackedUnsigned(byte[] data, ref int offset,
            out UInt64 value)
        {
            value = 0;
            if (offset >= data.Length)
                return false;
            byte token = data[offset++];
            if (token < 0xC0)
            {
                value = token;
                return true;
            }
            if (token < 0xC8 || token > 0xCF)
                return false;
            int length = token - 0xC7;
            if (offset + length > data.Length)
                return false;
            for (int i = 0; i < length; ++i)
                value = (value << 8) | data[offset++];
            return true;
        }

        private static bool TryReadPackedSigned(byte[] data, ref int offset,
            out Int64 value)
        {
            value = 0;
            if (offset >= data.Length)
                return false;
            byte token = data[offset++];
            if (token < 0xC0)
            {
                value = token;
                return true;
            }
            if (token == 0xD0)
            {
                value = Int64.MinValue;
                return true;
            }
            bool negative = token < 0xC8;
            if (token > 0xCF)
                return false;
            int length = negative ? token - 0xBF : token - 0xC7;
            if (length < 1 || offset + length > data.Length)
                return false;
            UInt64 magnitude = 0;
            for (int i = 0; i < length; ++i)
                magnitude = (magnitude << 8) | data[offset++];
            if (magnitude > 0x7FFFFFFFFFFFFFFFUL)
                return false;
            value = negative ? -(Int64)magnitude : (Int64)magnitude;
            return true;
        }

        private static void WritePackedUnsigned(List<byte> output, UInt64 value)
        {
            if (value < 0xC0)
            {
                output.Add((byte)value);
                return;
            }
            int length = BytesNeeded(value);
            output.Add((byte)(0xC7 + length));
            WritePackedMagnitude(output, value, length);
        }

        private static void WritePackedSigned(List<byte> output, Int64 value)
        {
            if (value >= 0)
            {
                WritePackedUnsigned(output, (UInt64)value);
                return;
            }
            if (value == Int64.MinValue)
            {
                output.Add(0xD0);
                return;
            }
            UInt64 magnitude = (UInt64)(-value);
            int length = BytesNeeded(magnitude);
            output.Add((byte)(0xBF + length));
            WritePackedMagnitude(output, magnitude, length);
        }

        private static int BytesNeeded(UInt64 value)
        {
            int length = 0;
            do
            {
                ++length;
                value >>= 8;
            }
            while (value != 0);
            return length;
        }

        private static void WritePackedMagnitude(List<byte> output, UInt64 value,
            int length)
        {
            for (int shift = (length - 1) * 8; shift >= 0; shift -= 8)
                output.Add((byte)(value >> shift));
        }

        public override PacketType GetType()
        {
            return PacketType.CMsgF96DCDB0;
        }
    }
}
