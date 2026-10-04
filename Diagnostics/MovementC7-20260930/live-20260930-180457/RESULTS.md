# Experiment10 result: C7 accepted, wall persists

Launch18:04:57 server38568/main38304. Pinned server150A707AA20D324BEC1B19671BEE9B65CC1B3227BBB35A0654E179BBEF37C9CD and hook185B86C14C58C41F7E4F6972114C4DF7CEE99CB5D046EA62092F048134162FED confirmed. Both native hooks installed18:05:01. CRT3off18:09:14, startup sent18:09:15, first C5 accepted18:09:16.

Nine complete C7 messages accepted18:10:19–23 with body48, no Rejected decode. At18:10:23 last C7 precedes AreaReplicationDestroy; detector log18:10:24 crosses(-63.37 -> -62.94). Thus C7 reaches existing gameplay with correct end position and now triggers crossing while moving, before final C5 stop. Detector emitted one46-byte phase-info destroy, stream001B502E/node1AC6F6DC1F, same plaintext as prior runs. CRT18 suppressed.

Hook18:10:23 selects exteriorF4308000 from retreatD2339000 in areaF37B39A0, activation already3/6, selection returned exterior. All five exact-knight targets revalidated before/return; E0bit1000 and collider2Cbit40 clear. No collision re-enable. In this same hook file selection-return precedes incoming destroy parse, CRT17apply and named phsPhaseInfo.OnReplicationNodeDestroy enter/return. No nested gateway update logged. Cross-process second-resolution timestamps do not establish a total order.

Operator reports still stuck. Therefore C7 decoder fix is Behavior-verified for live acceptance and crossing detection; C7 rejection alone as wall cause is falsified for this controlled run. Do not claim whole wall solved or whole collision world clear. Preserve decoder fix; no guessed acknowledgement. Existing room/region observations repeated successfully; no need another run of these controls.

Small current logs saved18:10:40 before close, full194442-byte server/117789-byte hook/90448-byte launcher, zero errors. Manifest retains original saved paths in prelaunch-20260930-181040-554; copies here have same bytes. No process memory scan or dump. User advised can close.

Next offline question: what other physical collider or character room/physics association is responsible for the stop? Review native collision contact and character room-association paths against existing extracted room assets before choosing any new observer/run. This is unresolved, not a proven new packet requirement.
