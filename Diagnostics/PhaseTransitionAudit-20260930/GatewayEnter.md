# Gateway TriggerEnter comparison

The operator highlighted the reader's compiled `TriggerEnter(NodeRef Me,
NodeRef a1)` body at https://swtor.jedipedia.net/reader. Read-only DOM inspection
confirmed the body agrees with `_JPEXTRACT/phsGatewayClassMethods.txt`.

Observed sequence:

1. Require a valid entering node and equality with GetPlayerCharacterNode().
2. Hash the trigger's TriggerParam and resolve PHASE.GetPhasedInstanceNode.
3. Refresh UpdateGatewayForInstance for that instance's name ID.
4. Read the player's GetPhaseInfo().
5. Call the instance's OnPlayerEnteredGateway only when the player has no phase
   info or that info belongs to this same instance.

This body does not set phsPhase, teleport the player, select a native room, or
directly issue a server transfer request. It delegates further behavior to the
resolved instance. The class-specific handler in
`_JPEXTRACT/phsClassPhasedInstanceClassMethods.txt` checks eligibility, offers a
join popup for CanOwnOrJoin/CanJoinMultiple, or displays rejection messages.
The extracted base OnPlayerEnteredGateway body is empty; do not infer that every
override is empty. The separate PHASE.RequestJoinPhase method performs the
OnRequestJoinPhase server call after setting a join override.

For retreat exit, entering a gateway trigger is distinct from leaving existing
phase membership. The normal phsEntity phase-field update callback remains the
recovered exit input. TriggerLeave is unresolved in the extracted text, so this
comparison does not prove the complete production exit sequence.

Confidence: Client-derived script semantics; no new packet schema, runtime
acceptance, or lifecycle completeness claim. No hook or launcher changes and no
client run. Existing lifecycle hooks observe phase-info destruction, not the
phsEntity update or PHASE.OnPhasedInstanceUpdated callback.
