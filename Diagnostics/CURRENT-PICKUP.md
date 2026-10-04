# Current pickup — foundation before taxi

Updated 2026-10-04, Toronto. This is the single active development checkpoint.
Read this, `Foundation-Audit-20261004.md`, then `Protocol-Evidence-Registry.md`.
Older handoffs, plans, audits, and experiment entries are historical evidence,
not instructions. See `Documentation-Status.md` for superseded material.

## Repository cleanup completed — awaiting review

The user requested the full `!emulator_clean_plan.txt` cleanup, ancestry audit
and architecture assessment, without new feature implementation. All nine
phases are assessed in `../docs/repository-cleanup.md`; progress and exact
inventories/manifests are in `RepositoryCleanup-20261004/`. Maintained overview:
`../README.md` and `../docs/{architecture,project-state,research-workflow}.md`.

75 fork-only root files were archived; 710 generated/local paths were removed
from tracking without physical deletion. Upstream baseline is cached 79eb5e9,
test1 HEAD 7785bc8; checkpoint branch and dirty binary patch preserve review
context. Existing hashed runtime inputs are unchanged. Both active C# projects
build in isolation; four baseline checks pass. WorldEntryOffline fails its
preexisting missing-observer assertion. RetreatGateway/Weller pins are stale;
Taxi pins match but do not prove gameplay. No live run or protocol fix occurred.

**Stop for user review.** The foundation investigations below and suggested
Phase 2 research-layer prompt are proposals, not instructions to continue now.
No taxi expansion or new AI/MCP implementation was started.

## User objective and current decision

Build a reliable April 2012 SWTOR emulator. Before extending taxi behavior,
resolve the character-load/phasing foundations and identify which compatibility
workarounds are necessary. The user explicitly redirected work away from taxi
feature development and requested this consolidated pickup and documentation
cleanup. Do not restart the old invisible-wall investigation by default.

## Accepted gameplay baseline

- World entry renders and the character moves, using compatibility settings.
- Retreat exit/reentry and improved gateway timing were accepted in prior runs.
  This establishes the local behavior, not the original general phase engine.
- Weller's model, nameplate, and quest indicator existed before NPC work.
  First conversation and normal conversation ending were enabled later; quest
  progression and persistence remain incomplete.
- Exterior NPC models are visible. The medcenter droid is not targetable or
  interactable according to the user; do not call it a working gameplay NPC.
- Taxi terminal remains absent. Map marker/tutorial do not prove its creation,
  targetability, interaction, map opening, or travel. No taxi success is accepted.

## Current implementation, not assumed normal lifecycle

Character selection constructs an ID-only Character; no saved state is loaded.
WorldSendToArea names fixed Tython instance 1. Area startup replays a captured
session, substitutes the player ID, uses generated CRT1/CRT4 phase-order overrides,
omits Safe Login protection, forces mobility and loaded fields in CRT16/17,
and teleports to the fixed captured start. The compatibility launcher patches
the loading phase-confirmation branch. Client-reported movement refreshes the
tether anchor every >=250 ms. A local plane/corridor detector clears/restores
membership using captured phase identities. General server simulation, phase
eligibility, area lifecycle, and dynamic awareness are not established.

Active Taxi launcher also enables Weller and ability experiments through its
inherited Trace-Tython wrapper. Its name does not describe the whole baseline.
The legacy PhaseExit one-shot path is bypassed with PHASE_REENTRY=1; CRT3 and
phase-instance retry are off in the reviewed run. Uncalled room-activation
helpers are not active streaming behavior.

## Foundation findings to address

1. Phase exit also replaces the positive-effect container with captured slot 1.
   Ability replication shares that container. Potential buff/bookkeeping damage
   is a Hypothesis; no live reproduction was performed. Investigate necessity
   and remove the unrelated mutation only through a controlled experiment.
2. Mobility is isolated into its own record because combined updates failed.
   That workaround works locally; the cause may be serialization or lifecycle
   and is unresolved. Do not treat "field poisons record" as an explanation.
3. Loading completion bypasses the original server phase-confirmation exchange.
4. Startup sent flags are set before completion; failure can leave partial entry
   marked complete. Connection flags lack a clear new-area reset boundary.
5. Movement gameplay does not validate the decoded component against the active
   area service. Finite coordinates alone do not establish authority.
6. AreaEnterSignals.Fire is called only in movement Echo mode, while the current
   mode is Swallow. Environment state settings alone do not prove packets sent.

Detailed source references and limitations: `Foundation-Audit-20261004.md`.

## Proposed first foundation task after review

Perform a bounded schema26 player-update encoding audit before changing runtime:

1. Preserve the dirty tree and accepted baseline. Identify active switches,
   actual CRT inputs/transformations, native reader evidence, and relevant tests.
2. Compare field9 mobility encoding with field129 loaded Boolean encoding and
   field100 stat-map ordering using the April native reader and local
   `Tools/Hero/Hero/PackedStream.cs`. Use PacketWorkbench for existing fixtures.
3. Produce one supported conclusion: a demonstrated encoding defect and smallest
   opt-in correction, or the exact remaining uncertainty. Do not bisect blindly,
   remove all workarounds, synthesize a taxi, or expand observer tooling.
4. Run applicable existing offline checks before/after any packet change. Record
   one-variable native experiments before asking the user to run the client.

Then address phase-exit effect coupling, original loading confirmation, explicit
entry/reset state, and the captured medcenter's targetability as the general NPC
control. Reorder only when new evidence establishes a dependency.

## Evidence and log interpretation

- Accepted phase behavior: `RetreatGateway-20261001/prelaunch-20261001-003805-442/RESULTS.md`
  and `RetreatReentry-20260930/prelaunch-20261001-002114-440/RESULTS.md`.
- October 4 reviewed server trace: `last-server-full.log` and
  `../SharpServer/bin/Debug/NexusToR.log`; launcher: `last-compatibility-run.log`.
  These paths are mutable. Preserve/hash them before another launch if needed.
- At14:59:41 taxi node1AC7000001 sent; at14:59:43 matching-node appearance errors;
  at15:00:06 retreat exit logged. Earlier taxi errors cannot be caused by that
  later crossing, but a shared startup defect remains possible.
- `prelaunch-*` directories preserve the PRECEDING run. Folder timestamps are
  not the timestamps of the enclosed gameplay. Inspect log contents and identity.
- No new live run, runtime fix, or baseline tests occurred during this audit.
- Historical manifests/launchers may have stale pins. Do not silently regenerate
  all hashes or advertise a launcher as ready without checking its inputs.

## Completion criteria for foundation work

One documented entry sequence with explicit selected-player/area/phase/effect
ownership; understood player encoding; loading confirmation accounted for;
phase changes do not mutate unrelated effects; repeatable entry/exit/reentry
without partial initialization or duplicate state. Keep any remaining workaround
explicit and bounded. Rendered scenery alone does not meet these criteria.
