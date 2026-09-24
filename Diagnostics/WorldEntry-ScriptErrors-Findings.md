# 2026-09-20 (third session) — SMSG_RESULTS works; duplicate init caused the crash

## Breakthrough: the client now runs its scripts

With `SWTOR_RPC_REPLY_MODE=mirror` the client answered every `CMsgF96DCDB0` RPC
request with `SMSG_RESULTS (0xD5280283)`, and the client **immediately ran its
area-entry scripts** — for the first time in this project it sent
`SendScriptError` packets:

```
SendScriptError: Client script error: msg=[Character already exists: 115000043427]
  Call trace: Script 14988232461720378822 line 329 me[id=115000043427 class=...]
  starting method/function FN_2745700068
  Call trace: Script 14988068873268833607 line 13 me[id=115000043427 ...]
  starting method/function FN_705007523
```

(Six such errors, different character ids: 115000043427, 115000039403,
115000046732, 115000047014, 115000031327, 115007216749.)

So the unanswered RPC really was the gate that kept the script layer idle all
along. Answered RPCs -> scripts execute -> the world-entry sequence advances.

## Why it then crashed (my bug, not a protocol problem)

`SWTOR_RE_SEND_INIT=1` was set for that run, so the init burst went out twice:

```
AREA-PAYLOAD type=AreaClientReplicationTransaction ... stream-id occurrences:
[('12',2), ('13',2), ('14',2), ('15',2), ('17',2), ..., ('2D',2)]   # CRT1..CRT17 x2
```

Source of the two copies:
1. `AreaStartupBundle.Send` on the first `AreaModulesList` (CRT1..CRT17,
   awareness, hack pack, RPCs, signals), and
2. `SendInWorldInit` on `CMsgC586BD22` (forced by `SWTOR_RE_SEND_INIT=1`).

Applying the same initial-replication set twice makes the client re-create node
GOMs, which the entry scripts then find already present ->
`Character already exists` -> the script engine throws `HeroScriptError`, a
`SerializationException` is thrown inside the CRT handler (client RVA
`0x24F143`, i.e. the `0x24F0B4` CRT parse), and the client finally dies with an
access violation at client RVA `0x003F5AE6` (eax=0, ecx=0 — null deref).
Dumps: `Diagnostics/world-entry-20260920-164020-72260-first.dmp`,
`Diagnostics/world-entry-20260920-164022-72260-unhandled.dmp`.

Conclusion: the re-send switch is a diagnostic-only tool and must stay **0**.
The `AreaStartupBundle` alone is the correct single delivery.

## Current switch state (Run-SWTORClassic-Trace-Tython.cmd)

```
SWTOR_TRACE_AREA_PAYLOADS=1
SWTOR_CRT_MISSING_MODE=skip
SWTOR_AREA_ENTER_MODE=both
SWTOR_AREA_ENTER_TRIGGER=sync
SWTOR_RE_SEND_INIT=0            <-- fixed: no duplicate init
SWTOR_RPC_REPLY_MODE=mirror     <-- the breakthrough; answers the client's RPCs
SWTOR_RPC_RESULT_A=true
SWTOR_RPC_RESULT_B=true
```

## Next run

Kill the servers (env is snapshotted at start), launch the trace cmd, select the
Tython character, and let it sit ~60 s. Expect:

1. `RpcReply: CMsgF96DCDB0: SMSG_RESULTS (mirror) sent ...` replies, and
2. **no** duplicate CRT burst (each stream id should appear exactly once in the
   `AREA-PAYLOAD type=AreaClientReplicationTransaction` lines), and
3. no `Character already exists` script errors.

Watch for: the loading screen dropping, any remaining `SendScriptError` text
(now genuinely diagnostic — the client names the failing script/function), or a
new crash (if so, the trace/stack identifies the next gap).
