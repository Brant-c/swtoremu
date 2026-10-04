# Startup ordering and authored destination audit

No runtime/configuration edits, process scan or new client run. Reference code
and preserved CRT3-off logs were compared; native excerpts were byte-prefix
verified against the same April executable. No new opcode identity was derived.

## Order: known changes, not complete verification

| Step | swtoremu2 reference | Current observed startup | Evidence/limit |
| --- | --- | --- | --- |
| Startup trigger | Area service attach reply | First AreaModulesList report | Current renders; waiting for module report supported by earlier world-startup investigation |
| SetCharacter | Twice after AreaTalk, before CRT2 | Once before HackPack and CRT1 | Deliberate old experiment; Handover-20260929-Notify says SetCharacter-first did not open wall |
| Teleport | Before CRT1 | After CRT2 | CRT2 contains placement; later placement avoids overwriting a diagnostic spawn |
| CRT1 then startup RPCs then CRT2 | This relative order | Retained | Source plus preserved construction log; actual generic client applies recorded in saved hook logs |
| Protective login effect | Effect fixture 1 sent | Suppressed in comparison configuration; replicated node removed by existing repair | Enables movement; not a verified room transition |
| CRT3 | Always replayed | Opt-in; last run omitted | Both controlled settings render/move but remain blocked |
| Awareness1 / OnEnter / effects2..8 / CRT4..10 / awareness2 / CRT11..17 | This order | Retained | Existing captures reused; character remapping and matched override are additional content differences |
| Doorway | No dynamic transition handler found in reviewed reference source | One phase-info destroy, CRT18 suppressed | Named destroy callback entered/returned; does not establish room selection |

`crt3off-observed-server-order.log` preserves the construction sequence from
the immutable 15:11:20 run snapshot. `TORGameClient.SendPacket` serially
constructs and synchronously writes each packet to its stream, rather than
using an outbound reordering queue. This shows the bundle's write order;
it is not independent proof of the native client's asynchronous asset or
script completion order. The startup-completed marker likewise proves emission.

The early SetCharacter placement is a remaining failed experiment, not a proven
prerequisite. Do not repeat its test or silently restore the legacy order while
claiming the CRT3 comparison remains unchanged. Any later order adjustment is
a new controlled variable requiring an explicit expected native observation.

## Destination: authored target confirmed; live selection unproved

Existing area.dat lists gnarls_new and all four retreat interiors. Their
authored visible-room links include gnarls_new. Each interior has a portal
target `4611686024647056040 gnarls_new`; exact records are preserved in
`authored-portal-targets.csv`. Relevant nearby targets:

- gnarls_retreat_int_d portal at `(-63.5996,-6.7407,-126.8874)` -> gnarls_new.
- gnarls_retreat_int_c portal at `(-62.4149,-6.7428,-126.9537)` -> gnarls_new.

These establish existing destination configuration in the extracted assets.
They do not identify the live interior, prove the portal is instantiated, or
show that the native player-room pointer changes. Both portal records have
PortalTag=false; do not filter solely on PortalTag=true when auditing links.
The area identifier remains tython_blockout/4611686019869492753/1; there is no
evidence this doorway requires travel to a different area instance.

## Correction: environment versus destination

Native parser VA 0x00B7D53B compares a room-setting key with `EnviroScheme`
(UTF-16 at 0x0115A950), resolves it and calls setter 0x00B79F70. That setter
stores the reference at object+0x1BC. Getter 0x00B7A040 and fallback
0x00B8D0F0 (name `Area`) feed the area+0x400 selection. Thus that path includes
environment selection; it is not sufficient evidence for destination-room
residency. Authored gnarls_new uses EnviroScheme=Area; retreat interiors use
interiorScheme. Earlier "related-room reference" wording was too broad.

The actual room-change routine remains VA 0x00B91AE0, updating area+0x298 and
global0x014927B0. Native entity association+0x98 can supply its argument.
Activation has a state+0x90==6 path and a deferred path. Those conditions are
statically established, but no saved live log resolves them for this doorway.

## Next evidence target

Determine whether the player's room association changes from a retreat interior
to gnarls_new and whether that object's native content reaches the activation
prerequisite. Trace the entity association setter and collision/portal path
offline before preparing a bounded event log for a new run. Existing server
construction logs cannot answer those native questions. Avoid another generic
doorway test, broad scan or guessed notification packet.
