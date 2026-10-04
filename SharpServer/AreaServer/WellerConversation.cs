using System;
using System.Runtime.CompilerServices;
using NexusToRServer.NET;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.AreaServer
{
    internal static class WellerConversation
    {
        internal const UInt64 WellerNode = 0x1AC6F6DC6DUL;
        // Captured right-click request, distinct from target selection 9738A931.
        internal const UInt32 InteractionSid = 0x99EB62D0;
        // Both captured with one typed ID equal to our controller after the
        // last dialogue response. Exact finish/escape name mapping is pending.
        internal const UInt32 EndRequestSid = 0x70C14D2A;
        internal const UInt32 AlternateEndRequestSid = 0x14CDD239;
        private sealed class State { public UInt64 Character, Instance, Controller; }
        private static readonly ConditionalWeakTable<TORGameClient, State> States = new ConditionalWeakTable<TORGameClient, State>();
        internal static bool TryParse(byte[] body, out UInt64 owner)
        {
            return TryParseRequest(body, InteractionSid, out owner);
        }
        internal static bool TryParseRequest(byte[] body, UInt32 sid, out UInt64 owner)
        {
            owner = 0;
            if (body == null || body.Length < 15 || BitConverter.ToInt32(body, 0) != body.Length - 4 ||
                body[4] != 0xC7 || BitConverter.ToUInt32(body, 5) != 0x1279C371 ||
                BitConverter.ToUInt32(body, 9) != sid || body[13] != 1) return false;
            int offset = 14; byte token = body[offset++];
            if (token < 0xC0) owner = token;
            else
            {
                if (token < 0xC8 || token > 0xCF) return false;
                int count = token - 0xC7;
                if (offset + count != body.Length) return false;
                for (int i = 0; i < count; ++i) owner = (owner << 8) | body[offset++];
            }
            return offset == body.Length;
        }
        internal static bool Handle(TORGameClient client, UInt32 component, byte[] body)
        {
            if (Environment.GetEnvironmentVariable("SWTOR_WELLER_CONVERSATION") != "1") return false;
            if (body == null || body.Length < 13 || body[4] != 0xC7 ||
                BitConverter.ToUInt32(body, 5) != 0x1279C371) return false;
            UInt32 sid = BitConverter.ToUInt32(body, 9);
            if (sid == EndRequestSid || sid == AlternateEndRequestSid)
                return HandleEnd(client, component, body, sid);
            if (sid != InteractionSid) return false;
            UInt64 owner;
            if (!TryParse(body, out owner) || owner != WellerNode || client.ActiveCharacter == null ||
                component != (((UInt32)0x65B3 << 16) | client.AreaServiceID))
            {
                Log.Write(LogLevel.Warning, "WellerConversation: interaction rejected (body, target, player or component mismatch).");
                return true;
            }
            State state = States.GetValue(client, key => new State());
            lock (state)
            {
                UInt64 player = client.ActiveCharacter._id;
                if (state.Controller != 0 && state.Character == player)
                {
                    Log.Write(LogLevel.Client, "WellerConversation: duplicate interaction ignored; controller=0x{0:X16}.", state.Controller);
                    return true;
                }
                state.Character = player;
                state.Instance = AreaAbilityEffectReplication.NextNodeID();
                state.Controller = AreaAbilityEffectReplication.NextNodeID();
                client.SendPacket(new AreaWellerConversation(state.Instance, state.Controller, owner));
                Log.Write(LogLevel.Warning, "WellerConversation: EXPERIMENT start sent owner=0x{0:X16} instance=0x{1:X16} controller=0x{2:X16}; tree={3}; quest progression pending.", owner, state.Instance, state.Controller, AreaWellerConversation.ConversationName);
            }
            return true;
        }
        internal static bool CanEnd(UInt64 currentController, UInt64 requestedController,
            UInt64 currentCharacter, UInt64 selectedCharacter, UInt32 component, UInt16 areaService)
        {
            return currentController != 0 && currentController == requestedController &&
                currentCharacter != 0 && currentCharacter == selectedCharacter && areaService != 0 &&
                component == (((UInt32)0x65B3 << 16) | areaService);
        }
        private static bool HandleEnd(TORGameClient client, UInt32 component, byte[] body, UInt32 sid)
        {
            if (Environment.GetEnvironmentVariable("SWTOR_WELLER_END") != "1") return false;
            UInt64 requested; State state;
            if (!TryParseRequest(body, sid, out requested) || client.ActiveCharacter == null ||
                !States.TryGetValue(client, out state))
            {
                Log.Write(LogLevel.Warning, "WellerConversation: end rejected (malformed request or no conversation).");
                return true;
            }
            lock (state)
            {
                if (!CanEnd(state.Controller, requested, state.Character, client.ActiveCharacter._id, component, client.AreaServiceID))
                {
                    Log.Write(LogLevel.Warning, "WellerConversation: end rejected (stale/foreign controller, player or component).");
                    return true;
                }
                client.SendPacket(new AreaWellerConversation(state.Instance, state.Controller, WellerNode, 1));
                client.SendPacket(new AreaWellerConversation(state.Instance, state.Controller, WellerNode, 2));
                Log.Write(LogLevel.Warning, "WellerConversation: EXPERIMENT end sent sid=0x{0:X8} controller=0x{1:X16} then instance=0x{2:X16}; quest progression pending.", sid, state.Controller, state.Instance);
                state.Controller = 0; state.Instance = 0; state.Character = 0;
            }
            return true;
        }
    }
}
