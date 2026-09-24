# Startup investigation

The C7 error reproduced only inside the restricted diagnostic environment. The client's internal system check reported "Unable to initialize platform object." Outside that environment the platform check passed and the game window opened.

Controlled unrestricted comparisons:
- Rebuilt hook, original asset setting: parent and renderer exited with code 0 after roughly 11 seconds.
- Rebuilt hook, temporary retail asset path: same exit behavior. Original configuration restored.
- Original memory manager (no hook), original asset setting: same code-0 exit behavior. Rebuilt hook restored and SHA256 verified.

The first-chance Boost bad_alloc exceptions occur in static exception initialization and are handled. They do not establish memory exhaustion. No unhandled exception was observed in the unrestricted comparisons.

The exit cause remains unconfirmed. Do not patch out C7 or claim the hook/asset absence caused the shutdown. The debugger needs unrestricted access for valid Windows platform-check results. Existing trace tools modify only process memory for temporary diagnostic breakpoints, not the client executable on disk.

All retail files were left unchanged. The workspace client configuration and rebuilt MemoryMan.dll are restored. Next diagnostic should capture the normal shutdown call path or file/API failures, rather than investigating the sandbox-only C7 error.

## Full retail asset test (2026-09-10 17:10)
The workspace client_defaults.ini now points BaseResourceFileName to the user's retail Assets directory. Retail files were not modified. Prior configuration is saved in Diagnostics/client_defaults.before-assets.ini.
Process Monitor confirmed successful CreateFile calls for all 101 requested .tor archives, with no missing .tor paths. The client still shut down, parent exit code 0 after approximately 27 seconds. No TCP/UDP events for swtor-emu.exe were present in the 25-second trace; that capture ended shortly before the process exit. Successful file reads do not establish asset format/content compatibility with the 2012 executable.
Two earlier test copies remain under workspace Assets (~277 MB), but the current configuration uses the retail folder. Evidence: Diagnostics/Captures/full-assets-client.csv and capture folder 20260910-171007-154.
The missing archive path issue is resolved. The remaining shutdown needs a call-path or resource-decoding investigation; server failure is not established by this trace.

## C5 asset compatibility finding
User reports C5: failed to load game assets. The three payloads read near startup shutdown were located by exact offsets in the archive index. All three have Zstandard frame magic 28 B5 2F FD. zlib rejects each with an incorrect-header error; Zstandard decodes each to exactly its indexed uncompressed size (921724, 7942052, and 144 bytes). The archived file index still labels these compression method 1. The legacy source Tools/tor_tools/Hero/Hero/Repository.cs GetFile handles method 1 with a zlib Inflater, as does TorArchive/File.cs.
This establishes an asset compression incompatibility with the legacy repository reader and a strong explanation for C5. It does not yet capture the executable's failing decompression call or prove compression is the only content compatibility problem. The debugger run did not capture C5 dialog text.
Evidence and repeatable read-only test: Diagnostics/Inspect-Assets.py, Diagnostics/asset-compression-results.txt. Decoder installed locally at Diagnostics/python-deps. No retail assets changed or extracted to disk.
Next recommended experiment: convert a separate small local test archive from Zstandard to zlib with validated indexing/checksums, or instrument the client decoder. Do not overwrite retail archives or assume recompression resolves modern game-data differences. Matching historical assets are the alternative if legitimately available.

## Direct error trace (converted partial set)
TraceError.exe captured the client's error-report routine (RVA 0x76800) with argument 5 and caller RVA 0x73A93. Disassembly shows this branch is selected by the literal UTF-16 command FAILEDASSETLOAD; DISCONNECTED is a separate branch reporting code 4. Thus this run's C5 is an explicit asset-load failure, not the disconnection branch. The exact resource or decoding failure remains unknown. Both child and parent exited with status 0 afterward.
Evidence: trace-converted-error.txt; TraceError.cpp/build-error-trace.cmd; Read-ErrorStrings.py. The debugger uses one-use, per-process breakpoints restored before continuation. No client executable on disk was patched. Conversion remains suspended at PID 26876, with 43 complete archives.

## Loader origin and resource (partial converted set)
TraceState captured previousState=2 at RVA 0x3AD957, identifying the GOM initialization callback failure flag. TraceResource captured callback status 0xFACE000F at RVA 0x42D371 and resource /systemgenerated/client.gom. Static code explicitly logs Resource '%s' wasn't found for that status.
The converted main_global archive does contain the repository hash for /resources/systemgenerated/client.gom (6107069DB7C70D58); its zlib payload decodes to the indexed 921724 bytes. Thus the resource exists in the converted file but the client repository lookup cannot resolve it in this partial setup. The /resources prefix is used by repository tools; whether the runtime adds it must be investigated rather than assuming a rename is sufficient.
Next investigation: client archive mounting/index/metadata lookup, including the incomplete archive set and preserved modern archive metadata. Do not assume converting more payloads alone fixes this failure. Conversion stays suspended.
