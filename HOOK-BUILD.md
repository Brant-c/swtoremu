# Local client hook build

Detours 4.0.1 is checked out under Dependencies/Detours at commit e4bfd6b03e50de46b47abfbd1e46b384f0c5f833.
Run build-hook.cmd from the repository root to build the x86 static Detours library and Release MemoryMan.dll with Visual Studio 2026 Community. Run test-hook.cmd to check attach, trampoline calls, and detach in an isolated test process.

Output: Client/Hook/Bin/x86/MemoryMan.dll.
The hook and Detours use the static release runtime (/MT). The hook no longer imports MSVCR100D.dll or MSVCP100D.dll. Original memory-manager exports still forward to Nexus.dll, which must remain beside the client.

The six legacy DetourFunction calls now use a checked transaction. A missing SSL signature prevents hook installation instead of attempting to hook address zero. The capture timestamp conversion checks the signed 32-bit range.

Validation: Release/Win32 build passed; synthetic x86 attach/original-call/detach test passed; 16 forwarded exports checked; installed DLL hash matches build output. Full client startup and game compatibility have NOT been verified. This fixes the debug runtime dependency, not missing game assets or platform services.

The replaced extracted-client DLL is preserved beside MemoryMan.dll as MemoryMan.dll.before-detours4-<timestamp>.bak. No retail installation files were changed.
