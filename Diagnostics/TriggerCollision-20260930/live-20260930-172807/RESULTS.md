# Experiment09 result — region collision is clear at the blocked transition

User loaded without movement, crossed once, stopped atwall still stuck.
Freshlaunch17:28:07 Toronto, main10580/server8188; pins and installedDLL match.
No caps/prefix mismatch/target readfailures in preserved logs.

## Decisive observations
Native exactTriggerParam+validlocalcachedcoords identify3authoredINSTANCE_REGIONs,
originalgateway andnewnamedgatewayclone (seePRE-CROSSING andcoordinate-map).
All5nativeobjects materialized in this run; older blanketabsenceclaims refuted.
Atstartup3regionsCollidable1then0, bit1000 andcollider40 bothsetthenclear.
17:34:46 native roomselect changesretreat_dD312A500 tognarls_newF5199500.
Before ANDreturn snapshots revalidateall5targets; bit1000clear andcollider40clear
for all, exactauthoredlocalcoords unchanged. No target collisionre-enable logged.
This falsifies persistent Collidable/physicsmembership on these identified
regions as the measured explanation at transition; not an inventoryofallcolliders.
17:34:47 acceptedC5 X -64.87->-62.92; exact46-byte destroySHA256
2F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF,
workbench0differences. GenericCRT17 bracketsnamedphaseInfoDestroyentry/return;
no nestedgateway logged. CRT3off/CRT18suppressed, userwallpersists.

## User-reported C7 decode rejection
17:34:43 through17:34:47 serverrejects unsupportedmovementvariantC7, length56,
offset8. Exactrawsamples saved movement-c7-samples.json/first.bin.
Current CMsg61116AD5 accepts ONLYC5 length44wholepacket; C7 has12additionalbytes.
Legacy msg_player_move_state.h has flag2 MoveVec (3floats) BEFORE EndPosition;
this is a candidate explanation for extra12bytes, not Aprilverified complete
schema. Headerdeclares16bitmask/endpadding while currentC5 decoderuses32bitword;
must verify Aprilnative widths/ordering before expanding gameplaydecoder.
C7 was rejected, but subsequentC5 DID trigger existingdestroy andclientroom
switch precededitsapply. Rejectionnotestablishedaswallcause. DefaultsC5also
swallowed/noack; don'tinvent C7 ack or unrelatednotification tofixwall.

## Conclusion
Behavior-verified narrowregionidentity/flagstate andexteriorselection. Wall
cause stillunresolved. Nativeworldgeometry/othercolliders/playerroom+98/
movementprotocol remaincandidates. Nextofflinework: deriveAprilC7 fields and
compareexistingmoveheader, retainrawfixtures; no more regionlogger runneeded.
No runtimefix/newpacket. Small currentlogs and exactbytes saved here via
snapshot-manifest.csv. Usercancloseclientnow; don'tauto-restart.
