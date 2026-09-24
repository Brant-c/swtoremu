namespace NexusToRServer
{
    public enum CPacketType : uint
    {
        Null = 0x00,
        ClientHello = 0x00000011,
        ConnectionHandshake = 0x04,
        Ping = 0x00000001,
        Pong = 0x00000001,
        RequestID = 0xA609E6A7,
        ReplyID = 0x6731C5AF,
        RequestIntroduceConnection = 0x8B0D492F,
        ReplyIntroduceConnection = 0x90F2D084,
        RequestClose = 0x43DB3479
    }

    public enum PacketType : uint
    {
        Null = 0x00,
        ClientHello = 0x00000011,
        ConnectionHandshake = 0x04,
        Ping = 0x00000001,
        Pong = 0x00000001,
        ObjectRequest = 0xA609E6A7,
        ObjectReply = 0x6731C5AF,
        SignatureResponse = 0x8B0D492F,
        ClientInformation = 0xD4BA5CFB,
        ServiceRequest = 0x5FE920D4,
        TimeRequesterRequest = 0x420923E0,
        TimeRequesterReply = 0x8D576F7B,
        HackNotifyData = 0x0C0BA34F,
        CMsgC26464A9 = 0xC26464A9,
        ModulesList = 0x2195CC8A,
        CharacterListRequest = 0xFB2047CE,
        CharacterListReply = 0x0EC2A425,
        SetTrackingInfo = 0xD0D38F43,
        SendScriptError = 0x09AB71E5,
        WorldByteReport = 0x8EB28DE9,
        RepositoryDataReceipt = 0xB4BF82C3,
        RepositoryDataRequest = 0x463B0D17,
        RepositoryDataNotFound = 0x2F7A6A25,
        RepositorySyncRequest = 0x45F77B86,
        RepositorySyncReply = 0x26959B72,
        RepositoryRevision = 0xA08C1ACF,
        RequestClose = 0x43DB3479,
        WorldNotifyGauntletVersion = 0x25ACBEF4,
        WorldRequestRPC = 0x25E86D5C,
        WorldHackPack = 0xECB59833,
        WorldShouldSendScriptErrors = 0x35BEBAA5,
        GameSystemNotifyID = 0x4BD75535,
        TrackingServerInit = 0x04CCE2BB,
        CreateCharacterRequest = 0xD130EAB9,
        SelectCharacterRequest = 0xCFFE7758,
        SelectCharacterReply = 0xA0D00B3A,
        WorldTravelPending = 0x246462DB,
        WorldTravelStatus = 0x7AD491DA,
        WorldSendToArea = 0x13509F15,
        ClientReplicationTransaction = 0x34287945,
        AreaHackPack = 0x0E71623B,
        AreaSendAwarenessRange = 0x1CA72F2D,
        AreaUpdateTimeSource = 0x8F0A39AA,
        AreaRequestRPC = 0x0ADFF9BF,
        AreaTeleportCharacter = 0x944511BF,
        SetMailboxInteraction = 0x01837678,
        AreaTalk = 0x6BA87A93,
        AreaSetCharacter = 0xCFBFFBCB,
        AreaEffEventMessage = 0xDBF41C90,
        CMsg7CB9A193 = 0x7CB9A193,
        AreaModulesList = 0x74D16DED,
        AreaClientReplicationTransaction = 0x0D446E80,
        HasMail = 0x4AA61E6B,
        AreaAwarenessEntered = 0xA1D9E226,
        SMsg23B61238 = 0x23B61238,
        SystemRequestRPC = 0x2D0B9303,

        // Opcodes seen from the client during world entry but never handled.
        // Naming them gives them a symbolic name in the packet log and gives the
        // handler an explicit case, so their traffic is decoded rather than
        // reported as an anonymous 'Unknown Packet'.
        CMsgC586BD22 = 0xC586BD22,
        CMsgF96DCDB0 = 0xF96DCDB0,
        CMsg4A765897 = 0x4A765897,
        CMsgCCACB51D = 0xCCACB51D,
        CMsg61116AD5 = 0x61116AD5,

        // Server->client RPC result message. The client's inbound handler
        // (client RVA 0x25214E -> handler 0x2521A4) reads two strings:
        //     string1 (0x97D270), string2 (0x97D270), then the end-of-message
        //     check (0x97D020), and dispatches both to the scripting layer.
        // Used to answer the client's own CMsgF96DCDB0 / CMsg4A765897 RPC
        // requests; without a result the client's script layer never completes
        // and it re-fires the same request forever.
        SMsgResults = 0xD5280283,

        // Server->client "enter world" signals, handled by the client's message
        // dispatch (0x2B4792AE at 0x64F4BC, 0xADEAFCA3 at 0x6501DD in the client
        // disassembly). Body layouts were decoded from those handlers:
        //   SetRendezvousPoint = (u64, u32, vec3, vec3, u8)
        //   ChangeState        = (u64, string)
        CharacterSetRendezvousPoint = 0x2B4792AE,
        CharacterChangeState = 0xADEAFCA3
    }
}
