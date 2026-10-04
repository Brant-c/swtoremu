# Result — experiment 08

Operator: loaded without action, then walked to doorway, stopped at wall,
still stuck. Main client13756; area F40E39A0. Launch16:34:05 Toronto.
Pinned DLL and input identity verified before crossing. No native hook cap,
prefix mismatch or unreadable target states in preserved logs.

## Decisive evidence

Same-PID name registrations at16:37:07:
- gnarls_retreat_int_d = D2C19000
- gnarls_new = F4C38000

At16:37:21 startup selected retreat_d. Nested activation of gnarls_new
entered with8C=2/90=6 and returned8C=3/90=6 before operator movement.
At16:39:58 doorway:
- Native select enter: old D2C19000, requested F4C38000, states3/6.
- Exterior activation entered args1,1,0 with states3/6 and returned3/6;
  surrounding room activations also executed. This is the already-active
  content-apply branch, not a new +90==6 transition from inactive state.
- Native select return stored F4C38000 (gnarls_new) at area+298.
- In the SAME hook log, that select return appears before the routed destroy
  parse and generic CRT17 apply/named phase-info destroy enter/return.
  File order is evidence; second-resolution timestamps do not prove ordering
  between all client threads or server/client clocks.
- Server accepted X -64.87 -> -62.93 and sent exactly46-byte destroy.
  SHA2562F816FE78E5A1C9983D2E151EB705E079AF4A323B4FE8F0559DE0B186766E5DF;
  PacketWorkbench comparison with baseline: equal,0differences.
- Named phase-info destroy entered/returned; no nested gateway update logged.
  This observer only logs gateway calls nested within destroy callback.
- CRT18 suppressed, CRT3 off, no retries. User still blocked.

## Conclusion and limits

Behavior-verified: this run selected authored gnarls_new and ran its activation
routine, while the wall remained. Failure to select the destination or to call
that activation routine is falsified for this run. Blanket claims that exterior
never activates are contradicted by the observed startup activation.

No proof of complete asset loading, collision readiness, player+98 association,
trigger identity/Collidable value, or which collider blocks the player.
Immediate +90 branch at doorway was not newly exercised: room was already8C3.
Do not promote a missing room packet, InstanceCreated, AssetCreated or CRT18.
Next offline target: gateway/trigger collision-setting path and physical
collider association after successful room selection. No further run needed
until a concrete collision target or correction is identified.

Evidence preserved: snapshot-manifest.csv and small full server/hook/launcher
logs here (~hundreds ofKB total), deciding-hook-events.log, exact destroy binary
and destroy-comparison.json. No stale diagnosticlogs or memorydumps copied.
User may close client now. Runtime diagnostic remains opt-in, no fix applied.
