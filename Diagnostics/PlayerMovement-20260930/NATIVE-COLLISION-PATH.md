# Native movement collision path, 2026-09-30

Confidence: Client-derived. No new live result or packet claim.
All addresses below are preferred virtual addresses in the pinned executable,
not RVAs or runtime addresses. See Locate-PlayerBehavior.py for PE hash and
byte checks. The output verifies instruction prefixes; adjacent jump tables
in a linear listing are data, not executable instructions.

## Jedipedia April1.2.0 findings

chrBehaveClassMethods14988251745630664747 registers its per-frame callback.
OnFrameUpdate calls the stand/grounding/movement debug oracles, then the local
player's BehaviorFinalAnimUpdate, camera/behavior rendering and metrics. This
establishes a script source for final animation/transmission scheduling; it
does not itself identify the native collision caller.

chrMoveDebugClassMethods14988218968260248917 is an optional movement action
tester. Its action can synthesize movement or send a server command. Do not
enable or invoke it as a passive diagnostic. It is not the ordinary input path.

chrGroundingDebugClassMethods14988137249406313410 creates an optional grounding
debug handle and updates it. chrStandDebugClassMethods14988050961431879266
obtains character collider/grounding bounds and calls GetSupportingSurface
with slope threshold, output position and output normal. STAND/SLIP/other
results receive different render colors. This is a floor support query;
it is not a general proof that the player can move horizontally.

Exact dictionary hashes and native registrations:

| Name | Hash | Registered wrapper |
| --- | --- | --- |
| GetCharacterColliderBounds_o | 103589FD | C1AA90 |
| GetCharacterGroundingBounds_o | 5BBE1820 | C1AB70 |
| GetCharacterSlopeThreshold | CED9BDA4 | C1A500 |
| GetSupportingSurface | 9478901D | C150E0 |

C150E0 obtains the manager through global14928F0+858 and calls CEF540.
The derived bounds wrapper bodies have not all been audited yet. Do not infer
their full wire format or ABI from registrations.

## Collision and support are distinct native branches

BehaviorPlayerCharacterBWA primary table115098C slot+24 points to722250.
That routine obtains the controller at behavior+20C and calls737120 at722469.
737120 resolves behavior through controller+0C, character through behavior+B8,
and compares that character with global14929DC+4. For character mode values
1/4/5/3 it calls737520 at737209. Separately it conditionally calls739AE0 at
73722A. These numerical modes are not yet named enums.

737520 compares current character position at node+2C/+30/+34 against the
saved vector at behavior+F0. It derives character bounds with7291A0 and calls
7B7450 at737732 with six stack arguments: saved position, current position,
bounds, output position, result collection, and Boolean1. It consumes the
collision result, iterates records with strideE0, and adjusts movement.
This is a stronger normal movement candidate than the previous target-relative
7228A0: it is directly in the player's behavior update and uses the player's
position delta rather than a target node. Live doorway coverage remains to be
confirmed, including bypass flags and callback scheduling.

7B7450 has a plain caller-cleaned stack argument layout, returns AL, and writes
the output position. Its full bounded listing reaches return7B78C5. It queries
global14928F0+858 through slots+20/+24 with numeric category2. The branch with
a result collection uses slot+24 at7B7715; an accepted step updates the output
position, while a positive collision outcome enters adjustment branches. Do
not equate function return true with successful travel: its caller branches
into collision processing on true. Individual result-record identity fields
are still unresolved.

739AE0 conditionally calls738F80 at739C1B and stores its numeric result at
controller+8. 738F80 calls CEF540 at7394DF and739668, then applies the selected
position through738DE0 ->739990/739A30 ->6D5D60. Thus the character update and
Jedipedia's stand tester share the native supporting-surface routine.

7EA870, reached from721D40, only initializes/updates the node+2D0 state's
position and flags in the reviewed body. It is not the physical collision
query; do not hook it as a wall detector based on its location in behavior code.

## Next bounded evidence

Measure the local player's proposed delta versus accepted output in7B7450,
filtered to caller737737 and the doorway vicinity. Record result count and
confirmed collider identity if the record schema can be recovered. Measure
the supporting-surface result only for the same character/frame. This separates
physical contact rejection from floor support rejection. No need to log every
ray, entire VM context, or repeat confirmed phase/UI exit.

No observer was installed and no launcher/runtime setting changed in this
stage. The evidence does not yet identify which object stops the character or
prove missing room readiness. No client run is requested yet.

## Implemented bounded diagnostic (experiment15)
The preceding no-observer statement describes the earlier audit stage. MovementCollisionTrace.h now implements exact-prefix guarded passive sweep/support/context hooks. ReleaseWin32 build succeeds; new MovementCollision-20260930 launcher VerifyOnly passes and identity pins are separate from experiment14. Standing samples excluded; support linked to same character and recent movement. Contact+80 interface follows native C15380: subtract4 then dereference object+94 reference storage. Up to4 contacts recorded per sample, room+98 and collider+F0 linked to known trigger table. No field or collision writes and no extra queries. Live coverage and blocking object remain pending. Query output is not itself final accepted character position.
