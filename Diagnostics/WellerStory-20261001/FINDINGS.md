# Weller conversation startup, 2026-10-01

Captured source: ../RetreatGateway-20261001/prelaunch-20261001-010315-023/NexusToR.log, preserved with SHA256 manifest.

At 01:02:33 target selection sent selector 1279C371:9738A931 once. The four interactions sent 1279C371:99EB62D0 at 01:02:33, :34, :36, :38, all with one typed ID argument, runtime node 1AC6F6DC6D. Do not conflate the target selector with the four clicks. Exact body: 10-00-00-00-C7-71-C3-79-12-D0-62-EB-99-01-CC-1A-C6-F6-DC-6D. The public name of the generic interaction entry point remains unresolved; contextual attribution to Weller right-click is Captured.

Jedipedia reader loaded scripts: cnvControllerSingleClassMethods (14988052517490532956), cnvInstanceClassMethods (14988211127375339264), cnvOwnerComponentClassMethods (14988042477242067960). The controller's OnReplicationNodeCreate resolves cnvControllerInstance.LoadConversationTree, registers itself with $CONVERSATION, and calls InitController. The instance uses cnvInstanceConversationName and the client's tree GetStartNode/FollowLinksAndLogicTree. The controller then creates its local choreographer. No server dialogue text or forced start-node override is needed for this startup experiment.

Weller NPC prototype npc.location.tython.class.jedi_knight.attack_of_the_flesh_raiders.derrin_weller specifies cnv.location.tython.class.jedi_knight_new.derrin_weller. The owner component resolves override, then placeable name, then this prototype name.

Captured CRT1 already defines structure60 cnvInstance: owner ID and conversation String; structure59 cnvControllerSingle: instance NodeRef. All captured CRT object lists were searched using structure_id; no instance/controller creation records were found in CRT2..17. Kind15 is NodeRef (HeroTypes.cs/HeroNodeRef.cs), despite the diagnostic's shorthand ClassRef label. The generated response uses captured schemas, style8 values, instance before controller, independent fresh runtime IDs, and the existing stream sequence allocator. The predicted startup effect remains Hypothesis until a client run.

Opt-in SWTOR_WELLER_CONVERSATION=1 intercepts only selector99EB62D0, validates the complete typed body, component and selected player, and permits only captured Weller node. It ignores duplicate clicks while its controller exists. Default behavior is unchanged. Completion/escape cleanup, quest grants/progression, persistence, and exterior NPC replication are pending. Do not claim a full conversation lifecycle or story implementation from a successful startup.

Verification: Debug/x86 build passed. Strict input rejection passed for truncations, corrupt selector/type, trailing byte; area8/19 routing passed. Independent CRT decoder consumed both generated records exactly (130-byte packet), checked captured class/schema identities, values, reference and all field-presence states. AreaRouting, AreaBlobFraming (38 bodies), AreaWireRoundTrip (54 fixture packets) and PacketWorkbench passed. WorldEntryOffline still fails its existing missing RequestWorldFadeIn observer source check; no hook changes were made.

WellerStory Launch.ps1 -VerifyOnly passed effective configuration and SHA checks. Existing retreat phase flags retained. Historical RetreatGateway identity intentionally retained; it will reject the newly built server. Use Run-SWTORClassic-WellerStory.cmd for this experiment.

Next operator action: stay in retreat, right-click Weller once, observe cinematic/choice wheel or errors, then close client. Preserve logs before any further build. Search WellerConversation start marker, serialization/entry-point/conversation errors and subsequent RPCs. If scene fails, distinguish schema/create acceptance from client tree eligibility/stage loading. Do not repeat broad observer work.

## Startup accepted; teardown implemented
See RESULTS-START.md: user confirms cinematic/conversation. Capture prelaunch-20261001-012911-086 shows final controller requests swallowed. New SWTOR_WELLER_END handles only captured70C14D2A/14CDD239, fully bounded, matches active owned controller/character/area, destroys controller before instance in separate ordered transactions, clears state for repeat interaction. No quest commit. Tests and effective launcher configuration pass; native cleanup acceptance pending.
