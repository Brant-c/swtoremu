# Experiment2026-09-30-09 — Retreat trigger collision event log

## Question
Does a native TriggerNode for the knight retreat retain Collidable or physics membership across the blocked doorway crossing?

## Existing evidence
Experiment08 selected gnarls_new and ran activation, wall remained. Collision
control independently derived: TriggerNode property Collidable keyB4963DC1,
setter7FDE70, +E0 bit1000, +F0 collider/+2C bit40 association. Native identity
TriggerParam keyD84FB395 ->7FE1F0 ->string+138/firstpointer, hash+148/14C.
Static confidence Client-derived; no live trigger state yet. Detailed derivation
and bounded logger contracts: ../TriggerCollision-20260930/README.md.

## Single variable
Add opt-in native collision diagnostic, TRIGGER_COLLISION=1, to experiment08.
Two property hooks plus bounded event-derived target snapshots at existing
room selection events. No protocol/server change, no collision mutation.
All29 oldsettings match; fixedcaps. No scans/dumps/extra native calls.

## Exact input
Inputidentity.csv/newDLL185B86C14C58C41F7E4F6972114C4DF7CEE99CB5D046EA62092F048134162FED
in TriggerCollision-20260930. CRT3off/logonly/retrydisabled. Same existing S2C
0D446E80 area65B3/0008 destroy46bytes SHA256
2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF.
Authored3regions/1gateway and assethash exported, not live-presence proof.

## Predictions
Positive: identified same-object region collision/physics flags remain enabled
at valid room-switch snapshots, supported identity/localcoords. Supports that
region as blocker candidate; does not alone prove actual collision contact.
Alternative: flags/association cleared on all matched regions, weakening region
barrier explanation. No target identity/validposition/snapshot is inconclusive.
No calls by itself proves neither absence of a region nor cleared native state.

## Evidence to preserve
Fresh installation markers/PID/name maps, TriggerParam controls/targets,
Collidable calls and room selection snapshots, caps/unreadable markers.
Fresh server accepted crossing/exactdestroy/workbench, operator wall/outside.
Small current full server/hook/launcher logs; preserve before restart.

## Result
Completed live run17:28:07. At17:34:46 client switched tognarls_new; all5
identified retreat targets had collision1000/physics40clear before/return.
3regions andoriginalgateway matchauthoredcoords; clonealsoidentified.
17:34:47 C5cross/destroy/namedcallbackexecuted, userstillwall. No caps/faults.
UserreportedC7rejections;10complete56byte rawfixtures preserved, decoderC5only.
See [result](../TriggerCollision-20260930/live-20260930-172807/RESULTS.md).

## Conclusion
Measured persistent Collidable/physicsmembership on these regions falsified.
Target identity/flags Behavior-verified; notproofallcollisiongeometryclear.
Diagnosticstillopt-in. NextderiveAprilC7shape offline; extraMoveVec12bytes is
candidate supported bylegacyheader, not completeAprilverified schema.
No runtimefix/newpacket or newclientrun needed yet.
