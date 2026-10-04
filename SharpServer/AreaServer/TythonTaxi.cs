using System;
using System.Runtime.CompilerServices;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.AreaServer
{
    internal static class TythonTaxi
    {
        private sealed class State { public UInt64 Player, Npc; }
        private static readonly ConditionalWeakTable<TORGameClient,State> States=new ConditionalWeakTable<TORGameClient,State>();

        /// <summary>
        /// Emits the taxi object list as its OWN awareness packet, after the
        /// captured startup objects.
        ///
        /// This is deliberately additive. Merging these records into awareness set
        /// 1 was tried and reverted: set 1 is the shared stream that carries every
        /// NPC already working (vendor, authored speeders), so a rejected or
        /// malformed appended list costs the whole object set, not just the taxi.
        /// An opt-in experiment must never take that blast radius. Rejected
        /// hypothesis recorded in Diagnostics/Experiments/2026-10-01-04.
        /// </summary>
        internal static void Initialize(TORGameClient client)
        {
            if (Environment.GetEnvironmentVariable("SWTOR_TYTHON_TAXI") != "1" || client.ActiveCharacter == null || client.AreaServiceID == 0) return;
            State state=States.GetValue(client,key=>new State());
            lock(state)
            {
                if (state.Player == client.ActiveCharacter._id && state.Npc != 0) return;
                UInt64[] nodes=new UInt64[5];
                for(int i=0;i<nodes.Length;i++) nodes[i]=AreaAbilityEffectReplication.NextNodeID();
                state.Player=client.ActiveCharacter._id; state.Npc=nodes[0];
                // Control mode swaps the generated taxi for a byte-for-byte copy of the
                // captured medcenter droid record (only the identity differs), so exactly
                // one NPC object is introduced either way and the sole variable against
                // runs 8a/8b is record content.
                if (CloneControl)
                {
                    // CONTROL no longer sends its own packet: the clone is merged into
                    // awareness set 1 by AreaStartupBundle, as one object list, because
                    // set 1 is delivered after any separate packet and the client never
                    // referenced our node afterwards. The node id is allocated here only
                    // so the log names the mode and the interaction handler stays disabled.
                    Log.Write(LogLevel.Warning,"TythonTaxi: CONTROL clone mode active; the captured medcenter droid clone is merged into awareness set 1 as one object list. Taxi interaction is disabled.",state.Npc);
                    return;
                }
                client.SendPacket(new AreaTaxiAwareness(nodes));
                client.SendPacket(new AreaTaxiInteraction(state.Player,0,false));
                Log.Write(LogLevel.Warning,"TythonTaxi: EXPERIMENT taxi NPC=0x{0:X16}; template=npc.location.tython.taxi.jediretreat_pad1; placement={1} (fixture hash logged by AreaTaxiAwareness); Retreat/Gnarls destinations unlocked for this session. Flight is pending.",state.Npc,AreaTaxiAwareness.Placement);
            }
        }
        private static bool CloneControl
        { get { return Environment.GetEnvironmentVariable("SWTOR_TAXI_CLONE_CONTROL") == "1"; } }

        /// <summary>
        /// CONTROL mode: the clone is not sent here as its own packet. It is merged
        /// INTO awareness set 1 by AreaStartupBundle, because the run log shows set 1
        /// arrives after any separate packet and the client never references our
        /// node afterwards -- the replacement-semantics signature. Returns the node
        /// id to merge, or 0 when the taxi path (separate packet) is in use.
        /// </summary>
        internal static UInt64 CloneNodeForMerge()
        {
            return CloneControl ? AreaAbilityEffectReplication.NextNodeID() : 0;
        }

        /// <summary>
        /// The merged taxi payload needs all five identities (the NPC record plus its
        /// four attached effect containers), so control mode allocates a full set here
        /// rather than a single node.
        /// </summary>
        internal static UInt64[] MergeNodes()
        {
            if (!CloneControl) return null;
            UInt64[] n = new UInt64[5];
            for (int i = 0; i < n.Length; i++) n[i] = AreaAbilityEffectReplication.NextNodeID();
            return n;
        }

        /// <summary>
        /// Selected ladder rung (0-3), defaulting to 0 when unset or malformed.
        /// </summary>
        internal static int LadderRung
        {
            get
            {
                Int32 r;
                return Int32.TryParse(Environment.GetEnvironmentVariable("SWTOR_TAXI_LADDER_RUNG"),
                                      out r) && r >= 0 && r <= 3 ? r : 0;
            }
        }

        internal static void LogCloneMerged(UInt64 node, int rung)
        {
            Log.Write(LogLevel.Warning,
                "TythonTaxi: CONTROL ladder rung {0} merged into awareness set 1 as one object list; npc=0x{1:X16}. Taxi interaction is disabled in this mode.", rung, node);
        }

        /// <summary>
        /// Records that the ladder rung could not be built and the captured awareness
        /// set was sent untouched, so a broken control can never be mistaken for a
        /// client that rejected the merged list.
        /// </summary>
        internal static void LogCloneFailed()
        {
            Log.Write(LogLevel.Warning,
                "TythonTaxi: CONTROL ladder rung FAILED to build; the captured awareness set 1 was sent UNCHANGED. This run tested nothing -- do not read it as a result.");
        }
        internal static bool Handle(TORGameClient client, UInt32 component, byte[] body)
        {
            State state;
            if (Environment.GetEnvironmentVariable("SWTOR_TYTHON_TAXI") != "1" || CloneControl || client.ActiveCharacter==null ||
                !States.TryGetValue(client,out state) || state.Player!=client.ActiveCharacter._id ||
                component != (((UInt32)0x65B3<<16)|client.AreaServiceID) || body==null || body.Length<14) return false;
            UInt32 sid=BitConverter.ToUInt32(body,9); UInt64 target;
            if (!WellerConversation.TryParseRequest(body,sid,out target) || target != state.Npc) return false;
            // Generic right-click request is captured. The second selector is
            // April compiled RequestUseTerminal at offset 0x4850 (client-derived).
            if (sid != WellerConversation.InteractionSid && sid != 0x574AFD80)
            {
                Log.Write(LogLevel.Warning,"TythonTaxi: bounded one-ID request to owned taxi sid=0x{0:X8}; awaiting selector attribution.",sid);
                return false;
            }
            lock(state)
            {
                client.SendPacket(new AreaTaxiInteraction(state.Player,0,true));
                client.SendPacket(new AreaTaxiInteraction(state.Player,state.Npc,true));
                Log.Write(LogLevel.Warning,"TythonTaxi: EXPERIMENT map interaction sent; npc=0x{0:X16} sid=0x{1:X8}; destination selection capture required before flight implementation.",state.Npc,sid);
            }
            return true;
        }
    }
}
