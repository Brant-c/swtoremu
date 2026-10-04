# Repository cleanup, ancestry audit and architecture assessment

Completed 2026-10-04 for `!emulator_clean_plan.txt`. All nine phases were
assessed; uncertain material is retained with explicit review items. No major
feature, protocol fix, client launch, server launch or new AI tooling was performed.
The cleanup is ready for operator review, not a claim of complete emulation.

## 1. Upstream relationship

- Branch: `test1`, HEAD `7785bc8`, matching cached `origin/test1`.
- Origin: `https://github.com/Brant-c/swtoremu.git`.
- Upstream: `https://github.com/g91/swtoremu.git`.
- Cached `upstream/master`, `origin/master`, local master and the merge base
  are `79eb5e9cf0c08dc72288eca0722d44a0a1293de0` (2019-11-24).
- Upstream history includes `a5c6e15` Initial commit and `79eb5e9` notice update.
  This is the best available original emulator import, not proof of every
  pre-import project's historical revision.
- Three ordinary descendant commits: `b94cf7d` initial commit (2026-09-23),
  `58718f5` Rigged entry to tython (messy state) (2026-09-26), and `7785bc8`
  Decompiled client from Jedipedia as reference (2026-10-02).
- Extensive dirty/untracked work and separate Cline checkpoint histories remain.
  A normal commit's author does not establish authorship of every included file.
  No fetch/push or remote-history update was performed; these are local Git facts.

`cleanup-baseline-20261004` protects the starting HEAD without switching branches.
Dirty tracked bytes are in the local binary-capable `tracked-before.patch`; the
starting index patch is empty. Status, history, remotes, both upstream diff lists
and untracked paths are saved in `Diagnostics/RepositoryCleanup-20261004`.
Material actually moved has per-file hashes. The checkpoint branch alone does
not preserve dirty/untracked files; no claim of a complete filesystem backup.

Major fork divergences: .NET/toolchain and Detours compatibility, login RSA
handling, repository asset delivery, area routing/framing, deferred world/area
startup, selected-character remapping, client loading fallback, player field
overrides, local movement/phase/story/ability/taxi experiments, tracing and large
research/generated output. Original C++ sources, native Packet.h, and original
C# fixture strategy remain architectural evidence. See architecture.md.

## 2. Removed

**No physical files or runtime code were deleted.** 710 fork-added generated or
local paths were removed from the Git index; their present bytes remain on disk
(two Python cache files were already absent on arrival). The exact list is
`untracked-generated-paths.txt`. Counts: Client 48, Diagnostics 538, Hacks 2,
nexusclient 10, Parser 10, SharpServer 18, Tools 84.

These comprise fork-added IDE/intermediate/cache output, selected symbol files,
generated Extracted2012/python-deps/ProcessMonitor content and mutable latest
logs. Original upstream paths, fixture blobs and required configs are excluded.
Git index removals are staged; documentation/archive moves are ordinary working
changes. No commit or push was made. Review the combined worktree carefully,
because it also contains the operator's substantial preexisting changes.

## 3. Archived

75 fork-only root files moved to `Archive/RepositoryCleanup-20261004/root-scratch`:
one-shot PowerShell build/state/toolchain/source probes, their `_*.txt` and
ToolingProbe outputs, `_launch_helper.ps1`, and three redundant Launch-Trace*
wrappers. The active Run-* and dated experiment launch chains remain unchanged.
`archive-manifest.csv` records original path, new path, reason and SHA256.

Prior README, START-HERE, AGENTS, dirty .gitignore, CURRENT-PICKUP and
Documentation-Status are copied to before-docs. Existing Historical-Handoffs,
dated runs and captured evidence are retained in their original locations;
relocating them would break pins and evidence links. Old Trace*.cpp executables
remain opt-in research instruments pending individual review, not supported
log collectors. Archived scripts must not be run without rechecking side effects.

## 4. Updated

- README now explains ancestry, actual status, prerequisites and build/start/log commands.
- Short operational AGENTS replaces historical narrative; START-HERE redirects.
- docs/architecture.md, project-state.md and research-workflow.md establish the
  maintained architecture, capability/dependency map and workflow.
- CURRENT-PICKUP records completion and waits for review; Documentation-Status
  identifies the maintained overview without promoting old plans.
- .gitignore preserves its starting dirty rules and adds local RuntimeLogs,
  audit build/patch output, Python dependency output and trace console output;
  required upstream area fixtures are explicitly excepted from generic bin rules.
- scripts/Build-Server.ps1, Start-Servers.ps1 and Collect-Logs.ps1 provide a small
  workflow around existing components. No emulator runtime source was edited.

## 5. Preserved and classified

| Significant group | Origin / classification | Disposition and reasoning |
|---|---|---|
| Server/, Packets/, original Parser source | UPSTREAM | KEEP; native architecture/protocol evidence, not replaced by the C# fork |
| SharpServer original transport/crypto/MongoDB and TOR/Character | UPSTREAM with selected local modifications | KEEP / INVESTIGATE; inherited TODOs and captured state are not later AI inventions |
| Fixed Tython route and bin/Debug/AreaServer fixtures | UPSTREAM; some CRT inputs later modified | KEEP; essential runtime/research data, not disposable build output |
| Login RSA, shared area routing/framing and locked logger queue | LOCAL-VALIDATED within existing checks/evidence | KEEP; purposeful differences, no reset to upstream |
| Bounded PacketCursor/message decoders | EXPERIMENTAL local safety work with regression checks | KEEP; no blanket migration or rollback |
| Startup, remap, CRT overrides and CompatibilityLauncher | PATCH/BYPASS | KEEP / INVESTIGATE; current world entry depends on them |
| PlayerMovementState, RetreatGatewayState and selected Weller behavior | LOCAL-VALIDATED bounded controls; patched architecture | KEEP; accepted local behavior does not prove general systems |
| PhaseExit/retry, taxi synthesis, ability variants, room helpers | EXPERIMENTAL | KEEP / INVESTIGATE; opt-in, no new default semantics inferred |
| Diagnostics dated results/fixtures/registry/workbench | Local research, mixed evidence quality | KEEP; claims reviewed against current source, dates and logs |
| Root one-shot probes/outputs and redundant wrappers | AI/SESSION ARTIFACT by purpose/checkpoint context; exact authorship UNKNOWN | ARCHIVE; preserve bytes, eliminate misleading supported entry points |
| Dependencies/Detours | Local dependency, not emulator upstream | KEEP; hook build depends on it; bundled runtime output remains ignored |
| Tools/Hero and Tools/tor_tools/Hero | Both UPSTREAM, different copies | KEEP; tor_tools has explicit project references; no speculative consolidation |
| AssetOriginals/Assets2012/Assets2012April/nexusclient | Local prepared client/assets; nexusclient.rar is UPSTREAM | KEEP locally; not a reproducible source build, no asset deletion |
| _JPEXTRACT and Diagnostics/Scripts2012/DecodedScripts2012 | Later reference/extracted research data | INVESTIGATE; some tracked, purpose/reproducibility/publication status not resolved |
| .vs/obj/caches/symbols/selected latest logs added by fork | Generated/local artifacts | Remove tracking only; retain bytes and existing upstream artifacts |
| .vscode settings, upstream .user/.suo/bin artifacts | Machine-specific / UPSTREAM historical artifacts | INVESTIGATE; preserve rather than normalize unrelated originals |

The inventory records existence/origin of paths, not whether every inherited
path still has original bytes. Significant current differences are reviewed in
architecture.md and the upstream diff lists. No unsupported claim of exact AI
authorship or line-by-line correctness is made.

## 6. Current important tree

```text
README.md / AGENTS.md / START-HERE.md / LICENSE
!emulator_clean_plan.txt
docs/                  architecture, project-state, research-workflow, this report
scripts/               Build-Server, Start-Servers, Collect-Logs
SharpServer/           active C# runtime, NET, TOR, AreaServer, shard-list
  bin/Debug/AreaServer required inherited capture fixtures
Server/                original C++ Framework, Proxy/World/Time/Script/PluginNet
Client/                original client projects and locally modified Hook
Tools/                 Hero, PacketAnalyser, SCPTExtractor, tor_tools and others
Packets/ / Parser/ / Hacks/  original protocol/capture/reference projects
Diagnostics/           checkpoint, registry, workbench, tests, dated evidence
  RepositoryCleanup-20261004/ inventory, progress, manifests, validation
Archive/RepositoryCleanup-20261004/ retired root probes and prior documents
Dependencies/          local Detours/runtime prerequisites
Assets2012April/ etc.   prepared local assets (ignored; some old tracked extracts remain)
_JPEXTRACT/             retained later reference data
RuntimeLogs/           ignored immutable log copies and server console sessions
```

Initial filesystem: 13,712 files; 5,157 indexed paths; 2,097 upstream paths.
Initial Diagnostics was about 67.95 GB, April assets about 18.41 GB; broad
recursive cleanup would be unsafe. After untracking: 4,447 indexed paths.
`inventory-{before,after}.csv` and `tree-summary-*` cover the whole tree except
Git internals, including ignored assets/builds. Later audit outputs add files.

## 7–8. Capabilities, dependencies and bypasses

The full concise map is in [project-state.md](project-state.md), including all
six requested status labels. The dominant dependency is:
character ownership/state → correct player encoding/readiness → transactional
world/area lifecycle → phase/actor/effect ownership → interactions/story/combat
and travel. Transport framing success alone does not resolve the next layers.

Preserved bypasses include captured snapshot replay, byte-scanned remap, fixed
spawn/instance, reordered phase creation, Safe Login suppression, forced
mobility/loaded state, client loading confirmation patch, moving tether,
captured retreat membership and phase-exit effect replacement. Their scope and
downstream risks are listed in project-state.md. No causal hypothesis was
promoted to fact and no new protocol behavior was installed.

## 9. Logging / runnable workflow and validation

Supported workflow: build both existing components with Build-Server; check
and launch servers only with Start-Servers; snapshot existing logger outputs
with Collect-Logs into RuntimeLogs. Existing in-process Log is retained, not
replaced. Historical client experiments remain separate and use exact pins.

Validation performed:

- Isolated **current-source** NexusToRServer and ShardListServer builds succeeded
  using VS MSBuild, Debug/x86; existing compiler warnings remain.
- AreaRouting, AreaBlobFraming (38 cases), AreaWireRoundTrip (54 cases) and
  PacketWorkbench passed before and after cleanup, with the fresh assembly
  explicitly selected for the final serializer checks.
- WorldEntryOffline fails before and after at the missing RequestWorldFadeIn
  gate observer assertion. It was not weakened to manufacture a pass.
- Three workflow scripts parse; Start-Servers -CheckOnly succeeds. Actual new
  startup is intentionally unexercised; no server/client processes launched.
- Collect-Logs was run; eight copies' SHA256 hashes verified.
- All 553 existing hashed runtime sources, fixtures, selected binaries and Run-*
  inputs are byte-identical to the initial snapshot.
- Project item scan: one missing C++ header `Server/WorldServer/Src/DataBase/otlv4.h`,
  also absent from cached upstream. Historical C++ build remains unverified.
- Pin audit: RetreatGateway 60/63, Taxi 95/95, WellerStory 77/91 match. Exact
  mismatches are in launcher-pins.csv; no manifests were regenerated. Taxi input
  identity is not native acceptance. Retreat/Weller launchers cannot pass their
  old preflight against today's inputs.

## 10. Manual review / intentional retention

- Fix the stale WorldEntryOffline observer assertion only after recovering its
  intended source/history contract; keep current failing result visible.
- Do not overwrite historical launcher pins. Establish a newly identified
  control run separately after review, preserving current payload transformations.
- Original DB credential literal, self-signed certificate passphrase, inherited
  platform.p12 and captured login material need credential/privacy review before
  publishing/deployment. Locations are recorded without values; constants are
  not evidence of working authentication. No credentials were rotated or removed.
  Literal scan is limited and includes vendored API false positives; it is not
  an exhaustive secret scanner. Capture binaries may contain sensitive material.
- Required fixture blobs remain under bin; moving them needs coordinated loader,
  test and experiment-pin changes. Upstream-generated clutter is deliberately
  retained pending provenance-aware review, not globally swept away.
- Large tracked script/extract/reference trees, old injected trace programs,
  modern/local resource cache assumptions and machine paths need targeted review.
  Some generic trace scripts contain overconfident historical comments; pinned
  bytes remain unchanged and maintained docs qualify those claims.
- Legacy C++ dependencies and missing otlv4 header; original license/README/file
  notice differences; no legal determination, historical source rewrite or
  dependency installation was made.
- No account/character persistence, general NPC initialization, authoritative
  simulation or general room/phase engine is inferred from rendered scenery.
- No commit/push, history cleanup, branch reset, external tree modification or
  game/research asset deletion. Preexisting dirty runtime work stays intact.

## 11. Top three investigations

1. April schema26 player-update encoding and loading readiness contract.
2. Selected-character/area/instance ownership, normal confirmation, transactional
   entry completion and per-area reset boundaries.
3. Separate phase/actor/effect lifecycle; captured medcenter targetability as
   interaction control before more synthesized actors.

See project-state.md for the downstream dependencies each investigation unlocks.

## 12. Recommended Phase 2 prompt

> Read the cleanup report, maintained architecture/state/workflow, CURRENT-PICKUP
> and evidence registry. Design and implement a minimal isolated read-only
> research layer joining version-identified April 2012 client/Jedipedia GOM,
> scriptdef/nodes, native client derivations, upstream emulator source, current
> source and preserved runtime logs. Begin with a source/identity catalog and
> citations by commit, native address, fixture offset and run timestamp. Support
> one bounded question: schema26 mobility/loaded/stat-map encoding and its
> readiness contract. Keep capture, client-derived, behavior and hypothesis
> evidence distinct. Use existing packet/content tools; do not change gameplay,
> runtime startup or historical pins, launch the game, or implement taxi. Define
> privacy boundaries and reproducible read-only access before exposing an MCP
> interface. Preserve uncertainty and return a reviewable first slice rather
> than a broad autonomous feature-development system.

This prompt is a recommendation only. Stop here and await review.
