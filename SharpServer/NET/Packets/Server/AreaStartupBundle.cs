using System;

namespace NexusToRServer.NET.Packets.Server
{
    /// <summary>
    /// The complete area-server startup bundle for one character entering an
    /// area. The sequence and payloads are the ones recovered from the
    /// tython_blockout capture set (AreaServer/CRT, AreaServer/Awareness,
    /// AreaServer/EffectEvent, AreaServer/HackPacks).
    ///
    /// This is emitted from the AreaModulesList handler rather than from the
    /// area-service attach reply. The world side of this server waits for the
    /// client's ModulesList module report before it emits the world startup
    /// packets; AreaModulesList is the area-side equivalent report
    /// (Packets/MessageHeaders/msg_area_modules_list.h has the same
    /// MessageID/StreamID/Payload shape as msg_modules_list.h). Sending the
    /// area state before the client reported its area modules left the client
    /// area-loaded but never in-world.
    /// </summary>
    static class AreaStartupBundle
    {
        public static void Send(TORGameClient client)
        {
            if (client == null) return;
            if (client.AreaServiceID == 0)
            {
                Log.Write(LogLevel.Warning, "AreaStartupBundle: area service not attached; startup not sent.");
                return;
            }

            string area = client._area ?? string.Empty;
            string areaID = client._areaID ?? string.Empty;
            string areaCode = client._areaCode ?? string.Empty;

            client.SendPacket(new AreaHackPack(area, areaID, areaCode));
            client.SendPacket(new AreaUpdateTimeSource());
            client.SendPacket(new AreaSendAwarenessRange(9.000000f, 13.500000f));
            client.SendPacket(new AreaRequestRPC(new byte[] { 0xCF, 0x2B, 0x7E, 0x42, 0x02, 0x2E, 0x10, 0x03, 0x0D, 0x06, 0x00 }));
            client.SendPacket(new SetMailboxInteraction(false));
            if (client.ActiveCharacter != null)
                client.SendPacket(new AreaTeleportCharacter(client.ActiveCharacter._id, 0x01, -64.874100f, -6.906221f, -127.670998f, 0.000000f, -90.000198f, 0.000000f, 0x01));
            client.SendPacket(new AreaClientReplicationTransaction(area, areaID, areaCode, 1));
            client.SendPacket(new AreaRequestRPC(new byte[] { 0xCF, 0x75, 0xDC, 0xE5, 0xC3, 0x03, 0x11, 0xA4, 0xC8 }));
            client.SendPacket(new AreaRequestRPC(new byte[] { 0xC7, 0x4F, 0x77, 0x41, 0xBD, 0xE7, 0xFF, 0x95, 0x39, 0x02, 0x05, 0x02, 0x05 }));
            client.SendPacket(new AreaRequestRPC(new byte[] { 0xC7, 0x75, 0xA1, 0x1A, 0xAF, 0x77, 0x65, 0x06, 0x24, 0x03, 0x01 }));
            client.SendPacket(new AreaRequestRPC(new byte[] { 0xC7, 0x0C, 0x19, 0xE0, 0xBE, 0x7A, 0xDB, 0x81, 0x73 }));
            client.SendPacket(new AreaTalk("logon", "@str.gui.characterselection#199(" + area + ") (" + areaID + ") (" + areaCode + ")"));
            if (client.ActiveCharacter != null)
                client.SendPacket(new AreaSetCharacter(client.ActiveCharacter._id));
            client.SendPacket(new AreaClientReplicationTransaction(area, areaID, areaCode, 2));
            client.SendPacket(new AreaEffEventMessage(area, areaID, areaCode, 1));
            client.SendPacket(new SystemRequestRPC(new byte[] { 0xC7, 0x07, 0xE5, 0x4B, 0x65, 0x7A, 0x20, 0x86, 0x83 }));
            client.SendPacket(new AreaRequestRPC(new byte[] { 0xCF, 0x75, 0xDC, 0xE5, 0xC3, 0x03, 0x11, 0xA4, 0xC8 }));
            client.SendPacket(new AreaRequestRPC(new byte[] { 0xCF, 0x65, 0xF1, 0x36, 0x91, 0x30, 0x11, 0x03, 0x85, 0x08, 0x02, 0x02, 0x00, 0x00, 0x07, 0x02, 0x00, 0x00, 0x08, 0x02, 0x04, 0x00, 0x00, 0x08, 0x02, 0x06, 0x00, 0x00, 0x08, 0x02, 0x07, 0x00, 0x00 }));
            client.SendPacket(new AreaRequestRPC(new byte[] { 0xC7, 0x07, 0xE5, 0x4B, 0x65, 0x48, 0x36, 0xA3, 0xC6, 0x08, 0x01, 0x03, 0x00, 0x00 }));
            client.SendPacket(new AreaClientReplicationTransaction(area, areaID, areaCode, 3));
            client.SendPacket(new AreaRequestRPC(new byte[] { 0xCF, 0x05, 0x77, 0x43, 0xE1, 0xC6, 0xB9, 0xC0, 0x9A, 0x02, 0x00 }));
            if (client.ActiveCharacter != null)
                client.SendPacket(new HasMail(client.ActiveCharacter._id));
            client.SendPacket(new AreaRequestRPC(new byte[] { 0xC7, 0x4F, 0x77, 0x41, 0xBD, 0xE7, 0xFF, 0x95, 0x39, 0x02, 0x05, 0x02, 0x05 }));
            client.SendPacket(new AreaAwarenessEntered(area, areaID, areaCode, 1));
            client.SendPacket(new SMsg23B61238(0x01, new byte[] { 0xCF, 0x43, 0x12, 0xBC, 0xBA, 0x6B, 0x8F, 0x69, 0xE0, 0x01, 0xCF, 0x40, 0x00, 0x01, 0x0E, 0x21, 0x8A, 0x83, 0x9C, 0x01, 0xCF, 0x40, 0x00, 0x01, 0x0E, 0x21, 0x8A, 0x83, 0x9C, 0x01, 0xCF, 0x40, 0x00, 0x01, 0x0E, 0x21, 0x8A, 0x83, 0x9C, 0x01, 0xCF, 0xE0, 0x00, 0x9E, 0xBF, 0xFA, 0xA2, 0xE2, 0x04, 0x06, 0x08, 0x4F, 0x6E, 0x20, 0x45, 0x6E, 0x74, 0x65, 0x72, 0x02, 0x01, 0x07, 0x01, 0x00, 0x00 }));
            for (int eff = 2; eff <= 8; eff++)
                client.SendPacket(new AreaEffEventMessage(area, areaID, areaCode, eff));
            for (int crt = 4; crt <= 17; crt++)
            {
                client.SendPacket(new AreaClientReplicationTransaction(area, areaID, areaCode, crt));
                if (crt == 10)
                    client.SendPacket(new AreaAwarenessEntered(area, areaID, areaCode, 2));
            }

            Log.Write(LogLevel.Client, "AreaStartupBundle: area startup sent; area=({0})/({1})/({2}).", area, areaID, areaCode);

        }
    }
}