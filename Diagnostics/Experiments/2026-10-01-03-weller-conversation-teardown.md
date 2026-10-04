# Experiment 2026-10-01-03 - Weller conversation teardown

## Question
Does removing the active controller then its instance in response to the captured end request restore the gameplay camera and input?

## Existing evidence
Experiment02 startup verified by user: cinematic and conversation played, end camera stuck. Start01:25:13, dialogue choices and final one-ID requests01:27:28/37 all reference created controller1AC7000002. Registry WellerConversationEndRequests. Jedipedia cnvControllerSingle OnReplicationNodeDestroy clears $CONVERSATION controller, calls UninitChoreographer (or disables conversation input), then instance.UninitConversation. That requires instance still alive.

## Single variable
SWTOR_WELLER_END=1: handle the two captured end selectors by sending ordered removal transactions and clear per-client server state. Existing startup/phase behavior retained. No quest mutation.

## Exact input
Run-SWTORClassic-WellerStory.cmd; pinned identity.csv; start remains SWTOR_WELLER_CONVERSATION=1. End fixtures end-body-70C14D2A.bin/end-body-14CDD239.bin; emitted end-8-1.bin/end-8-2.bin and area19 copies; hashes in fixture-hashes.csv. S2C0D446E80. First transaction reaffirms controller instance link and removes controller; next reaffirms instance owner/name and removes instance. Only active owned controller can request this.

## Predictions
Positive: end sent marker, normal gameplay camera/movement returns after natural completion; repeat interaction creates new nodes; Escape also releases scene.
Negative: end marker and client receipt confirmed but camera remains frozen, or destruction errors occur.
Inconclusive: no end request or no end sent marker, stale launcher/process/identity, unrelated scene error. Finish-vs-escape selector name remains unresolved; both guarded paths only release conversation.

## Evidence to preserve
Full small server and hook logs; operator report for natural completion, movement, repeat and Escape. WellerStory Preserve-CurrentLogs.ps1 retains SHA manifest.

## Result
Pending. Debug/x86 and strict end-request parsing/ownership guards pass. Independent capture schema decoder checks removal transactions, exact sizes/values and area8/19. Routing/framing38/wire54 pass. Launcher effective configuration and pinned inputs verified, both Weller flags1. Existing WorldEntryOffline missing observer source check unchanged.

## Conclusion
Teardown still Hypothesis until client confirms camera/input. Startup Behavior-verified. Quest hooks/persistence remain next work after lifecycle acceptance.
