# Weller startup result

User reports cinematic and subsequent conversation played successfully, but final face/camera stayed in conversation. Server start marker01:25:13 created instance1AC7000001 then controller1AC7000002. Subsequent choices E44A53FB carry typed controller ID plus integer dialogue node. Final one-ID request70C14D2A at01:27:28 and later14CDD239 at01:27:37 both target this controller; both swallowed. Full logs and hashes preserved in prelaunch-20261001-012911-086.

Startup is Behavior-verified. Camera/input cleanup was missing, as explicitly pending in experiment02. No quest progress claim. Experiment03 adds ordered active-controller/instance teardown with separate opt-in, using existing recovered destroy callback semantics. Exact finish-vs-escape public name mapping remains unresolved; both requests can safely release only the current owned conversation and cannot commit quest changes.
