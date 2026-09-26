using System;

namespace NexusToRServer.NET.Packets.Server
{
    static class AreaEnterSignals
    {
        public static void Fire(TORGameClient client)
        {
            if (client == null || client.AreaServiceID == 0 || client.AreaEnterSignalsSent)
                return;

            client.AreaEnterSignalsSent = true;
            UInt64 charID = client.ActiveCharacter == null ? 0UL : client.ActiveCharacter._id;
            client.SendPacket(new CharacterSetRendezvousPoint(
                charID, 1, -64.874100f, -6.906221f, -127.670998f,
                0.000000f, -90.000198f, 0.000000f, 1));
            client.SendPacket(new CharacterChangeState(
                charID, Environment.GetEnvironmentVariable("SWTOR_AREA_ENTER_STATE") ?? string.Empty));
            if (Environment.GetEnvironmentVariable("SWTOR_POST_STATE_ON_ENTER") == "1")
            {
                // The captured batch precedes the final CRTs. Repeat it once after
                // CRT17 acknowledgement and state change, when the character is complete.
                client.SendPacket(AreaStartupBundle.CreateOnEnter(charID));
            }
            Log.Write(LogLevel.Client,
                "AreaEnterSignals: rendezvous+state sent after character sync; char={0}; postStateOnEnter={1}.",
                charID, Environment.GetEnvironmentVariable("SWTOR_POST_STATE_ON_ENTER") == "1");
        }
    }
}
