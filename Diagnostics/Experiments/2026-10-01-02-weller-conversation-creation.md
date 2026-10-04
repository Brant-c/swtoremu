# Experiment 2026-10-01-02 - Weller conversation creation

## Question
Does responding to the captured Weller right-click with schema60 instance then schema59 controller start the existing client conversation tree?

## Existing evidence
Four user-reported clicks captured at 01:02:33/34/36/38, selector1279C371:99EB62D0, Weller node1AC6F6DC6D. Registry WellerRightClickCaptured. Captured schemas59/60 define all transmitted fields. Jedipedia cnvControllerSingle OnReplicationNodeCreate initializes the conversation; cnvInstance loads the named tree and evaluates its own starting branch. Generated create lifecycle awaits acceptance.

## Single variable
Enable SWTOR_WELLER_CONVERSATION=1: reply to Weller interaction with conversation instance/controller creation. Retain working retreat/tether flags.

## Exact input
Pinned files and SHA256 in Diagnostics/WellerStory-20261001/identity.csv; launcher Run-SWTORClassic-WellerStory.cmd. C2S body click-body.bin. S2C 0D446E80 destination area8 (dynamic), create values fixture conversation-8.bin; stream and allocated instance/controller IDs vary. All bytes independently decoded by Verify-Conversation.py. Exact fixture hashes in fixture-hashes.csv.

## Predictions
Positive: WellerConversation EXPERIMENT start sent, client starts cinematic and dialogue choices without serialization errors.
Negative: delivered creation produces schema/node deserialization errors, or accepted nodes fail tree initialization/eligibility/stage readiness. Distinguish those failures through existing client/server logs.
Inconclusive: missing start marker, wrong launcher, stale process or inputs, no Weller interaction delivery. No new native observer.

## Evidence to preserve
Current log source already saved with SHA manifest. New server/client logs saved by WellerStory Preserve-CurrentLogs.ps1 after run. Operator visible cinematic/choice-wheel report.

## Result
Pending client run. Offline build/strict parser/captured schema checks pass; routing/framing/wire/workbench pass. Existing WorldEntryOffline missing RequestWorldFadeIn observer failure persists.

## Conclusion
Still opt-in. Story quest progression, conversation completion/escape cleanup and persistence remain pending. Do not claim story completed on startup acceptance.
