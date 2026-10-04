# client.gom compatibility probe

## Live run status

The compatibility launcher now prints a status block every five seconds. It reports process memory, CPU time accumulated during the interval, visible-window state, TCP connection state, and the last requested and supplied resource. It identifies quiet asset tracing after 30 seconds and reserves `POSSIBLY STUCK` for two minutes without a different tracked resource. `Run-SWTORClassic-With-Status.cmd` opens this output in a persistent terminal.

One full run remained quiet on `scriptdef.list` for more than 53 seconds, then completed all 997 bridged reads, supplied the area and fallback texture files, and logged `Active area load complete`. This proves that a short absence of resource requests does not mean the client is stuck. The run limit is now ten minutes to leave time for the engine initialization that follows.

The original local launch command set `platform` to `127.0.0.1:443`, but the bundled TLS `ShardListServer` listens on 8888. Its `Shards.xml` also advertised the author's old `192.168.1.11:8995` endpoint. The service is now built for .NET Framework 4.8, uses an available Windows crypto provider, and returns shards at `127.0.0.1:7979`. A direct TLS test returned a valid five-shard JSON document.

`swtor_dual.icb` constructs `shardaddress` from `server`, `port`, and `instance`, but the old `go1.bat` omitted all three and client logs consequently showed `shardaddress: @::`. The launch command now supplies `127.0.0.1`, `7979`, and instance `1` so the client has a concrete local login destination even before shard selection succeeds.

The first direct login exposed a dormant server defect: `LoginServer/Router.cs` decrypted only the first 256-byte RSA block even though the login token and Salsa session keys span multiple blocks. The remaining block code had been commented out. The handler now validates and decrypts every 256-byte block. A live client then completed login, received `127.0.0.1:20060`, authenticated to the shard server, connected to the time server on 20066, and exchanged five-second ping packets. This is the first confirmed end-to-end client/server connection in the compatibility run.

A 50-second validation run reached bucket 633. Asset counts and memory continued to rise throughout the run, so the monitor correctly classified that interval as active loading and showed that the client had not yet contacted the server.

Tested 2026-09-10 against the retail swtor_main_global_1.tor currently installed on this machine.

The archive contains filename hash 6107069DB7C70D58 for /resources/systemgenerated/client.gom. Its method-1 payload is Zstandard rather than the zlib expected by the original Repository.cs. Decoding yields exactly 921724 bytes.

Built the original Tools/tor_tools/Hero/Hero sources with the bundled Tools/Hero/SharpZipLib source, without changing either. The original definition constructors and GOM.ParseDefinition accepted every record:

- 13153 records accepted; zero ignored; zero failures.
- 12 associations, 2221 classes, 752 enumerations, 10014 fields, 154 nodes.
- DBLB version 2.

An isolated one-resource uncompressed TOR fixture also passes the original Repository.AddFile/GetFile filename-hash lookup and byte-for-byte payload comparison. Its archive version is preserved from the retail header. This fixture is for the tool test only, not a complete client asset archive; do not replace a game archive with it.

Run Run-Probe.ps1 to reproduce extraction, build, and checks. Outputs stay in this directory. Retail files, original tool source, and client settings were not modified.

## What this establishes

The current client.gom can be extracted and parsed with the historical tools after handling outer Zstandard compression. It is not necessary to reconstruct an old client.gom merely to use those tools. The current client configuration points to the retail Assets folder; older conversion notes are stale for that setting.

## What remains unverified

The 2012 game executable has not been shown to accept this archive or data. Its mounting rules, archive version/metadata checks, resource prefix handling, internal definition semantics, and other required assets can differ from the permissive tool reader. Prior runtime diagnostics identified a resource-lookup failure. A controlled runtime archive-mount/lookup trace remains necessary before choosing a client compatibility fix. This test does not establish complete game compatibility or server gameplay support.

## Runtime follow-up: concrete read and definition failures

The runtime tests below supersede the earlier uncertainty about whether the retail client.gom is found. Tests ran outside the sandbox because the sandbox produces a separate platform-init failure.

### Normal retail configuration

TraceReads.exe uses rearmed, temporary process breakpoints to distinguish successive resource requests by name. For /systemgenerated/client.gom:

- Metadata lookup returns EAX=0 at RVA 0x742556 (success).
- The content read at RVA 0x742624 requests 0xE107C (921724) bytes.
- The read returns EAX=4 at RVA 0x742629 (failure).
- Local content is therefore unavailable, and the fallback at RVA 0x741CB0 returns 0xFACE0004 unconditionally. The request cleanup reports 0xFACE000F, which produces the misleading final resource-not-found message.

The normal retail trace also shows failed reads of /global.dep and loading-screen resources. The fallback stub is not itself proof of a bad startup configuration: it is selected after local content cannot be supplied. This run rules out missing client.gom archive membership or a resource-prefix mismatch as the initial failure for that file. The precise low-level reader error is not decoded; the independently confirmed Zstandard/zlib mismatch remains a strong explanation, rather than a captured decompressor error.

Evidence: ../trace-reads-retail.txt, ../TraceReads.cpp, ../trace-lookup-retail.txt.

### Partial archive experiment

prepare-runtime-test.py copies only swtor_main_global_1.tor and appends a zlib-compressed client.gom, preserving its uncompressed bytes, metadata, original checksum and archive version. Test-Runtime.ps1 temporarily selects this partial directory and restores the original configuration in finally, verifying the backup hash. The partial setup failed at metadata lookup, before reading client.gom. It is inconclusive as a compression test and should not be used as a working asset setup.

Evidence: runtime-test.json, trace-runtime-zlib.txt.

### Isolated decoded-GOM runtime experiment

TraceGomOverride.exe retains the retail configuration. Only when the named request is exactly /systemgenerated/client.gom and the requested length matches the verified decoded payload does it supply those bytes to the existing destination buffer and simulate a successful return from the read call. This intervention affects only the diagnostic process. It does not modify the client executable or any retail archive on disk and is not a permanent fix.

The original content-read failure is passed. The executable then throws an unhandled omega::OString exception while processing GOM definitions:

    cannot construct an invalid type

The stack includes RVAs 0xA282C, 0xA28A2, 0x5739D5, 0xA6789, 0xAAA99, 0xA9E2F and the GOM callback at 0x42D2BB. Child exit code is 0xE06D7363. A second run captured the same exception and message.

Evidence: trace-gom-override.txt, trace-gom-exception.txt, ../TraceGomOverride.cpp, ../build-gom-override.cmd.

### Conclusion and next decision

The modern GOM passing the standalone historical tool parser does not imply that the April 2012 executable accepts its type definitions. This controlled runtime test exposes a second compatibility problem beyond the failed outer resource read. Bulk recompression is therefore not an established fix. The next practical path is a coherent historical client/asset set close to the executable's build, or a separate substantial investigation into the exact rejected definition and executable type encoding. Do not patch out the type exception or claim a playable emulator.

All launched diagnostic processes exited. The original client_defaults.ini was restored byte-for-byte and verified against client_defaults.runtime-backup.ini (SHA256 CC65AF3FFF664BCD90BE474521D5023D3DE90EF018042F64A9D73B65E5DB91F6). Retail assets were unchanged.

## Definition-level investigation and isolation test

TraceDefinition.cpp captures the input to the runtime field-type reader at RVA 0x573950 and the invalid-type branch at RVA 0xA2814. The failing record captured from process memory exactly matches the source GOM record:

- Field ID: 4611686316368904000.
- Name: empty in this asset; no name was inferred.
- Source file offset: 579400; record length: 39 bytes.
- Type descriptor: `08 01 18 03 01 02 02`.
- Outer type: lookup list (8), keyed by ID (1).
- Nested value type: 24 (0x18), rejected by the executable's `cmp al,17h` / unsigned-below check. Types 23 and above take the invalid-type exception path.
- Direct owning class ID: 4611690223225570000; its name is also empty.

audit-types.py recursively audits field descriptors using the legacy container/reference shapes and rejects unknown types and unconsumed bytes. Of 10014 fields, exactly one fails this audit; one class directly references it. Results are in type-audit.json. This is a structural type audit, not proof that all other definitions have valid runtime semantics.

The prior standalone parser pass was overly permissive: HeroType's default switch branch accepts an unknown enum value without rejecting it, and does not require all descriptor bytes to be consumed. Therefore the earlier zero-error count must not be interpreted as full compatibility.

### Diagnostic exclusion, not a conversion

prepare-field-isolation.py creates client-field-isolation.gom by removing that single field record and removing its ID from the owning class's field list. All other records are preserved, except the class count/list and necessary GOM alignment. File size becomes 921684 bytes. It does not assign guessed semantics to type 24. The original decoded GOM is retained unchanged.

TraceFieldIsolation.cpp supplies this diagnostic copy only to the launched process and adjusts that read's buffer length to the smaller payload. Retail archives, client executable, and client settings are not changed. It does not suppress the invalid-type exception handler.

Two runs progressed beyond the former invalid-type crash and requested /systemgenerated/buckets.info and /systemgenerated/scriptdef.list. The confirmation trace also records two first-chance G::DefinitionNotFoundException events; their requested IDs are not yet captured, so they must not be attributed to the omitted field without evidence. This is progress past the original blocker, not complete GOM/gameplay validation. The timed diagnostic does not demonstrate login or world entry.

Evidence: trace-definition.txt, last-runtime-field.bin, type-audit.json, field-isolation.json, trace-field-isolation.txt, trace-field-isolation-confirm.txt. The first run reached the 45-second timeout. The confirmation tracer explicitly clears its own single-step flag after rearming probes; additional client-generated single-step events still appear.

Next investigation: identify the missing-definition IDs and handle the next resource reads. Type 24's full semantics remain unknown; do not promote field omission to a production compatibility fix, since scripts, prototypes or network data can require that field. The small number of unsupported field descriptors makes a targeted compatibility effort more plausible than the initial exception alone suggested.

## Resource bridge and world-load progress

`prepare-resource-cache.py` now extracts and decodes only observed startup resources into the workspace. The current cache contains 525 resources (200,426,324 bytes); `/engine/white.tex` is the sole requested name absent from the retail archives. Retail archives remain unchanged.

`analyze-missing-definitions.py` classified the verbose trace: 787 first-chance definition exceptions contain 786 unique names. Of these, 785 are numeric script/object references. None is a GOM definition ID in the core file or 358,651 bucket records, and none occurs in the historical name map. The client catches these probes and continues. `CharacterMoveState` is the only nonnumeric name and appears twice. Results are in `missing-definition-analysis.json`.

The quiet `CompatibilityLauncher.exe` reproduces the timing behavior required by the legacy two-process Nexus hook, supplies verified decoded cache files in process memory, and leaves the on-disk client and archives unchanged. A controlled run completed the bucket set and `scriptdef.list`, then requested and supplied `/world/livecontent/systemgenerated/3758002374/area.dat`. Both processes remained responsive and no second-chance exception was observed, but the main process then stayed CPU-bound for more than two minutes parsing the 92,190-byte modern area file. It created no game window and made no server connection. The area begins with `AREA_DAT_BINARY_FORMAT_` and carries modern format data that is not established as compatible with the April 2012 loader.

`Run-SWTORClassic.cmd` is therefore bounded to a five-minute compatibility test. It reports progress and cannot consume a CPU core indefinitely. `SharpServer/NET/TORGamePacketHandler.cs` still explicitly leaves in-game packets unimplemented. The area wait was investigated further below rather than being treated as the final boundary.

## Targeted area bypass

A sampled hot thread identified RVA `0x7937AB` inside the area-settings reader. Its surrounding constants are `[ROOMS]`, `[SETTINGS]`, `AreaBlur`, `SkyDome`, `DemoStartPoint`, `WindStrength`, and related environment settings. The routine repeatedly calls the tokenizer at RVA `0x50C510`; a false result jumps back to the wait loop. Its normal completion path begins at RVA `0x7943DE`.

`CompatibilityLauncher.exe` now uses a process-only breakpoint to redirect the first post-area false-token wait to that existing completion path. This does not patch the executable on disk. The client survived the bypass and advanced from `area.dat` to `/art/defaultassets/missing_material_d.tex`. After the decoded 378-byte XML texture descriptor was supplied, it advanced again to `/art/defaultassets/missing_material_d.dds`. The 11,064-byte DDS companion is now extracted and included in the bridge allowlist for the next run.

This demonstrates a possible route using the available files: bypass optional incompatible login-scene setup and supply narrowly verified decoded resources as they are requested. It does not yet establish a visible login screen, and full gameplay would still require both wider asset compatibility and substantial server implementation.
