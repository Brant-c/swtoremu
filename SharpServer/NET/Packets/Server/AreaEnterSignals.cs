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
            Log.Write(LogLevel.Client,
                "AreaEnterSignals: rendezvous+state sent after character sync; char={0}.", charID);
        }
    }
}