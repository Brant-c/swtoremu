# Verified CRT3-on log-only run

The user requested configuration verification and server/client logs instead
of full-memory observer scans. Launch.ps1 now explicitly sets CRT3=1, disables
phase-instance retry and enables the log-only profile. It starts no external
memory observer. The same desktop wrapper remains
`Run-SWTORClassic-PhaseLifecycle.cmd`; CRT3-off must not be used yet.

`Launch.ps1 -VerifyOnly` passed without starting processes. The actual batch
configuration reported CRT3=1, empty retry, lifecycle=1, log-only=1, full CRT
hex=0. All pinned inputs agree. No client/server was running at verification.
The baseline still requires live proof that CRT3 was emitted and that the named
hooks installed before requesting movement; old console files are not proof.

Full CRT dumps, RPC, loading-screen and player-field traces are disabled in this
profile. Event-dispatch tracing remains enabled because the current hook
initializes its CRT-apply observer under that gate. This retained instrumentation
was already proven to install the named methods in the preceding live run.
The server now logs the exact doorway destroy payload in log-only mode even
when general area payload tracing is disabled; that packet is 46 bytes, so
preserving the decisive bytes does not require dumping startup fixtures.
This edit affects logging only, not packet construction or ordering.

Debug x86 server build into the real launch path passed with existing warnings.
AreaRouting, AreaBlobFraming (38 bodies) and AreaWireRoundTrip (54 packets) passed.
The new server SHA-256 is
`1931A175025884E2E790363F7EEACEA096FAB3B8C9D41E3C273F426DE706A356`.
Metadata still contains `CRT18 suppressed` and not `emitted room-load stream`.
The hook remains the previously tested
`258C834F1A524F039CF96D74EBDED5650A9AA3FE1166759C808CE961AE1A3D36` build.
Identity.csv pins the new logging source/binary and launch configuration.
Protocol registry unchanged; prior WorldEntryOffline failure is not resolved
by these changes.

The preceding 14:21 launch independently installed all four named hooks at
14:24:39, but its server explicitly suppressed CRT3 at 14:24:40. A separately
attached read-only observer found the gnarls control, phase-info child and
parent instance HeroNodes; no player-phase-data HeroNode was found. That
explains its rejected baseline. No doorway attempt was requested. Partial
observer evidence remains in `live-20260930-142624-436/`; its original manifest
creation failed and the error is preserved. Server/hook logs are preserved in
`../DoorwayControl-20260930/phase-lifecycle-crt3-off-no-crossing-20260930-143535-058/`.

Reduced question: does the exact doorway destroy bracket named phase-info
destroy entry/return and a gateway update nested inside it? The server log
proves accepted movement and sending; the client hook log proves execution.
No lookup/global-state read-back, HeroNode removal or room residency claim can
be made from those logs alone. Operator-observed wall/movement remains separate.
This narrowed scope supersedes the external-observer READY gate for this run
at the user's explicit request. All packet-policy and CRT18/retry gates remain.
