# Doorway room-state rerun

This reruns the frozen experiment-01 control and adds only an external,
read-only native-state timeline. Keep the client and both servers closed before
launching.

Run from a fresh PowerShell process with no inherited `SWTOR_*` variables:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\SWTORClassic\swtoremu\Diagnostics\DoorwayControl-20260930\room-state-rerun\Launch.ps1"
```

After the client reaches Tython, do not use abilities. Walk once toward and
through the green Masters' Retreat doorway, keep walking against or beyond the
boundary for several seconds, then stop and leave the client open. Record
whether a loading screen appeared, whether area/minimap text changed, whether
the exterior rendered, and whether collision allowed continued movement.

`Launch.ps1` validates `identity.csv`, preserves prior logs before rotation,
starts `Watch-RoomState.ps1`, and launches the unchanged frozen control. The
observer writes `timeline.csv` and its console files in this directory. These
outputs are single-use: the launcher refuses to overwrite or relaunch them.
