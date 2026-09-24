# SWTORClassic compatibility test

Double-click `Run-SWTORClassic-With-Status.cmd` to start the local server and run the April 2012 client through the compatibility bridge for up to ten minutes. It opens a separate live-status terminal and leaves it open so the final state remains readable.

Keep the bridge window open during the test. It prints meaningful connection and initialization milestones, progress every 25 resources, and any client error. Repeating live status checks and automatic quiet-time thread dumps are disabled so the useful events remain readable.

The bridge reads decoded copies from `Diagnostics/GomCompatibility/ResourceCache`. It does not change the retail SWTOR installation. The client executable and retail TOR archives remain untouched.

This is a diagnostic path, not yet a playable startup path. It passes the original Zstandard read failure, the incompatible GOM field, all 997 definition buckets, and `scriptdef.list`. The bridge also bypasses the incompatible optional area-settings wait and supplies the fallback texture descriptor and its DDS image. This incremental path may reach the login UI without a complete historical asset set, but each newly reached resource must still be verified against the April 2012 client.

The emulator server also contains an explicit unimplemented in-game packet handler, so quests, combat, movement, and full world play remain unavailable.

The launcher also starts the bundled .NET 4.8 shard-list service on port 8888. The client receives a direct local login address, and the repaired login handler decrypts all RSA handshake blocks. A validated run authenticated to the shard server on port 20060 and maintained the time-server connection on port 20066 while asset loading continued.
