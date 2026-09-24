using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using NexusToRServer.NET.Packets.Server;

namespace NexusToRServer.NET.Packets.Client
{
    class ObjectReply : TORGameClientPacket
    {
        string _objID;
        string _objHash;
        string _objTarget;
        UInt64 _pID;
        UInt16 _serviceID;

        /// <summary>
        /// Reads and Parses the information stored in the Packet
        /// </summary>
        public override void ReadImplementation()
        {
            ReadUInt32(); // Packet Type
            ReadUInt32(); // Packet Component

            _serviceID = ReadUInt16();
            _objID = ReadString();
            _objHash = ReadString();
            _objTarget = ReadString();
            _pID = ReadUInt64(); // TODO: Match this with the sent pID
        }

        /// <summary>
        /// Runs the final Packet Implementation
        /// </summary>
        public override void RunImplementation()
        {
            Log.Write(LogLevel.Client, "Received Object Reply service=0x{0:X4} id='{1}' hash='{2}' target='{3}'", _serviceID, _objID, _objHash, _objTarget);
            switch (_objID)
            {
                case "omegaserverscriptcompilerobject":
                    GetClient().SendPacket(new SignatureResponse(0x65A9,
                                            _serviceID,
                                            "u" + GetClient().UserID.ToString() + "[ScriptCompilerServer:scriptcompiler]" + GetClient().Username + ".scriptcompiler",
                                            GetClient().EntryPoint,
                                            "815b44a:d4d18225:3d7e97f7"));
                    break;
                case "omegaclientscriptcompilerobject":
                    GetClient().SendPacket(new SignatureResponse(0x65AE,
                                            _serviceID,
                                            "u" + GetClient().UserID.ToString() + "[ScriptCompilerClient:scriptcompiler]" + GetClient().Username + ".scriptcompiler",
                                            GetClient().EntryPoint,
                                            "815b44a:d4d18225:3d7e97f7"));
                    break;
                case "omegascriptsearchobject":
                    GetClient().SendPacket(new SignatureResponse(0x65AF,
                                            _serviceID,
                                            "u" + GetClient().UserID.ToString() + "[SearchServer:searchserver]" + GetClient().Username + ".searchserver",
                                            GetClient().EntryPoint,
                                            "24d1e0af"));
                    break;
                case "OmegaServerProxyObjectName":
                    if (_objHash == "b7a6bba3:8ab55405:d7b5d3e1:5bc541f9")
                    {
                        GetClient().SendPacket(new SignatureResponse(0x65A7, _serviceID, "u" + GetClient().UserID.ToString(), GetClient().EntryPoint, "9cf74d45:1a6cc459:6fa57dc2"));
                        GetClient().SendPacket(new ClientInformation());
                        GetClient().State = ClientState.AUTHED;
                    }
                    break;
                case "Application_TimeRequester":
                    GetClient().SendPacket(new SignatureResponse(0x0006, _serviceID, "timesource", GetClient().EntryPoint, "462a9d1f"));
                    break;
                case "omegahandlerrepository":
                    GetClient().RepositoryServiceID = _serviceID;
                    GetClient().SendPacket(new SignatureResponse(0x65A8,
                                            _serviceID,
                                            "sp9u" + GetClient().UserID.ToString() + "[RepositoryServer:repositoryserver]" + GetClient().Username + ".repositoryserver",
                                            GetClient().EntryPoint,
                                            "979123dc:79bdb27:4ed529b0"));
                    GetClient().SendPacket(new RepositoryRevision(_serviceID));
                    break;
                case "omegaworldobject":
                    GetClient().WorldServiceID = _serviceID;
                    GetClient().SendPacket(new SignatureResponse(0x65AB,
                                            _serviceID,
                                            "sp2u" + GetClient().UserID.ToString() + "[WorldServer:worldserver]" + GetClient().Username + ".worldserver",
                                            GetClient().EntryPoint,
                                            "51e518d9:92367cb3:29f2db17"));
                    break;
                case "omegametricspublisherobject":
                    GetClient().SendPacket(new SignatureResponse(0x65AA,
                                            _serviceID,
                                            "sp1u" + GetClient().UserID.ToString() + "[biomonserver:biomon]" + GetClient().Username + ".biomon",
                                            GetClient().EntryPoint,
                                            "389fc8f0:9adcb7e6"));
                    break;
                case "omegamailresponseobject":
                    GetClient().SendPacket(new SignatureResponse(0x65B1,
                                            _serviceID,
                                            "sp6u" + GetClient().UserID.ToString() + "[Mail:mailserver]" + GetClient().Username + ".mailserver",
                                            GetClient().EntryPoint,
                                            "9759aa23"));
                    break;
                case "chatgatewayobject":
                    GetClient().SendPacket(new SignatureResponse(0x65AD,
                                            _serviceID,
                                            "sp4u" + GetClient().UserID.ToString() + "[ChatGateway:chatgateway]" + GetClient().Username + ".chatgateway",
                                            GetClient().EntryPoint,
                                            "900005df"));
                    break;
                case "auctionserverclientobject":
                    GetClient().SendPacket(new SignatureResponse(0x65B0,
                                            _serviceID,
                                            "sp5u" + GetClient().UserID.ToString() + "[AuctionServer:auctionserver]" + GetClient().Username + ".auctionserver",
                                            GetClient().EntryPoint,
                                            "9ce839f7"));
                    break;
                case "gamesystemsobject0":
                    GetClient().GameSystemsServiceID = _serviceID;
                    GetClient().SendPacket(new SignatureResponse(0x65AC,
                                            _serviceID,
                                            "sp3u" + GetClient().UserID.ToString() + "[GameSystemsServer:gamesystemsserver]" + GetClient().Username + ".gamesystemsserver",
                                            GetClient().EntryPoint,
                                            "450a2825"));
                    break;
                case "omegatrackingretailobject":
                    GetClient().TrackingServiceID = _serviceID;
                    GetClient().SendPacket(new SignatureResponse(0x65B2,
                                            _serviceID,
                                            "sp7u" + GetClient().UserID.ToString() + "[TrackingServer:trackingserver]" + GetClient().Username + ".trackingserver",
                                            GetClient().EntryPoint,
                                            "c5b320c1:8cebf93e"));
                    break;
                case "omegaareaobject":
                    GetClient().AreaServiceID = _serviceID;
                    Log.Write(LogLevel.Client, "Area service attached: server=0x65B3 client=0x{0:X4}. Routing area startup packets to this pair.", _serviceID);
                    GetClient().SendPacket(new SignatureResponse(0x65B3,
                                            _serviceID,
                                            String.Format("sp8u{0}[AreaServer-{1}-{2}-{3}-:areaserver]{4}.areaserver", GetClient().UserID.ToString(), GetClient()._area, GetClient()._areaID, GetClient()._areaCode, GetClient().Username),
                                            GetClient().EntryPoint,
                                            "91ac5777:62060b0:29f2db17"));
                    // NOTE 2026-09-18: the area startup bundle (HackPack, TimeSource,
                    // AwarenessRange, Teleport/SetCharacter, CRT 1-17, awareness,
                    // effect events, RPCs) moved to AreaStartupBundle and is now
                    // emitted by the first AreaModulesList report, mirroring how the
                    // world side waits for ModulesList before sending world startup.
                    // NOTE: second AreaSetCharacter removed 2026-09-18: the duplicate Set re-triggers
                    // Character-already-exists hero-script errors on the client. Single placement only.
                    // (AreaSetCharacter + the CRT/awareness/effect/RPC sequence are in
                    // AreaStartupBundle.Send, triggered by the AreaModulesList report.)
                    break;
                default:
                    break;
            }
        }

        /// <summary>
        /// Returns the PacketType of the specified Packet
        /// </summary>
        /// <returns>PacketType of specified Packet</returns>
        public override PacketType GetType()
        {
            return PacketType.ObjectReply;
        }
    }
}
