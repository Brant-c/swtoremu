#include <winsock2.h>
#include <windows.h>
#include <iphlpapi.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <dbghelp.h>
#include <stdio.h>
#include <fstream>
#include <iterator>
#include <map>
#include <string>
#include <vector>

static void captureWorldEntryException(HANDLE process, const DEBUG_EVENT &event,
                                       const CONTEXT &context) {
    // Limit capture to one first-chance and one unhandled exception per process.
    static std::map<DWORD, unsigned> captured;
    const unsigned phase = event.u.Exception.dwFirstChance ? 1u : 2u;
    if (captured[event.dwProcessId] & phase) return;
    captured[event.dwProcessId] |= phase;

    char path[MAX_PATH] = {};
    DWORD length = GetModuleFileNameA(NULL, path, MAX_PATH);
    if (!length || length >= MAX_PATH) {
        printf("World-entry dump: cannot resolve launcher directory.\n");
        return;
    }
    char *separator = strrchr(path, '\\');
    if (!separator) return;
    SYSTEMTIME now = {};
    GetLocalTime(&now);
    const size_t offset = (size_t)(separator + 1 - path);
    int written = _snprintf_s(path + offset, MAX_PATH - offset, _TRUNCATE,
        "world-entry-%04u%02u%02u-%02u%02u%02u-%lu-%s.dmp",
        now.wYear, now.wMonth, now.wDay, now.wHour, now.wMinute, now.wSecond,
        event.dwProcessId, phase == 1 ? "first" : "unhandled");
    if (written < 0) {
        printf("World-entry dump: path too long.\n");
        return;
    }
    HANDLE file = CreateFileA(path, GENERIC_WRITE, 0, NULL, CREATE_NEW,
                              FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        printf("World-entry dump create failed: error=%lu path=%s\n", GetLastError(), path);
        return;
    }
    CONTEXT savedContext = context;
    EXCEPTION_RECORD record = event.u.Exception.ExceptionRecord;
    EXCEPTION_POINTERS pointers = { &record, &savedContext };
    MINIDUMP_EXCEPTION_INFORMATION exception = {};
    exception.ThreadId = event.dwThreadId;
    exception.ExceptionPointers = &pointers;
    // The exception/context structures are in the debugger, not the client.
    exception.ClientPointers = FALSE;
    // Preserve heap-backed parser buffers as well as the original throw stack.
    MINIDUMP_TYPE flags = (MINIDUMP_TYPE)(MiniDumpWithFullMemory |
        MiniDumpWithFullMemoryInfo | MiniDumpWithThreadInfo |
        MiniDumpWithProcessThreadData | MiniDumpWithUnloadedModules);
    BOOL ok = MiniDumpWriteDump(process, event.dwProcessId, file, flags,
                                &exception, NULL, NULL);
    DWORD error = ok ? ERROR_SUCCESS : GetLastError();
    CloseHandle(file);
    printf("World-entry dump %s: error=%lu path=%s\n",
           ok ? "saved" : "failed", error, path);
    fflush(stdout);
}

// A style-7 Hero reader begins with ten words:
//   [style][w1][w2][w3][w4][w5][cursor][length][capacity][buffer]
// Only that validated shape is reported, so a wrong guess stays silent instead
// of printing unrelated memory. Mirrors Diagnostics/Inspect-WorldEntryReader.py.
static bool reportReader(HANDLE process, DWORD_PTR address) {
    unsigned words[10] = {};
    SIZE_T count = 0;
    if (!address ||
        !ReadProcessMemory(process, (void *)address, words, sizeof(words), &count) ||
        count != sizeof(words))
        return false;
    const DWORD style = words[0], cursor = words[6], length = words[7],
                capacity = words[8], pointer = words[9];
    if (style != 7 || length == 0 || length > capacity || capacity > 1024 * 1024 ||
        cursor > length)
        return false;
    printf("  Reader %08lX style=%lu cursor=%lu length=%lu capacity=%lu remaining=%lu buffer=%08lX\n",
           (DWORD)address, style, cursor, length, capacity, length - cursor, pointer);
    // Cap the dump so an unreasonable 'length' cannot flood the console.
    SIZE_T wanted = length < 512 ? length : 512;
    std::vector<BYTE> data(wanted);
    if (pointer && wanted &&
        ReadProcessMemory(process, (void *)pointer, &data[0], wanted, &count)) {
        printf("  Reader buffer (%u of %lu bytes):", (unsigned)count, length);
        for (size_t i = 0; i < (size_t)count; ++i)
            printf(" %02X", data[i]);
        if (count < length) printf(" ...");
        printf("\n");
    } else {
        printf("  Reader buffer %08lX is not readable\n", pointer);
    }
    fflush(stdout);
    return true;
}

// Walks the crashing thread once and reports the frame list plus, for any frame
// whose arguments are a validated style-7 reader, that reader's exact cursor and
// bytes. This is what identifies the input the client was reading when a run
// dies without a SerializationException (the observed access violations).
static void reportWorldEntryStack(HANDLE process, HANDLE traceThread, CONTEXT &trace) {
    SymSetOptions(SYMOPT_DEFERRED_LOADS | SYMOPT_FAIL_CRITICAL_ERRORS);
    SymInitialize(process, NULL, TRUE);
    STACKFRAME64 frame = {};
    frame.AddrPC.Offset = trace.Eip; frame.AddrPC.Mode = AddrModeFlat;
    frame.AddrFrame.Offset = trace.Ebp; frame.AddrFrame.Mode = AddrModeFlat;
    frame.AddrStack.Offset = trace.Esp; frame.AddrStack.Mode = AddrModeFlat;
    for (int i = 0; i < 22; ++i) {
        if (!StackWalk64(IMAGE_FILE_MACHINE_I386, process, traceThread, &frame, &trace,
                         NULL, SymFunctionTableAccess64, SymGetModuleBase64, NULL))
            break;
        IMAGEHLP_MODULE64 module = {}; module.SizeOfStruct = sizeof(module);
        SymGetModuleInfo64(process, frame.AddrPC.Offset, &module);
        printf("  World-entry stack %s + %08lX\n", module.ModuleName,
               (DWORD)(frame.AddrPC.Offset - module.BaseOfImage));
        // The three-component reader call passes its reader as the first
        // argument; callers repeat it, so checking both is cheap corroboration.
        reportReader(process, (DWORD_PTR)frame.Params[0]);
        if (frame.Params[1] != frame.Params[0])
            reportReader(process, (DWORD_PTR)frame.Params[1]);
    }
    SymCleanup(process);
    fflush(stdout);
}

static ULONGLONG fileTimeValue(const FILETIME &value) {
    ULARGE_INTEGER result = {};
    result.LowPart = value.dwLowDateTime;
    result.HighPart = value.dwHighDateTime;
    return result.QuadPart;
}

struct WindowCheck { DWORD pid; bool found; };

struct WaitingRepositoryCall {
    DWORD threadId;
    CONTEXT caller;
    bool valid;
    bool released;
    WaitingRepositoryCall() : threadId(0), caller(), valid(false), released(false) {}
};

static BOOL CALLBACK findGameWindow(HWND window, LPARAM stateValue) {
    WindowCheck *state = (WindowCheck *)stateValue;
    DWORD pid = 0;
    GetWindowThreadProcessId(window, &pid);
    char title[256] = {};
    GetWindowTextA(window, title, sizeof(title));
    if (pid == state->pid && IsWindowVisible(window) && strncmp(title, "Star Wars", 9) == 0)
        state->found = true;
    return TRUE;
}

static bool hasTcpConnection(DWORD pid) {
    DWORD size = 0;
    GetExtendedTcpTable(NULL, &size, FALSE, AF_INET, TCP_TABLE_OWNER_PID_ALL, 0);
    if (!size) return false;
    std::vector<BYTE> data(size);
    PMIB_TCPTABLE_OWNER_PID table = (PMIB_TCPTABLE_OWNER_PID)&data[0];
    if (GetExtendedTcpTable(table, &size, FALSE, AF_INET, TCP_TABLE_OWNER_PID_ALL, 0) != NO_ERROR)
        return false;
    for (DWORD i = 0; i < table->dwNumEntries; ++i) {
        unsigned short port = ntohs((u_short)table->table[i].dwRemotePort);
        if (table->table[i].dwOwningPid == pid && table->table[i].dwState != MIB_TCP_STATE_LISTEN &&
            (port == 443 || port == 8888 || port == 7979 || port == 20060 || port == 20066))
            return true;
    }
    return false;
}

static void printLiveStatus(const std::map<DWORD, HANDLE> &processes,
                            std::map<DWORD, ULONGLONG> &previousCpu,
                            ULONGLONG elapsedMs, ULONGLONG quietMs,
                            unsigned suppliedCount, const std::string &lastSupplied,
                            const std::string &lastRequested, bool areaWaitBypassed,
                            bool repositoryAttachBypassed, bool compilerAttachBypassed) {
    printf("\n[STATUS %02llu:%02llu] assets=%u  area-bypass=%s  repository-attach=%s  compiler-attach=%s  quiet=%llus\n",
           elapsedMs / 60000, (elapsedMs / 1000) % 60, suppliedCount,
           areaWaitBypassed ? "yes" : "no", repositoryAttachBypassed ? "forced" : "native",
           compilerAttachBypassed ? "forced" : "native",
           quietMs / 1000);
    bool anyConnection = false;
    for (std::map<DWORD, HANDLE>::const_iterator it = processes.begin(); it != processes.end(); ++it) {
        FILETIME created = {}, exited = {}, kernel = {}, user = {};
        PROCESS_MEMORY_COUNTERS memory = {};
        ULONGLONG cpu = 0, cpuDelta = 0;
        if (GetProcessTimes(it->second, &created, &exited, &kernel, &user)) {
            cpu = fileTimeValue(kernel) + fileTimeValue(user);
            if (previousCpu.count(it->first)) cpuDelta = cpu - previousCpu[it->first];
            previousCpu[it->first] = cpu;
        }
        memory.cb = sizeof(memory);
        GetProcessMemoryInfo(it->second, &memory, sizeof(memory));
        WindowCheck window = {it->first, false};
        EnumWindows(findGameWindow, (LPARAM)&window);
        bool connected = hasTcpConnection(it->first);
        anyConnection = anyConnection || connected;
        printf("  client pid=%lu  memory=%llu MB  cpu(last 5s)=%.2fs  window=%s  network=%s\n",
               it->first, (ULONGLONG)memory.WorkingSetSize / (1024 * 1024),
               cpuDelta / 10000000.0, window.found ? "visible" : "none",
               connected ? "connected" : "waiting");
    }
    printf("  last requested: %s\n  last supplied:  %s\n",
           lastRequested.empty() ? "(none yet)" : lastRequested.c_str(),
           lastSupplied.empty() ? "(none yet)" : lastSupplied.c_str());
    if (quietMs >= 120000)
        puts("  No new tracked asset activity; the client processes are still running.");
    else if (quietMs >= 30000)
        puts("  No tracked asset requests yet; the client is waiting before asset initialization.");
    else if (!anyConnection)
        puts("  State: client is still loading and has not contacted the server.");
    else
        puts("  State: client has opened a network connection.");
    fflush(stdout);
}

static std::string readFile(const std::string &path) {
    std::ifstream input(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
}

static bool startRepositoryCallback(HANDLE process, const std::string &data,
                                    const std::string &path, DWORD_PTR callback,
                                    DWORD thisPointer, CONTEXT &context,
                                    BYTE *&allocation, DWORD_PTR &returnAddress) {
    const SIZE_T callbackSize = 0x40;
    const SIZE_T allocationSize = data.size() + path.size() + 1 + callbackSize + 1;
    BYTE *remote = (BYTE *)VirtualAllocEx(process, NULL, allocationSize,
                                          MEM_COMMIT | MEM_RESERVE,
                                          PAGE_EXECUTE_READWRITE);
    if (!remote) return false;
    BYTE *remotePath = remote + data.size();
    BYTE *remoteResult = remotePath + path.size() + 1;
    BYTE *remoteReturn = remoteResult + callbackSize;
    DWORD result[16] = {};
    result[0] = 1;
    result[4] = (DWORD)remote;
    result[6] = (DWORD)data.size();
    result[10] = (DWORD)remotePath;
    SIZE_T wrote = 0;
    BYTE trap = 0xCC;
    bool copied =
        WriteProcessMemory(process, remote, data.data(), data.size(), &wrote) &&
        wrote == data.size() &&
        WriteProcessMemory(process, remotePath, path.c_str(), path.size() + 1, &wrote) &&
        wrote == path.size() + 1 &&
        WriteProcessMemory(process, remoteResult, result, sizeof(result), &wrote) &&
        wrote == sizeof(result) &&
        WriteProcessMemory(process, remoteReturn, &trap, 1, &wrote) && wrote == 1;
    if (!copied) {
        VirtualFreeEx(process, remote, 0, MEM_RELEASE);
        return false;
    }
    DWORD callFrame[2] = {(DWORD)remoteReturn, (DWORD)remoteResult};
    context.Esp -= sizeof(callFrame);
    if (!WriteProcessMemory(process, (void *)context.Esp, callFrame,
                            sizeof(callFrame), &wrote) || wrote != sizeof(callFrame)) {
        VirtualFreeEx(process, remote, 0, MEM_RELEASE);
        return false;
    }
    context.Ecx = thisPointer;
    context.Eip = (DWORD)callback;
    allocation = remote;
    returnAddress = (DWORD_PTR)remoteReturn;
    return true;
}

static bool startScriptDefinitionCallback(HANDLE process, const std::string &data,
                                          const std::string &path, DWORD_PTR callback,
                                          DWORD listener, BYTE *&allocation) {
    const SIZE_T eventSize = 0x2C;
    const SIZE_T thunkSize = 18;
    const SIZE_T allocationSize = data.size() + path.size() + 1 + eventSize + thunkSize;
    BYTE *remote = (BYTE *)VirtualAllocEx(process, NULL, allocationSize,
                                          MEM_COMMIT | MEM_RESERVE,
                                          PAGE_EXECUTE_READWRITE);
    if (!remote) return false;
    BYTE *remotePath = remote + data.size();
    BYTE *remoteEvent = remotePath + path.size() + 1;
    BYTE *remoteThunk = remoteEvent + eventSize;
    DWORD event[11] = {};
    event[0] = 1;
    event[4] = (DWORD)remote;
    event[6] = (DWORD)data.size();
    event[10] = (DWORD)remotePath;
    SIZE_T wrote = 0;
    BYTE thunk[thunkSize] = {
        0x68, 0, 0, 0, 0,             // push event
        0xB9, 0, 0, 0, 0,             // mov ecx, listener
        0xB8, 0, 0, 0, 0,             // mov eax, callback
        0xFF, 0xD0,                    // call eax
        0xC3                           // return from worker thread
    };
    *(DWORD *)&thunk[1] = (DWORD)remoteEvent;
    *(DWORD *)&thunk[6] = listener;
    *(DWORD *)&thunk[11] = (DWORD)callback;
    bool copied =
        WriteProcessMemory(process, remote, data.data(), data.size(), &wrote) &&
        wrote == data.size() &&
        WriteProcessMemory(process, remotePath, path.c_str(), path.size() + 1, &wrote) &&
        wrote == path.size() + 1 &&
        WriteProcessMemory(process, remoteEvent, event, sizeof(event), &wrote) &&
        wrote == sizeof(event) &&
        WriteProcessMemory(process, remoteThunk, thunk, sizeof(thunk), &wrote) &&
        wrote == sizeof(thunk);
    if (!copied) {
        VirtualFreeEx(process, remote, 0, MEM_RELEASE);
        return false;
    }
    HANDLE worker = CreateRemoteThread(process, NULL, 0,
                                       (LPTHREAD_START_ROUTINE)remoteThunk,
                                       NULL, 0, NULL);
    if (!worker) {
        VirtualFreeEx(process, remote, 0, MEM_RELEASE);
        return false;
    }
    CloseHandle(worker);
    allocation = remote;
    return true;
}

static std::string readRemoteWide(HANDLE process, DWORD_PTR address) {
    if (!address) return "(null)";
    wchar_t wide[256] = {};
    SIZE_T got = 0;
    if (!ReadProcessMemory(process, (void *)address, wide, sizeof(wide) - sizeof(wchar_t), &got) || !got)
        return "(unreadable)";
    std::string value;
    for (size_t i = 0; i < sizeof(wide) / sizeof(wide[0]) && wide[i]; ++i)
        value.push_back(wide[i] >= 32 && wide[i] < 127 ? (char)wide[i] : '?');
    return value;
}

static std::string executableDirectory() {
    char path[MAX_PATH] = {};
    GetModuleFileNameA(NULL, path, MAX_PATH);
    std::string value(path);
    size_t slash = value.find_last_of("\\/");
    return slash == std::string::npos ? "." : value.substr(0, slash);
}

// Match generated Hero machine code while ignoring relocated CALL operands.
// A mask byte of zero is a wildcard; nonzero bytes must match exactly.
static DWORD_PTR findRemotePattern(HANDLE process, const BYTE *needle,
                                   const BYTE *mask, SIZE_T needleSize) {
    SYSTEM_INFO system = {};
    GetSystemInfo(&system);
    // All recovered loaded HeroMachine methods in this client build occupy
    // the high private allocation band (RequestWorldFadeIn=EB677750 and
    // Replication_Create=F01F0010 in the reference dump). Limiting the scan
    // prevents multi-gigabyte asset pages from pausing the debugged client.
    DWORD_PTR cursor = 0xE0000000;
    const DWORD_PTR limit = 0xF4000000;
    MEMORY_BASIC_INFORMATION page = {};
    while (cursor < limit && VirtualQueryEx(process, (void *)cursor, &page, sizeof(page))) {
        // The 2011 client predates modern DEP assumptions and HeroMachine's
        // translated x86 may live in committed readable/writable allocations
        // without an executable protection bit. Scan all readable pages; the
        // long masked signatures and post-match opcode checks keep this exact.
        if (page.State == MEM_COMMIT &&
            !(page.Protect & (PAGE_GUARD | PAGE_NOACCESS)) && page.RegionSize >= needleSize) {
            const SIZE_T chunkSize = 1024 * 1024;
            std::vector<BYTE> data;
            for (SIZE_T offset = 0; offset < page.RegionSize; offset += chunkSize) {
                SIZE_T wanted = page.RegionSize - offset;
                if (wanted > chunkSize) wanted = chunkSize;
                data.resize(wanted);
                SIZE_T got = 0;
                if (!ReadProcessMemory(process, (void *)(cursor + offset), &data[0], wanted, &got))
                    continue;
                for (SIZE_T i = 0; i + needleSize <= got; ++i) {
                    bool match = true;
                    for (SIZE_T j = 0; j < needleSize; ++j)
                        if (mask[j] && data[i + j] != needle[j]) { match = false; break; }
                    if (match) return cursor + offset + i;
                }
            }
        }
        DWORD_PTR next = cursor + page.RegionSize;
        if (next <= cursor) break;
        cursor = next;
    }
    return 0;
}

// Compatibility fallback for the loading screen's final phase-confirmation
// decision.  Asset and string-table waits remain untouched.  Once the native
// script calls CheckContinue, route it through its own no-player/conversation
// fallback, which is exactly PhaseNeedsContinue(false) -> FadeIn.  This avoids
// inventing a phase reply when the legacy server has no matching phase RPC.
static bool installLoadingContinueFallback(HANDLE process, DWORD_PTR &methodOut) {
    static const BYTE signature[] = {
        0x53,0x57,0x56,0x83,0xEC,0x38,
        0xC7,0x04,0x24,0xDA,0x01,0x00,0x00,
        0xE8,0,0,0,0,
        0x8D,0x74,0x24,0x30
    };
    static const BYTE mask[] = {
        1,1,1,1,1,1, 1,1,1,1,1,1,1, 1,0,0,0,0, 1,1,1,1
    };
    DWORD_PTR method = findRemotePattern(process, signature, mask, sizeof(signature));
    if (!method) return false;

    // CheckContinue+0x73 is the byte-exact
    //   JE  CheckContinue+0xCE
    // following IsNodeRefValid.  Replace it with an unconditional JMP to the
    // same local PhaseNeedsContinue(false) block.  The sixth byte is padding.
    const BYTE expected[] = {0x0F,0x84,0x55,0x00,0x00,0x00};
    const BYTE replacement[] = {0xE9,0x56,0x00,0x00,0x00,0x90};
    BYTE current[sizeof(expected)] = {};
    SIZE_T got = 0;
    DWORD_PTR site = method + 0x73;
    if (!ReadProcessMemory(process, (void *)site, current, sizeof(current), &got) ||
        got != sizeof(current) || memcmp(current, expected, sizeof(expected)) != 0)
        return false;
    if (!WriteProcessMemory(process, (void *)site, replacement,
                            sizeof(replacement), &got) || got != sizeof(replacement))
        return false;
    FlushInstructionCache(process, (void *)site, sizeof(replacement));
    methodOut = method;
    return true;
}

static BOOL CALLBACK revealGameWindow(HWND window, LPARAM ownerPid) {
    DWORD pid = 0;
    GetWindowThreadProcessId(window, &pid);
    if (pid != (DWORD)ownerPid) return TRUE;
    char title[256] = {};
    GetWindowTextA(window, title, sizeof(title));
    if (strncmp(title, "Star Wars", 9) == 0 || strcmp(title, "SWTOR") == 0)
        ShowWindowAsync(window, SW_SHOW);
    return TRUE;
}

static void sampleClientStacks(const std::map<DWORD, HANDLE> &processes,
                               const std::map<DWORD, DWORD_PTR> &imageBases) {
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return;
    THREADENTRY32 entry = {}; entry.dwSize = sizeof(entry);
    if (Thread32First(snapshot, &entry)) do {
        std::map<DWORD, HANDLE>::const_iterator processIt = processes.find(entry.th32OwnerProcessID);
        std::map<DWORD, DWORD_PTR>::const_iterator baseIt = imageBases.find(entry.th32OwnerProcessID);
        if (processIt == processes.end() || baseIt == imageBases.end()) continue;
        HANDLE thread = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION,
                                   FALSE, entry.th32ThreadID);
        if (!thread || SuspendThread(thread) == (DWORD)-1) { if (thread) CloseHandle(thread); continue; }
        CONTEXT context = {}; context.ContextFlags = CONTEXT_CONTROL;
        if (GetThreadContext(thread, &context)) {
            DWORD_PTR base = baseIt->second;
            printf("CLIENT STACK pid=%lu tid=%lu eip=%08lX rva=%08lX",
                   entry.th32OwnerProcessID, entry.th32ThreadID, context.Eip,
                   context.Eip >= base && context.Eip < base + 0x02000000 ? (DWORD)(context.Eip - base) : 0xFFFFFFFF);
            DWORD frame = context.Ebp;
            for (int depth = 0; depth < 12 && frame; ++depth) {
                DWORD pair[2] = {}; SIZE_T got = 0;
                if (!ReadProcessMemory(processIt->second, (void *)frame, pair, sizeof(pair), &got) || got != sizeof(pair)) break;
                if (pair[1] >= base && pair[1] < base + 0x02000000) printf(" %08lX", pair[1] - (DWORD)base);
                frame = pair[0];
            }
            puts("");
        }
        ResumeThread(thread);
        CloseHandle(thread);
    } while (Thread32Next(snapshot, &entry));
    CloseHandle(snapshot);
    fflush(stdout);
}

int main(int argc, char **argv) {
    if (argc < 2 || argc > 3) {
        puts("Usage: CompatibilityLauncher.exe <old-client-directory> [test-timeout-seconds]");
        return 2;
    }
    const std::string toolDir = executableDirectory();
    std::ofstream startupSummary(toolDir + "\\startup-summary.log", std::ios::trunc);
    const auto reportStartup = [&](const std::string &message) {
        SYSTEMTIME now = {}; GetLocalTime(&now);
        char stamp[32] = {};
        sprintf_s(stamp, "[%02u:%02u:%02u] ", now.wHour, now.wMinute, now.wSecond);
        printf("%s%s\n", stamp, message.c_str()); fflush(stdout);
        startupSummary << stamp << message << std::endl;
    };
    reportStartup("[STARTUP] Concise progress and blockers: Diagnostics\\startup-summary.log");
    const std::string clientDir = argv[1];
    const char *cacheOverride = getenv("SWTOR_RESOURCE_CACHE");
    const std::string resourceCache = cacheOverride && *cacheOverride
        ? cacheOverride : toolDir + "\\GomCompatibility\\ResourceCacheApril2012";
    const std::string gom = readFile(resourceCache + "\\systemgenerated\\client.gom");
    const std::string bucketList =
        readFile(resourceCache + "\\systemgenerated\\buckets.info");
    const std::string scriptDefinitions =
        readFile(resourceCache + "\\systemgenerated\\scriptdef.list");
    const std::string prototypeIndex =
        readFile(resourceCache + "\\systemgenerated\\prototypes.info");
    if (gom.size() < 12 || gom.compare(0, 4, "DBLB") != 0) {
        puts("The selected client.gom is missing or has an invalid header.");
        return 3;
    }
    if (bucketList.empty()) {
        puts("The compatibility prototype-bucket list is missing.");
        return 3;
    }
    if (scriptDefinitions.empty()) {
        puts("The compatibility script-definition list is missing.");
        return 3;
    }
    printf("Compatibility resource cache: %s (client.gom: %u bytes).\n",
           resourceCache.c_str(), (unsigned)gom.size());
    std::string command = readFile(clientDir + "\\go1.bat");
    while (!command.empty() && (command.back() == '\r' || command.back() == '\n')) command.pop_back();
    if (command.empty()) {
        puts("The old client's go1.bat command is missing.");
        return 4;
    }
    const bool directShardLaunch = command.find("-set server ") != std::string::npos &&
                                   command.find("-set port ") != std::string::npos &&
                                   command.find("-set instance ") != std::string::npos;

    STARTUPINFOA startup = {}; startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESHOWWINDOW;
    // The operator needs a visible client for controlled doorway runs. The
    // April diagnostic build uses the title "SWTOR", not always "Star Wars".
    startup.wShowWindow = SW_SHOWNORMAL;
    PROCESS_INFORMATION created = {};
    std::string image = clientDir + "\\swtor-emu.exe";
    if (!CreateProcessA(image.c_str(), &command[0], NULL, NULL, FALSE,
                        DEBUG_PROCESS, NULL, clientDir.c_str(), &startup, &created)) {
        printf("Could not start the client (Windows error %lu).\n", GetLastError());
        return 5;
    }
    CloseHandle(created.hThread);
    CloseHandle(created.hProcess);
    puts("SWTOR compatibility bridge is active. Keep this window open while the game runs.");

    std::map<DWORD, HANDLE> processes;
    std::map<DWORD, DWORD_PTR> imageBases;
    std::map<DWORD, DWORD_PTR> readBreakpoint;
    std::map<DWORD, std::map<DWORD_PTR, BYTE> > probes;
    bool worldTravelStarted = false;
    std::map<DWORD, DWORD_PTR> loadingContinueFallbackMethod;
    std::map<DWORD, bool> loadingContinueFallbackSearched;
    // Diagnostic opt-out: allow the original CheckContinue player path to
    // issue its genuine CheckPhaseNeedsContinue server RPC.  The compatibility
    // fallback remains the default for ordinary runs.
    const bool loadingContinueFallbackEnabled =
        getenv("SWTOR_DISABLE_LOADING_CONTINUE_FALLBACK") == NULL;
    printf("LoadingContinueFallback: %s\n",
           loadingContinueFallbackEnabled ? "enabled" : "disabled for phase-RPC capture");
    std::map<DWORD, DWORD_PTR> pending;
    std::map<DWORD, WaitingRepositoryCall> waitingRepositoryCalls;
    std::map<DWORD, DWORD_PTR> releaseAfterShard;
    std::map<DWORD, unsigned> moduleSendCount;
    std::map<DWORD, unsigned> characterRewriteStage;
    std::map<DWORD, bool> characterDispatchActive;
    std::map<DWORD, bool> characterMethodsRefreshed;
    std::map<DWORD, unsigned> gomInjectionStage;
    std::map<DWORD, DWORD> gomInjectionThread;
    std::map<DWORD, DWORD_PTR> gomReturnBreakpoint;
    std::map<DWORD, DWORD_PTR> bucketReturnBreakpoint;
    std::map<DWORD, DWORD_PTR> prototypeReturnBreakpoint;
    std::map<DWORD, CONTEXT> prototypeCaller;
    std::map<DWORD, BYTE *> prototypeAllocation;
    std::map<DWORD, bool> prototypeInjected;
    std::map<DWORD, std::map<DWORD_PTR, CONTEXT> > guiCallers;
    std::map<DWORD, std::map<DWORD_PTR, CONTEXT> > specCallers;
    std::map<DWORD, std::map<DWORD_PTR, CONTEXT> > revisionCallers;
    std::map<DWORD,bool> revisionNotified;
    std::map<DWORD,bool> resourceInitializationResumed;
    std::map<DWORD, std::map<std::string, bool> > tracedResourcePaths;
    std::map<DWORD, DWORD> lastCharacterSpecResult;
    std::map<DWORD, ULONGLONG> lastCharacterSpecReport;
    std::map<DWORD, unsigned> guiCompletionCount;
    std::map<DWORD, bool> bucketListInjected;
    std::map<DWORD, DWORD_PTR> bucketFileReturnBreakpoint;
    std::map<DWORD, BYTE *> bucketFileAllocation;
    std::map<DWORD, DWORD> bucketLoader;
    std::map<DWORD, unsigned> nextBucketFile;
    std::map<DWORD, bool> scriptDefinitionInjected;
    std::map<DWORD, BYTE *> scriptDefinitionAllocation;
    std::map<DWORD, bool> scriptDefinitionCompleted;
    std::map<DWORD, bool> scriptWaitCleared;
    std::map<DWORD, std::string> lastPrototypeState;
    std::map<DWORD, std::string> lastBucketState;
    ULONGLONG started = GetTickCount64();
    DWORD timeoutMs = argc == 3 ? strtoul(argv[2], NULL, 10) * 1000UL : 0;
    bool done = false;
    unsigned suppliedCount = 0;
    std::string lastSupplied, lastRequested;
    bool bootstrapComplete = false;
    ULONGLONG areaSuppliedAt = 0;
    bool areaStacksSampled = false;
    bool areaWaitBypassed = false;
    bool repositoryAttachBypassed = false;
    bool compilerAttachBypassed = false;
    bool repositoryResultBypassed = false;
    bool compilerResultBypassed = false;
    bool repositoryStartupAdvanced = false;
    bool characterListRequestTriggered = false;
    ULONGLONG lastActivityAt = started;

    const unsigned bucketFileCount = bucketList.size() >= 11 && (BYTE)bucketList[8] == 0xC9
        ? ((unsigned)(BYTE)bucketList[9] << 8) | (BYTE)bucketList[10]
        : 0;
    const auto startBucketFileCallback =
        [&](DWORD pid, HANDLE process, DWORD_PTR base, unsigned index,
            CONTEXT &context) -> bool {
            char name[32] = {};
            sprintf_s(name, "%u.bkt", index);
            std::string data = readFile(resourceCache + "\\systemgenerated\\buckets\\" + name);
            if (data.empty()) return false;
            std::string path = std::string("/SystemGenerated/buckets/") + name;
            BYTE *allocation = NULL;
            DWORD_PTR returnAddress = 0;
            if (!startRepositoryCallback(process, data, path, base + 0x4300B0,
                                         bucketLoader[pid], context,
                                         allocation, returnAddress))
                return false;
            bucketFileAllocation[pid] = allocation;
            bucketFileReturnBreakpoint[pid] = returnAddress;
            probes[pid][returnAddress] = 0xC3;
            nextBucketFile[pid] = index + 1;
            return true;
        };

    while (!done && (!timeoutMs || GetTickCount64() - started < timeoutMs)) {
        DEBUG_EVENT event = {};
        if (!WaitForDebugEvent(&event, 500)) {
            if (bootstrapComplete)
                for (std::map<DWORD, HANDLE>::const_iterator it = processes.begin(); it != processes.end(); ++it)
                    EnumWindows(revealGameWindow, it->first);
            continue;
        }
        DWORD disposition = DBG_CONTINUE;
        HANDLE process = processes[event.dwProcessId];

        if (event.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT) {
            process = event.u.CreateProcessInfo.hProcess;
            processes[event.dwProcessId] = process;
            lastActivityAt = GetTickCount64();
            CloseHandle(event.u.CreateProcessInfo.hThread);
            DWORD_PTR base = (DWORD_PTR)event.u.CreateProcessInfo.lpBaseOfImage;
            imageBases[event.dwProcessId] = base;
            DWORD offsets[] = {
                0x742624, 0x42D371, 0x42D3A6, 0x42D534, 0xA87A1, 0x7937AB, 0x765BF, 0x765C1, 0x76763, 0x243F1E,
                // Direct shard mode uses services the archived emulator never implemented.
                // Advance through the client's real completion callbacks after each attach starts.
                0x24477F, 0x244821, 0x2449A0,
                // The client normally sends its module list from this routine.  Once the
                // connection is ready, use the same protocol object to ask for characters.
                0x67FC18, 0x67FC42, 0x67FC55, 0x67FC64,
                // Character-list handler entry, empty-list branch, and return.
                0x34EDC7, 0x34EF91, 0x34EFFB, 0x34F0ED, 0x34F0EF, 0x34F0FC, 0x34F1DE, 0x350B91, 0x350C14, 0x350C16,
                // Observe world travel without forcing its completion or changing packets.
                0x34F2B0, 0x34F46A, 0x34F482, 0x350240, 0x350461, 0x241740,
                // Startup-state check after the repository status query.
                0x3AD911, 0x3AD919, 0x3AD94B, 0x3AD952,
                0x7261E0, 0x738490, 0x712CD7, 0x7BFD34,
                0x773040, 0x7730BC, 0x7C01B0,
                0x3B0E3A, 0x3B0E3C, 0x3B1E90,
                0x745CF0, 0x7461FB, 0x23F810, 0x746600, 0x24A3E0,
                // Native script-definition parser milestones.
                0x7D72E0, 0x7D7400, 0x7D7427, 0x7D74A2, 0x7D7580, 0x7D75C1,
                0x7D75CD,
                // WinINet platform-request call and return sites.
                0x4C3F1F, 0x4C3F25, 0x4C3FCB, 0x4C3FD1,
                0x4C4010, 0x4C4016, 0x4C4067, 0x4C406D,
                0x4C41CB, 0x4C41D1
            };
            bool installed = true;
            for (unsigned i = 0; i < sizeof(offsets) / sizeof(offsets[0]); ++i) {
                // These probes stop all client threads for every asset. Keep
                // them opt-in now that native delivery has been established.
                if ((offsets[i] == 0x3B0E3A || offsets[i] == 0x3B0E3C || offsets[i] == 0x3B1E90) &&
                    !getenv("SWTOR_TRACE_ASSET_DELIVERY") && !getenv("SWTOR_TEST_PETMOUSE"))
                    continue;
                DWORD_PTR address = base + offsets[i];
                BYTE old = 0, trap = 0xCC; SIZE_T count = 0;
                ReadProcessMemory(process, (void *)address, &old, 1, &count);
                if (count != 1 || !WriteProcessMemory(process, (void *)address, &trap, 1, &count)) installed = false;
                else {
                    FlushInstructionCache(process, (void *)address, 1);
                    probes[event.dwProcessId][address] = old;
                    if (offsets[i] == 0x742624) readBreakpoint[event.dwProcessId] = address;
                }
            }
            if (!installed) {
                puts("Could not install the resource compatibility bridge.");
                TerminateProcess(process, 97);
            }
            if (event.u.CreateProcessInfo.hFile) CloseHandle(event.u.CreateProcessInfo.hFile);
        } else if (event.dwDebugEventCode == CREATE_THREAD_DEBUG_EVENT) {
            CloseHandle(event.u.CreateThread.hThread);
        } else if (event.dwDebugEventCode == LOAD_DLL_DEBUG_EVENT) {
            if (event.u.LoadDll.hFile) CloseHandle(event.u.LoadDll.hFile);
        } else if (event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT) {
            DWORD code = event.u.Exception.ExceptionRecord.ExceptionCode;
            DWORD_PTR address = (DWORD_PTR)event.u.Exception.ExceptionRecord.ExceptionAddress;
            if (code == EXCEPTION_BREAKPOINT && probes[event.dwProcessId].count(address)) {
                HANDLE thread = OpenThread(THREAD_ALL_ACCESS, FALSE, event.dwThreadId);
                CONTEXT context = {}; context.ContextFlags = CONTEXT_FULL;
                if (thread && GetThreadContext(thread, &context)) {
                    DWORD_PTR base = imageBases[event.dwProcessId];
                    if (address == base + 0x34F2B0 || address == base + 0x34F46A ||
                        address == base + 0x34F482 || address == base + 0x350240 ||
                        address == base + 0x350461 || address == base + 0x241740) {
                        SIZE_T count = 0;
                        DWORD manager = (DWORD)(base + 0x1096DF8), area = 0, state = 0, destination = 0;
                        BYTE selection = 0;
                        ReadProcessMemory(process, (void *)(manager + 0x28), &area, 4, &count);
                        if (area) ReadProcessMemory(process, (void *)(area + 0x8C), &state, 4, &count);
                        ReadProcessMemory(process, (void *)(manager + 0x70), &selection, 1, &count);
                        ReadProcessMemory(process, (void *)(manager + 0x74), &destination, 4, &count);
                        char target[192] = {};
                        if (destination) ReadProcessMemory(process, (void *)destination, target, sizeof(target)-1, &count);
                        static unsigned travelLogCount = 0;
                        if (address != base + 0x34F46A || (context.Eax & 0xff) || travelLogCount++ < 12) {
                            printf("World travel transition RVA=%08lX area=%08lX state=%lu selection=%u result=%u queued='%s'\n",
                                   (DWORD)(address-base), area, state, selection, context.Eax & 0xff, target);
                            fflush(stdout);
                        }
                        if (address == base + 0x34F482) reportStartup("[TRAVEL] Native area-load completion reached the active-area transition.");
                        if (address == base + 0x241740) {
                            worldTravelStarted = true;
                            reportStartup("[TRAVEL] Native client is connecting to the destination area service.");
                        }
                        BYTE old = probes[event.dwProcessId][address];
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
        // Keep the compatibility fix independent of optional breakpoint
        // observers. A busy client may never let WaitForDebugEvent time out,
        // so retry from the event path after travel as well.
        if (loadingContinueFallbackEnabled && worldTravelStarted) {
            for (std::map<DWORD, HANDLE>::const_iterator candidate = processes.begin();
                 candidate != processes.end(); ++candidate) {
                const DWORD scanPid = candidate->first;
                if (loadingContinueFallbackMethod[scanPid]) continue;
                DWORD_PTR method = 0;
                if (installLoadingContinueFallback(candidate->second, method)) {
                    loadingContinueFallbackMethod[scanPid] = method;
                    printf("LoadingContinueFallback: CheckContinue=%08lX patched to local PhaseNeedsContinue(false); asset waits preserved (event path).\n",
                           (DWORD)method);
                    fflush(stdout);
                }
            }
        }
                    if (gomReturnBreakpoint.count(event.dwProcessId) &&
                        address == gomReturnBreakpoint[event.dwProcessId]) {
                        SIZE_T count = 0;
                        BYTE failed = 0, complete = 0;
                        ReadProcessMemory(process, (void *)(base + 0xF8D038), &failed,
                                          sizeof(failed), &count);
                        ReadProcessMemory(process, (void *)(base + 0xF8D039), &complete,
                                          sizeof(complete), &count);
                        printf("Native client.gom callback returned: failed=%u complete=%u.\n",
                               failed, complete);
                        fflush(stdout);
                        gomInjectionStage[event.dwProcessId] = 2;
                        probes[event.dwProcessId].erase(address);
                        gomReturnBreakpoint.erase(event.dwProcessId);

                        DWORD_PTR startupCheck = base + 0x3AD919;
                        BYTE old = probes[event.dwProcessId][startupCheck];
                        WriteProcessMemory(process, (void *)startupCheck, &old, 1, &count);
                        FlushInstructionCache(process, (void *)startupCheck, 1);
                        context.Eip = (DWORD)startupCheck;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = startupCheck;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (bucketFileReturnBreakpoint.count(event.dwProcessId) &&
                        address == bucketFileReturnBreakpoint[event.dwProcessId]) {
                        SIZE_T count = 0;
                        probes[event.dwProcessId].erase(address);
                        bucketFileReturnBreakpoint.erase(event.dwProcessId);
                        if (bucketFileAllocation[event.dwProcessId]) {
                            VirtualFreeEx(process, bucketFileAllocation[event.dwProcessId],
                                          0, MEM_RELEASE);
                            bucketFileAllocation[event.dwProcessId] = NULL;
                        }
                        unsigned next = nextBucketFile[event.dwProcessId];
                        if (next % 25 == 0 || next == bucketFileCount) {
                            printf("Loaded %u of %u native prototype buckets.\n",
                                   next, bucketFileCount);
                            fflush(stdout);
                        }
                        if (next < bucketFileCount &&
                            startBucketFileCallback(event.dwProcessId, process, base,
                                                    next, context)) {
                            SetThreadContext(thread, &context);
                            CloseHandle(thread);
                            ContinueDebugEvent(event.dwProcessId, event.dwThreadId,
                                               DBG_CONTINUE);
                            continue;
                        }
                        if (next < bucketFileCount) {
                            printf("Could not supply prototype bucket %u.\n", next);
                            fflush(stdout);
                        }

                        DWORD_PTR startupCheck = base + 0x3AD952;
                        BYTE old = probes[event.dwProcessId][startupCheck];
                        WriteProcessMemory(process, (void *)startupCheck, &old, 1, &count);
                        FlushInstructionCache(process, (void *)startupCheck, 1);
                        context.Eip = (DWORD)startupCheck;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = startupCheck;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if(revisionCallers[event.dwProcessId].count(address)) {
                        CONTEXT resumed=revisionCallers[event.dwProcessId][address];
                        revisionCallers[event.dwProcessId].erase(address); probes[event.dwProcessId].erase(address);
                        if(!resourceInitializationResumed[event.dwProcessId]) {
                            SIZE_T count=0; DWORD adapter=0,owner=0,state=0;
                            ReadProcessMemory(process,(void *)(base+0x1092900),&adapter,4,&count);
                            ReadProcessMemory(process,(void *)(adapter+4),&owner,4,&count);
                            ReadProcessMemory(process,(void *)(owner+0x14),&state,4,&count);
                            if(owner && state==2) {
                                BYTE *trap=(BYTE *)VirtualAllocEx(process,NULL,1,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
                                if(trap) {
                                    BYTE opcode=0xCC; WriteProcessMemory(process,trap,&opcode,1,&count);
                                    DWORD target=(DWORD)trap; CONTEXT init=resumed; init.Esp-=4;
                                    WriteProcessMemory(process,(void *)init.Esp,&target,4,&count);
                                    init.Ecx=owner; init.Eip=(DWORD)(base+0x746DE0);
                                    resourceInitializationResumed[event.dwProcessId]=true;
                                    revisionCallers[event.dwProcessId][target]=resumed; probes[event.dwProcessId][target]=0xC3;
                                    reportStartup("[TEST] Resuming native resource-manager initialization after revision delivery.");
                                    SetThreadContext(thread,&init); CloseHandle(thread);
                                    ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE); continue;
                                }
                            }
                        }
                        DWORD_PTR resumeAt=base+0x3AD911; SIZE_T count=0;
                        BYTE old=probes[event.dwProcessId][resumeAt];
                        WriteProcessMemory(process,(void *)resumeAt,&old,1,&count);
                        FlushInstructionCache(process,(void *)resumeAt,1);
                        resumed.Eip=(DWORD)resumeAt; resumed.EFlags|=0x100; pending[event.dwThreadId]=resumeAt;
                        reportStartup("[TEST] Native asset-revision notification returned.");
                        SetThreadContext(thread,&resumed); CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE); continue;
                    }
                    if (specCallers[event.dwProcessId].count(address)) {
                        CONTEXT resumed=specCallers[event.dwProcessId][address];
                        specCallers[event.dwProcessId].erase(address);
                        probes[event.dwProcessId].erase(address);
                        DWORD_PTR resumeAt=base+0x3B0E3C;
                        SIZE_T count=0; BYTE old=probes[event.dwProcessId][resumeAt];
                        WriteProcessMemory(process,(void *)resumeAt,&old,1,&count);
                        FlushInstructionCache(process,(void *)resumeAt,1);
                        resumed.Eip=(DWORD)resumeAt; resumed.EFlags |= 0x100;
                        pending[event.dwThreadId]=resumeAt;
                        reportStartup("[TEST] Petmouse native resource completion returned; checking loader state.");
                        SetThreadContext(thread,&resumed); CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE);
                        continue;
                    }
                    if (guiCallers[event.dwProcessId].count(address)) {
                        unsigned completed = ++guiCompletionCount[event.dwProcessId];
                        if (completed == 54)
                            reportStartup("[READY] GUI resources: both lists and 52 XML files completed their native callbacks.");
                        CONTEXT resumed = guiCallers[event.dwProcessId][address];
                        guiCallers[event.dwProcessId].erase(address);
                        probes[event.dwProcessId].erase(address);
                        DWORD_PTR resumeAt = base + 0x3EB47F;
                        SIZE_T count = 0;
                        BYTE old = probes[event.dwProcessId][resumeAt];
                        WriteProcessMemory(process, (void *)resumeAt, &old, 1, &count);
                        FlushInstructionCache(process, (void *)resumeAt, 1);
                        resumed.Eip = (DWORD)resumeAt;
                        resumed.Eax = 1;
                        resumed.EFlags |= 0x100;
                        pending[event.dwThreadId] = resumeAt;
                        SetThreadContext(thread, &resumed);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x3EB47F) {
                        SIZE_T count = 0;
                        DWORD vtable = 0, pathAddress = 0;
                        ReadProcessMemory(process, (void *)context.Esi, &vtable, 4, &count);
                        ReadProcessMemory(process, (void *)context.Edi, &pathAddress, 4, &count);
                        char requestedPath[512] = {};
                        ReadProcessMemory(process, (void *)pathAddress, requestedPath, sizeof(requestedPath)-1, &count);
                        if (tracedResourcePaths[event.dwProcessId].size() < 200 && requestedPath[0] == '/' &&
                            !tracedResourcePaths[event.dwProcessId].count(requestedPath)) {
                            tracedResourcePaths[event.dwProcessId][requestedPath] = true;
                            printf("Post-script resource request: %s result=%08lX owner=%08lX vtableRVA=%08lX.\n",
                                   requestedPath, context.Eax, context.Esi, (DWORD)(vtable-base));
                            fflush(stdout);
                        }
                        // Native repository callbacks now run after synchronization.
                        // Keep the old manual bridge opt-in to avoid duplicate completion.
                        if (getenv("SWTOR_TEST_GUI_BRIDGE") &&
                            (vtable == base + 0xCB66D4 || vtable == base + 0xCB9694)) {
                            ReadProcessMemory(process, (void *)context.Edi, &pathAddress, 4, &count);
                            char pathBytes[512] = {};
                            ReadProcessMemory(process, (void *)pathAddress, pathBytes, sizeof(pathBytes)-1, &count);
                            std::string path(pathBytes);
                            for (size_t i=0; i<path.size(); ++i)
                                if (path[i]>='A' && path[i]<='Z') path[i] += 'a'-'A';
                            if (path.find("/guixml/") == 0 && path.find("..") == std::string::npos &&
                                path.find(':') == std::string::npos) {
                                std::string data = readFile(resourceCache + path);
                                BYTE *allocation = NULL;
                                DWORD_PTR returned = 0;
                                CONTEXT caller = context;
                                if (!data.empty() && startRepositoryCallback(process, data, path,
                                        base + 0x3EAD10, context.Esi, context, allocation, returned)) {
                                    // Native completion adapter uses ESI=owner, ECX=result,
                                    // no stack argument, and finishes dependency notification.
                                    context.Ecx = (DWORD)(allocation + data.size() + path.size() + 1);
                                    context.Esp += 4;
                                    DWORD returnWord = (DWORD)returned;
                                    WriteProcessMemory(process, (void *)context.Esp, &returnWord, 4, &count);
                                    guiCallers[event.dwProcessId][returned] = caller;
                                    probes[event.dwProcessId][returned] = 0xC3;
                                    printf("Supplying GUI resource through native completion: %s (%u bytes).\n",
                                           path.c_str(), (unsigned)data.size());
                                    fflush(stdout);
                                    SetThreadContext(thread, &context);
                                    CloseHandle(thread);
                                    ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                                    continue;
                                }
                            }
                        }
                        BYTE old = probes[event.dwProcessId][address];
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (prototypeReturnBreakpoint.count(event.dwProcessId) &&
                        address == prototypeReturnBreakpoint[event.dwProcessId]) {
                        probes[event.dwProcessId].erase(address);
                        prototypeReturnBreakpoint.erase(event.dwProcessId);
                        printf("Native prototype-index callback returned %lu.\n", context.Eax);
                        fflush(stdout);
                        CONTEXT resumed = prototypeCaller[event.dwProcessId];
                        resumed.Eip = (DWORD)(base + 0x3AD952);
                        resumed.EFlags |= 0x100;
                        pending[event.dwThreadId] = resumed.Eip;
                        SetThreadContext(thread, &resumed);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (bucketReturnBreakpoint.count(event.dwProcessId) &&
                        address == bucketReturnBreakpoint[event.dwProcessId]) {
                        SIZE_T count = 0;
                        probes[event.dwProcessId].erase(address);
                        bucketReturnBreakpoint.erase(event.dwProcessId);
                        DWORD total = 0;
                        ReadProcessMemory(process,
                                          (void *)(bucketLoader[event.dwProcessId] + 0xB8),
                                          &total, sizeof(total), &count);
                        printf("Native prototype-bucket-list callback scheduled %lu buckets.\n",
                               total);
                        fflush(stdout);

                        if (total && startBucketFileCallback(event.dwProcessId, process, base,
                                                             0, context)) {
                            puts("Supplying recovered prototype buckets through their native parser.");
                            fflush(stdout);
                            SetThreadContext(thread, &context);
                            CloseHandle(thread);
                            ContinueDebugEvent(event.dwProcessId, event.dwThreadId,
                                               DBG_CONTINUE);
                            continue;
                        }

                        DWORD_PTR startupCheck = base + 0x3AD952;
                        BYTE old = probes[event.dwProcessId][startupCheck];
                        WriteProcessMemory(process, (void *)startupCheck, &old, 1, &count);
                        FlushInstructionCache(process, (void *)startupCheck, 1);
                        context.Eip = (DWORD)startupCheck;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = startupCheck;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (releaseAfterShard.count(event.dwProcessId) &&
                        address == releaseAfterShard[event.dwProcessId]) {
                        WaitingRepositoryCall &wait = waitingRepositoryCalls[event.dwProcessId];
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        CONTEXT resumed = wait.caller;
                        resumed.ContextFlags = CONTEXT_FULL;
                        resumed.Eip = (DWORD)(base + 0x765C1);
                        resumed.Esp = wait.caller.Esp;
                        resumed.Eax = 1;
                        resumed.EFlags &= ~0x100;
                        SetThreadContext(thread, &resumed);
                        wait.released = true;
                        repositoryResultBypassed = true;
                        releaseAfterShard.erase(event.dwProcessId);
                        puts("Shard callback returned; released the waiting RepositoryServer initializer.");
                        fflush(stdout);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x243F1E && directShardLaunch) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        if (context.Edi < 9) {
                            context.Edi = 9;
                            puts("Direct shard launch: requested the complete shard-connected state.");
                            fflush(stdout);
                        }
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x7937AB && bootstrapComplete && !areaWaitBypassed && (context.Eax & 0xFF) == 0) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        context.Eip = (DWORD)(base + 0x7943DE);
                        SetThreadContext(thread, &context);
                        areaWaitBypassed = true;
                        puts("Bypassed the incompatible optional area-settings wait.");
                        fflush(stdout);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x24477F && directShardLaunch && getenv("SWTOR_TEST_REPOSITORY_BYPASS") && !repositoryAttachBypassed &&
                        (context.Eax & 0xFF) != 0) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);

                        DWORD returnAddress = (DWORD)(base + 0x24479F);
                        context.Esp -= sizeof(returnAddress);
                        WriteProcessMemory(process, (void *)context.Esp, &returnAddress, sizeof(returnAddress), &count);
                        context.Ecx = context.Edi;
                        context.Eip = (DWORD)(base + 0x2447B0);
                        SetThreadContext(thread, &context);
                        repositoryAttachBypassed = true;
                        puts("Repository attach started; invoked the client's repository-connected transition.");
                        fflush(stdout);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x244821 && directShardLaunch && !compilerAttachBypassed) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);

                        DWORD returnAddress = (DWORD)address;
                        context.Esp -= sizeof(returnAddress);
                        WriteProcessMemory(process, (void *)context.Esp, &returnAddress, sizeof(returnAddress), &count);
                        context.Ecx = context.Edi;
                        context.Eip = (DWORD)(base + 0x244840);
                        SetThreadContext(thread, &context);
                        compilerAttachBypassed = true;
                        puts("Compiler attach started; invoked the client's compilers-connected transition.");
                        fflush(stdout);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x765BF && directShardLaunch && getenv("SWTOR_TEST_REPOSITORY_BYPASS")) {
                        WaitingRepositoryCall &wait = waitingRepositoryCalls[event.dwProcessId];
                        if (!wait.valid) {
                            wait.threadId = event.dwThreadId;
                            wait.caller = context;
                            wait.valid = true;
                            puts("Repository initialization entered; preserving its caller while the shard connects.");
                            fflush(stdout);
                        }
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x2449A0 && directShardLaunch) {
                        WaitingRepositoryCall &wait = waitingRepositoryCalls[event.dwProcessId];
                        if (wait.valid && !wait.released) {
                            if (wait.threadId == event.dwThreadId) {
                                DWORD returnAddress = 0; SIZE_T count = 0;
                                if (ReadProcessMemory(process, (void *)context.Esp, &returnAddress,
                                                      sizeof(returnAddress), &count) && count == sizeof(returnAddress)) {
                                    BYTE original = 0, trap = 0xCC;
                                    ReadProcessMemory(process, (void *)returnAddress, &original, 1, &count);
                                    if (count == 1 && WriteProcessMemory(process, (void *)returnAddress, &trap, 1, &count)) {
                                        FlushInstructionCache(process, (void *)returnAddress, 1);
                                        probes[event.dwProcessId][returnAddress] = original;
                                        releaseAfterShard[event.dwProcessId] = returnAddress;
                                        puts("Shard connection completed; repository release is armed for the callback return.");
                                        fflush(stdout);
                                    }
                                }
                            } else {
                                HANDLE waitingThread = OpenThread(THREAD_ALL_ACCESS, FALSE, wait.threadId);
                                if (waitingThread && SuspendThread(waitingThread) != (DWORD)-1) {
                                    CONTEXT resumed = wait.caller;
                                    resumed.ContextFlags = CONTEXT_FULL;
                                    resumed.Eip = (DWORD)(base + 0x765C1);
                                    resumed.Esp = wait.caller.Esp;
                                    resumed.Eax = 1;
                                    resumed.EFlags &= ~0x100;
                                    if (SetThreadContext(waitingThread, &resumed)) {
                                        wait.released = true;
                                        repositoryResultBypassed = true;
                                        puts("Shard connection completed; released the waiting RepositoryServer initializer.");
                                        fflush(stdout);
                                    }
                                    ResumeThread(waitingThread);
                                }
                                if (waitingThread) CloseHandle(waitingThread);
                            }
                        }
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x765C1) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        if (getenv("SWTOR_TEST_REPOSITORY_BYPASS") && !repositoryResultBypassed && context.Eax != 1) {
                            context.Eax = 1;
                            repositoryResultBypassed = true;
                            puts("Accepted the compatibility RepositoryServer attach result.");
                            fflush(stdout);
                        }
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x76763) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        if (!compilerResultBypassed && (context.Eax & 0xFF) == 0) {
                            context.Eax = (context.Eax & 0xFFFFFF00) | 1;
                            compilerResultBypassed = true;
                            puts("Accepted the compatibility compiler-service attach result.");
                            fflush(stdout);
                        }
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x3AD911 && directShardLaunch) {
                        if(getenv("SWTOR_TEST_REVISION_BRIDGE") && repositoryAttachBypassed && !revisionNotified[event.dwProcessId]) {
                            revisionNotified[event.dwProcessId]=true;
                            CONTEXT caller=context; BYTE *allocation=0; DWORD_PTR returned=0;
                            std::string revision("1\0",2), path("local-asset-revision");
                            if(startRepositoryCallback(process,revision,path,base+0x23F700,0,context,allocation,returned)) {
                                DWORD stringObject=(DWORD)(allocation+revision.size()+path.size()+1);
                                DWORD stringFields[2]={(DWORD)allocation,0}; SIZE_T count=0;
                                WriteProcessMemory(process,(void *)stringObject,stringFields,sizeof(stringFields),&count);
                                DWORD frame[3]={(DWORD)returned,0,stringObject}; context.Esp-=4;
                                WriteProcessMemory(process,(void *)context.Esp,frame,sizeof(frame),&count);
                                revisionCallers[event.dwProcessId][returned]=caller; probes[event.dwProcessId][returned]=0xC3;
                                reportStartup("[TEST] Restoring native asset-revision notification for local revision 1.");
                                SetThreadContext(thread,&context); CloseHandle(thread);
                                ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE); continue;
                            }
                        }
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        if (repositoryAttachBypassed && context.Eax != 5) {
                            context.Eip = (DWORD)(base + 0x3AD965);
                            if (!repositoryStartupAdvanced) {
                                repositoryStartupAdvanced = true;
                                puts("Repository attach is complete; advanced the asset startup state into GOM loading.");
                                fflush(stdout);
                            }
                        } else {
                            context.Eip = (DWORD)address;
                            context.EFlags |= 0x100;
                            pending[event.dwThreadId] = address;
                        }
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x3AD919 && directShardLaunch && repositoryStartupAdvanced) {
                        SIZE_T count = 0;
                        unsigned &stage = gomInjectionStage[event.dwProcessId];
                        if (stage == 0) {
                            DWORD gomObject = 0;
                            ReadProcessMemory(process, (void *)(base + 0x10926E0), &gomObject,
                                              sizeof(gomObject), &count);
                            if (gomObject) {
                                const char resourcePath[] = "/SystemGenerated/client.gom";
                                const SIZE_T callbackSize = 0x2C;
                                const SIZE_T allocationSize = gom.size() + sizeof(resourcePath) + callbackSize + 1;
                                BYTE *remote = (BYTE *)VirtualAllocEx(process, NULL, allocationSize,
                                                                      MEM_COMMIT | MEM_RESERVE,
                                                                      PAGE_EXECUTE_READWRITE);
                                if (remote) {
                                    BYTE *remotePath = remote + gom.size();
                                    BYTE *remoteResult = remotePath + sizeof(resourcePath);
                                    BYTE *remoteReturn = remoteResult + callbackSize;
                                    DWORD result[11] = {};
                                    result[0] = 1; // Repository resource-data result.
                                    result[4] = (DWORD)remote; // Raw resource bytes.
                                    result[6] = (DWORD)gom.size();
                                    result[10] = (DWORD)remotePath;
                                    SIZE_T wrote = 0;
                                    bool copied =
                                        WriteProcessMemory(process, remote, gom.data(), gom.size(), &wrote) &&
                                        wrote == gom.size() &&
                                        WriteProcessMemory(process, remotePath, resourcePath, sizeof(resourcePath), &wrote) &&
                                        wrote == sizeof(resourcePath) &&
                                        WriteProcessMemory(process, remoteResult, result, sizeof(result), &wrote) &&
                                        wrote == sizeof(result);
                                    if (copied) {
                                        BYTE trap = 0xCC;
                                        copied = WriteProcessMemory(process, remoteReturn, &trap, 1, &wrote) && wrote == 1;
                                    }
                                    if (copied) {
                                        DWORD callFrame[2] = {(DWORD)remoteReturn, (DWORD)remoteResult};
                                        context.Esp -= sizeof(callFrame);
                                        WriteProcessMemory(process, (void *)context.Esp, callFrame,
                                                           sizeof(callFrame), &wrote);
                                        context.Eip = (DWORD)(base + 0x42D340);
                                        stage = 1;
                                        gomInjectionThread[event.dwProcessId] = event.dwThreadId;
                                        gomReturnBreakpoint[event.dwProcessId] = (DWORD_PTR)remoteReturn;
                                        probes[event.dwProcessId][(DWORD_PTR)remoteReturn] = 0xC3;
                                        puts("Supplying the compatibility client.gom through the client's native repository callback.");
                                        fflush(stdout);
                                        SetThreadContext(thread, &context);
                                        CloseHandle(thread);
                                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                                        continue;
                                    }
                                }
                                puts("Could not allocate the compatibility GOM callback data in the client.");
                                fflush(stdout);
                            }
                        }

                        BYTE old = probes[event.dwProcessId][address];
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x42D3A6 || address == base + 0x42D534) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        if (gomInjectionStage[event.dwProcessId] == 1 &&
                            gomInjectionThread[event.dwProcessId] == event.dwThreadId) {
                            if (address == base + 0x42D3A6)
                                printf("Native client.gom callback accepted repository result code 0x%08lX.\n", context.Eax);
                            else
                                puts("Native client.gom parser reached its completion flag.");
                            fflush(stdout);
                        }
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x3AD952 &&
                        directShardLaunch) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);

                        DWORD startupState = 0;
                        ReadProcessMemory(process, (void *)(context.Esi + 4), &startupState,
                                          sizeof(startupState), &count);
                        if (startupState == 3 || startupState == 4) {
                            DWORD wrapper = 0, loader = 0;
                            BYTE waiting = 0;
                            DWORD total = 0, loaded = 0, pendingCount = 0;
                            DWORD wrapperOffset = startupState == 3 ? 0x14 : 0x18;
                            ReadProcessMemory(process, (void *)(context.Esi + wrapperOffset),
                                              &wrapper, sizeof(wrapper), &count);
                            if (wrapper) {
                                ReadProcessMemory(process, (void *)(wrapper + 0x70),
                                                  &waiting, sizeof(waiting), &count);
                                ReadProcessMemory(process, (void *)(wrapper + 0x74),
                                                  &loader, sizeof(loader), &count);
                            }
                            if (loader) {
                                if (startupState == 3) {
                                    ReadProcessMemory(process, (void *)(loader + 0x18),
                                                      &total, sizeof(total), &count);
                                    ReadProcessMemory(process, (void *)(loader + 0x4C),
                                                      &loaded, sizeof(loaded), &count);
                                    ReadProcessMemory(process, (void *)(loader + 0x68),
                                                      &pendingCount, sizeof(pendingCount), &count);
                                } else {
                                    ReadProcessMemory(process, (void *)(loader + 0xB8),
                                                      &total, sizeof(total), &count);
                                    ReadProcessMemory(process, (void *)(loader + 0xBC),
                                                      &loaded, sizeof(loaded), &count);
                                    ReadProcessMemory(process, (void *)(loader + 0x94),
                                                      &pendingCount, sizeof(pendingCount), &count);
                                }
                            }
                            char stateText[160] = {};
                            sprintf_s(stateText, "waiting=%u total=%lu loaded=%lu pending=%lu",
                                      waiting, total, loaded, pendingCount);
                            std::map<DWORD, std::string> &lastState =
                                startupState == 3 ? lastPrototypeState : lastBucketState;
                            if (lastState[event.dwProcessId] != stateText) {
                                lastState[event.dwProcessId] = stateText;
                                printf("%s loader state changed: %s.\n",
                                       startupState == 3 ? "Prototype" : "Prototype-bucket",
                                       stateText);
                                fflush(stdout);
                            }
                            if (repositoryStartupAdvanced && startupState == 3 && wrapper && waiting &&
                                !prototypeInjected[event.dwProcessId] &&
                                prototypeIndex.compare(0, 4, "PINF") == 0) {
                                BYTE *allocation = NULL;
                                DWORD_PTR returned = 0;
                                prototypeCaller[event.dwProcessId] = context;
                                if (startRepositoryCallback(process, prototypeIndex,
                                        "/SystemGenerated/prototypes.info", base + 0x42FAD0,
                                        wrapper, context, allocation, returned)) {
                                    prototypeInjected[event.dwProcessId] = true;
                                    prototypeAllocation[event.dwProcessId] = allocation;
                                    prototypeReturnBreakpoint[event.dwProcessId] = returned;
                                    probes[event.dwProcessId][returned] = 0xC3;
                                    puts("Supplying prototypes.info through the native PINF callback.");
                                    fflush(stdout);
                                    SetThreadContext(thread, &context);
                                    CloseHandle(thread);
                                    ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                                    continue;
                                }
                            }
                            if (repositoryStartupAdvanced && startupState == 4 && wrapper && waiting && !total &&
                                !bucketListInjected[event.dwProcessId]) {
                                const char resourcePath[] = "/systemgenerated/buckets.info";
                                const SIZE_T callbackSize = 0x2C;
                                const SIZE_T allocationSize = bucketList.size() +
                                    sizeof(resourcePath) + callbackSize + 1;
                                BYTE *remote = (BYTE *)VirtualAllocEx(process, NULL, allocationSize,
                                                                      MEM_COMMIT | MEM_RESERVE,
                                                                      PAGE_EXECUTE_READWRITE);
                                if (remote) {
                                    BYTE *remotePath = remote + bucketList.size();
                                    BYTE *remoteResult = remotePath + sizeof(resourcePath);
                                    BYTE *remoteReturn = remoteResult + callbackSize;
                                    DWORD result[11] = {};
                                    result[0] = 1;
                                    result[4] = (DWORD)remote;
                                    result[6] = (DWORD)bucketList.size();
                                    result[10] = (DWORD)remotePath;
                                    SIZE_T wrote = 0;
                                    bool copied =
                                        WriteProcessMemory(process, remote, bucketList.data(),
                                                           bucketList.size(), &wrote) &&
                                        wrote == bucketList.size() &&
                                        WriteProcessMemory(process, remotePath, resourcePath,
                                                           sizeof(resourcePath), &wrote) &&
                                        wrote == sizeof(resourcePath) &&
                                        WriteProcessMemory(process, remoteResult, result,
                                                           sizeof(result), &wrote) &&
                                        wrote == sizeof(result);
                                    BYTE trap = 0xCC;
                                    copied = copied &&
                                        WriteProcessMemory(process, remoteReturn, &trap, 1, &wrote) &&
                                        wrote == 1;
                                    if (copied) {
                                        DWORD callFrame[2] = {(DWORD)remoteReturn,
                                                              (DWORD)remoteResult};
                                        context.Esp -= sizeof(callFrame);
                                        WriteProcessMemory(process, (void *)context.Esp, callFrame,
                                                           sizeof(callFrame), &wrote);
                                        context.Ecx = wrapper;
                                        context.Eip = (DWORD)(base + 0x430AF0);
                                        bucketLoader[event.dwProcessId] = loader;
                                        bucketListInjected[event.dwProcessId] = true;
                                        bucketReturnBreakpoint[event.dwProcessId] =
                                            (DWORD_PTR)remoteReturn;
                                        probes[event.dwProcessId][(DWORD_PTR)remoteReturn] = 0xC3;
                                        puts("Supplying buckets.info through the native prototype-bucket-list callback.");
                                        fflush(stdout);
                                        SetThreadContext(thread, &context);
                                        CloseHandle(thread);
                                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId,
                                                           DBG_CONTINUE);
                                        continue;
                                    }
                                }
                                puts("Could not allocate the prototype-bucket-list callback data in the client.");
                                fflush(stdout);
                            }
                        }
                        if (startupState == 6 && (!lastCharacterSpecResult.count(event.dwProcessId) ||
                            lastCharacterSpecResult[event.dwProcessId] != context.Eax ||
                            GetTickCount64() - lastCharacterSpecReport[event.dwProcessId] >= 30000)) {
                            lastCharacterSpecResult[event.dwProcessId] = context.Eax;
                            lastCharacterSpecReport[event.dwProcessId] = GetTickCount64();
                            DWORD manager=0, root=0, total=0;
                            ReadProcessMemory(process,(void *)(base+0x10929DC),&manager,4,&count);
                            if (manager) {
                                ReadProcessMemory(process,(void *)(manager+0x28),&root,4,&count);
                                ReadProcessMemory(process,(void *)(manager+0x30),&total,4,&count);
                            }
                            std::vector<DWORD> nodes;
                            std::map<DWORD,bool> seen;
                            if(root) nodes.push_back(root);
                            unsigned ready=0, failed=0, waiting=0;
                            std::string names;
                            while(!nodes.empty() && seen.size()<4096) {
                                DWORD node=nodes.back(); nodes.pop_back();
                                if(!node || node==manager+0x20 || seen.count(node)) continue;
                                seen[node]=true;
                                DWORD record[5]={};
                                if(!ReadProcessMemory(process,(void *)node,record,sizeof(record),&count)) continue;
                                // Native successor at VA973090: right=0, left=4, parent=8.
                                nodes.push_back(record[0]); nodes.push_back(record[1]);
                                DWORD state=0xFFFFFFFF, name=0;
                                ReadProcessMemory(process,(void *)(record[4]+0xC),&state,4,&count);
                                if(state==2) ++ready;
                                else if(state==3) ++failed;
                                else {
                                    ++waiting;
                                    if(waiting<=5) {
                                        ReadProcessMemory(process,(void *)(record[4]+0x160),&name,4,&count);
                                        if(!names.empty()) names += ", ";
                                        names += readRemoteWide(process,name);
                                    }
                                }
                            }
                            char message[1024]={};
                            sprintf_s(message,"[%s] Character-spec initialization: ready=%u/%lu, waiting=%u, failed=%u. Pending examples: %s.",
                                      context.Eax==1?"READY":context.Eax==2?"FAILED":"WAIT",
                                      ready,total,waiting,failed,names.empty()?"none":names.c_str());
                            reportStartup(message);
                            if(context.Eax==0)
                                reportStartup("[BLOCKER] The native character-spec loader has not completed. Character selection cannot finish startup; pings only confirm the server connection is alive.");
                        }
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x3AD94B && directShardLaunch &&
                        repositoryStartupAdvanced) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        if ((context.Eax & 0xFF) != 0 &&
                            !scriptDefinitionInjected[event.dwProcessId]) {
                            DWORD owner = 0, listener = 0;
                            ReadProcessMemory(process, (void *)(context.Esi + 0x20),
                                              &owner, sizeof(owner), &count);
                            if (owner)
                                ReadProcessMemory(process, (void *)(owner + 0x2C0),
                                                  &listener, sizeof(listener), &count);
                            BYTE *allocation = NULL;
                            if (listener &&
                                startScriptDefinitionCallback(
                                    process, scriptDefinitions,
                                    "/SystemGenerated/scriptDef.list",
                                    base + 0x7D72E0, listener, allocation)) {
                                scriptDefinitionInjected[event.dwProcessId] = true;
                                scriptDefinitionAllocation[event.dwProcessId] = allocation;
                                puts("Supplying scriptDef.list through the client's native script-definition parser.");
                                fflush(stdout);
                            }
                            else {
                                puts("The native script-definition listener is not ready; preserving its wait.");
                                fflush(stdout);
                            }
                        }
                        if (scriptDefinitionInjected[event.dwProcessId]) {
                            if (!scriptDefinitionCompleted[event.dwProcessId]) {
                                // Keep stage 5 active until its native callback has
                                // registered every definition and updated the owner.
                                // Native test al,al -> jne returns while waiting.
                                context.Eax = (context.Eax & 0xFFFFFF00) | 1;
                                context.EFlags &= ~0x40;
                            }
                            else {
                                context.Eax &= 0xFFFFFF00;
                                context.EFlags |= 0x40;
                                if (!scriptWaitCleared[event.dwProcessId]) {
                                    scriptWaitCleared[event.dwProcessId] = true;
                                    puts("Script definitions are ready; advancing into game-data initialization.");
                                    fflush(stdout);
                                }
                            }
                        }
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x7D72E0 ||
                        address == base + 0x7D7400 ||
                        address == base + 0x7D7427 ||
                        address == base + 0x7D74A2 ||
                        address == base + 0x7D7580 ||
                        address == base + 0x7D75C1 ||
                        address == base + 0x7D75CD) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        probes[event.dwProcessId].erase(address);
                        if (address == base + 0x7D72E0)
                            puts("Native script-definition parser entered.");
                        else if (address == base + 0x7D7400)
                            puts("Native script-definition parser accepted the resource result.");
                        else if (address == base + 0x7D7427)
                            puts("Native script-definition list was decoded.");
                        else if (address == base + 0x7D74A2)
                            puts("Native script definitions are being registered with GOM.");
                        else if (address == base + 0x7D7580)
                            puts("Native script-definition registration loop completed.");
                        else if (address == base + 0x7D75C1) {
                            puts("Native script-definition parser completed.");
                        }
                        else {
                            BYTE waiting = 0xFF;
                            ReadProcessMemory(process, (void *)(context.Edi + 0x2E1),
                                              &waiting, sizeof(waiting), &count);
                            printf("Native script-definition completion callback returned; waiting=%u.\n",
                                   waiting);
                            scriptDefinitionCompleted[event.dwProcessId] = true;
                            // Script completion does not prove character-spec readiness.
                            // Leave that gate to the native stage-6 result.
                            reportStartup("[READY] Native script definitions registered; beginning game and GUI initialization.");
                            DWORD_PTR requestProbe = base + 0x3EB47F;
                            BYTE original = 0, trap = 0xCC;
                            if (ReadProcessMemory(process, (void *)requestProbe, &original, 1, &count) && original == 0x8B) {
                                probes[event.dwProcessId][requestProbe] = original;
                                WriteProcessMemory(process, (void *)requestProbe, &trap, 1, &count);
                                FlushInstructionCache(process, (void *)requestProbe, 1);
                            }
                        }
                        fflush(stdout);
                        context.Eip = (DWORD)address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId,
                                           DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x67FC18 && directShardLaunch &&
                        !characterListRequestTriggered) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        unsigned sends = ++moduleSendCount[event.dwProcessId];
                        DWORD gameObject = 0;
                        ReadProcessMemory(process, (void *)(base + 0x10926F0), &gameObject,
                                          sizeof(gameObject), &count);
                        if (sends >= 2 && gameObject &&
                            scriptDefinitionCompleted[event.dwProcessId] &&
                            lastCharacterSpecResult.count(event.dwProcessId) &&
                            lastCharacterSpecResult[event.dwProcessId] == 1) {
                            characterRewriteStage[event.dwProcessId] = 1;
                            puts("Game data and script definitions are initialized; converting this module report into a character-list request.");
                            fflush(stdout);
                        } else if (sends >= 2) {
                            puts("Character-list request is waiting for GOM, scripts, and character-spec initialization.");
                            fflush(stdout);
                        }
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x67FC42 || address == base + 0x67FC55 ||
                        address == base + 0x67FC64) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        unsigned &stage = characterRewriteStage[event.dwProcessId];
                        if (stage && !characterListRequestTriggered) {
                            if (address == base + 0x67FC42 && stage == 1) {
                                const DWORD opcode = 0xFB2047CE;
                                context.Esp -= sizeof(opcode);
                                WriteProcessMemory(process, (void *)context.Esp, &opcode,
                                                   sizeof(opcode), &count);
                                context.Eip = (DWORD)(base + 0x67FC47);
                                stage = 2;
                            } else if (address == base + 0x67FC55 && stage == 2) {
                                // CharacterListRequest has no ModulesList payload argument.
                                context.Eip = (DWORD)(base + 0x67FC64);
                            } else if (address == base + 0x67FC64 && stage == 2) {
                                const DWORD opcode = 0xFB2047CE;
                                context.Esp -= sizeof(opcode);
                                WriteProcessMemory(process, (void *)context.Esp, &opcode,
                                                   sizeof(opcode), &count);
                                context.Eip = (DWORD)(base + 0x67FC69);
                                characterListRequestTriggered = true;
                                stage = 0;
                                puts("Sent the character-list request through the client's normal packet path.");
                                fflush(stdout);
                            } else {
                                context.Eip = (DWORD)address;
                                context.EFlags |= 0x100;
                                pending[event.dwThreadId] = address;
                            }
                        } else {
                            context.Eip = (DWORD)address;
                            context.EFlags |= 0x100;
                            pending[event.dwThreadId] = address;
                        }
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    DWORD dispatchOffset = (DWORD)(address - base);
                    if (dispatchOffset == 0x1BE538 || dispatchOffset == 0x1BE552 ||
                        dispatchOffset == 0x1BE745 || dispatchOffset == 0x1BE747 ||
                        dispatchOffset == 0x1CA960 || dispatchOffset == 0x1CA7F4 ||
                        dispatchOffset == 0x1CA838 || dispatchOffset == 0x1CA866 ||
                        dispatchOffset == 0x1CA7D6 || dispatchOffset == 0x1CA23C ||
                        dispatchOffset == 0x1CA257 || dispatchOffset == 0x1CB790) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        if (characterDispatchActive[event.dwThreadId]) {
                            if (dispatchOffset == 0x1CA7D6 && scriptDefinitionCompleted[event.dwProcessId] &&
                                !characterMethodsRefreshed[event.dwProcessId]) {
                                // Startup can cache an empty method table before the injected
                                // script definitions finish registering. Invalidate only this
                                // first character callback's table; let the native code rebuild it.
                                const ULONGLONG stale = 0;
                                if (WriteProcessMemory(process, (void *)(context.Esi+0x30), &stale, sizeof(stale), &count) &&
                                    count == sizeof(stale)) {
                                    context.Ecx = 0;
                                    characterMethodsRefreshed[event.dwProcessId] = true;
                                    puts("Rebuilding the character callback method cache after script registration.");
                                }
                            }
                            DWORD frame[8] = {}, object[24] = {};
                            ReadProcessMemory(process, (void *)(context.Ebp-0x34), frame, sizeof(frame), &count);
                            ReadProcessMemory(process, (void *)context.Eax, object, sizeof(object), &count);
                            printf("Script lookup RVA=%08lX eax=%08lX ecx=%08lX edx=%08lX esi=%08lX frame=%08lX %08lX %08lX object=%08lX %08lX class=%08lX\n", dispatchOffset, context.Eax, context.Ecx, context.Edx, context.Esi, frame[0], frame[1], frame[2], object[0], object[1], object[18]);
                            fflush(stdout);
                        }
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x34EDC7 || address == base + 0x34EF91 ||
                        address == base + 0x34F1DE || address == base + 0x34EFFB ||
                        address == base + 0x34F0ED || address == base + 0x34F0EF ||
                        address == base + 0x34F0FC || address == base + 0x350B91 ||
                        address == base + 0x350C14 || address == base + 0x350C16) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        if (address == base + 0x350C14) {
                            characterDispatchActive[event.dwThreadId] = true;
                            // Arm internal probes only once this specific callback is about
                            // to run, avoiding startup script-registration overhead.
                            const DWORD offsets[] = {0x1BE538, 0x1BE552, 0x1BE745, 0x1BE747,
                                0x1CA960, 0x1CA7D6, 0x1CA7F4, 0x1CA838, 0x1CA866,
                                0x1CA23C, 0x1CA257, 0x1CB790};
                            for (unsigned i=0; i<sizeof(offsets)/sizeof(offsets[0]); ++i) {
                                // Method-cache repair needs only this one site. Full lookup
                                // tracing is extremely expensive while world scripts run.
                                if (offsets[i] != 0x1CA7D6 && !getenv("SWTOR_TRACE_SCRIPT_LOOKUPS")) continue;
                                DWORD_PTR probe = base + offsets[i];
                                if (!probes[event.dwProcessId].count(probe)) {
                                    BYTE original = 0, trap = 0xCC;
                                    if (ReadProcessMemory(process, (void *)probe, &original, 1, &count) &&
                                        WriteProcessMemory(process, (void *)probe, &trap, 1, &count)) {
                                        probes[event.dwProcessId][probe] = original;
                                        FlushInstructionCache(process, (void *)probe, 1);
                                    }
                                }
                            }
                        } else if (address == base + 0x350C16) {
                            characterDispatchActive[event.dwThreadId] = false;
                            // These were scoped to the character callback. Leaving them
                            // armed pauses every client thread on every later script lookup,
                            // even when their logging condition is false.
                            const DWORD lookupOffsets[] = {0x1BE538, 0x1BE552, 0x1BE745, 0x1BE747,
                                0x1CA960, 0x1CA7D6, 0x1CA7F4, 0x1CA838, 0x1CA866,
                                0x1CA23C, 0x1CA257, 0x1CB790};
                            for (unsigned i=0; i<sizeof(lookupOffsets)/sizeof(lookupOffsets[0]); ++i) {
                                DWORD_PTR site=base+lookupOffsets[i];
                                if (probes[event.dwProcessId].count(site)) {
                                    BYTE original=probes[event.dwProcessId][site];
                                    WriteProcessMemory(process,(void*)site,&original,1,&count);
                                    FlushInstructionCache(process,(void*)site,1);
                                    probes[event.dwProcessId].erase(site);
                                }
                            }
                            puts("Character callback returned; removed its temporary script-lookup probes.");
                        }
                        if (address == base + 0x34EDC7) {
                            DWORD characterState = 0;
                            ReadProcessMemory(process, (void *)(context.Ebp + 8), &characterState,
                                              sizeof(characterState), &count);
                            DWORD state28 = 0; BYTE state70 = 0;
                            if (characterState) {
                                ReadProcessMemory(process, (void *)(characterState + 0x28), &state28,
                                                  sizeof(state28), &count);
                                ReadProcessMemory(process, (void *)(characterState + 0x70), &state70,
                                                  sizeof(state70), &count);
                            }
                            printf("Character-list handler started: state+28=0x%08lX state+70=%u.\n",
                                   state28, state70);
                        } else if (address == base + 0x34EF91) {
                            puts("Character-list handler finished character iteration.");
                        } else if (address == base + 0x34F1DE) {
                            puts("Character-list handler completed normally.");
                        } else {
                            DWORD globals[3] = {}, cached[2] = {}, args[8] = {};
                            ReadProcessMemory(process, (void *)(base + 0x10926E0), globals, sizeof(globals), &count);
                            ReadProcessMemory(process, (void *)(base + 0x109B524), cached, sizeof(cached), &count);
                            ReadProcessMemory(process, (void *)context.Esp, args, sizeof(args), &count);
                            printf("Character dispatch RVA=%08lX eax=%08lX ecx=%08lX edx=%08lX esi=%08lX cached=%08lX/%08lX gom=%08lX script=%08lX args=%08lX %08lX %08lX %08lX %08lX %08lX\n", (DWORD)(address-base), context.Eax, context.Ecx, context.Edx, context.Esi, cached[0], cached[1], globals[0], globals[1], args[0], args[1], args[2], args[3], args[4], args[5]);
                        }
                        fflush(stdout);
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    DWORD platformOffset = (DWORD)(address - base);
                    if (platformOffset == 0x4C3F1F || platformOffset == 0x4C3F25 ||
                        platformOffset == 0x4C3FCB || platformOffset == 0x4C3FD1 ||
                        platformOffset == 0x4C4010 || platformOffset == 0x4C4016 ||
                        platformOffset == 0x4C4067 || platformOffset == 0x4C406D ||
                        platformOffset == 0x4C41CB || platformOffset == 0x4C41D1) {
                        DWORD callArgs[8] = {}; SIZE_T count = 0;
                        ReadProcessMemory(process, (void *)(context.Esp + 4), callArgs, sizeof(callArgs), &count);
                        if (platformOffset == 0x4C3F1F)
                            printf("Platform request: parsing URL '%s'.\n", readRemoteWide(process, callArgs[0]).c_str());
                        else if (platformOffset == 0x4C3F25)
                            printf("Platform request: URL parse returned 0x%08lX.\n", context.Eax);
                        else if (platformOffset == 0x4C3FCB)
                            puts("Platform request: opening WinINet session.");
                        else if (platformOffset == 0x4C3FD1)
                            printf("Platform request: WinINet session returned 0x%08lX.\n", context.Eax);
                        else if (platformOffset == 0x4C4010)
                            printf("Platform request: connecting to '%s' on port %lu.\n",
                                   readRemoteWide(process, callArgs[1]).c_str(), callArgs[2]);
                        else if (platformOffset == 0x4C4016)
                            printf("Platform request: connection handle returned 0x%08lX.\n", context.Eax);
                        else if (platformOffset == 0x4C4067)
                            printf("Platform request: opening HTTP object '%s'.\n",
                                   readRemoteWide(process, callArgs[2]).c_str());
                        else if (platformOffset == 0x4C406D)
                            printf("Platform request: HTTP object returned 0x%08lX.\n", context.Eax);
                        else if (platformOffset == 0x4C41CB)
                            puts("Platform request: sending HTTPS request.");
                        else if (platformOffset == 0x4C41D1)
                            printf("Platform request: send returned 0x%08lX.\n", context.Eax);
                        fflush(stdout);
                        BYTE old = probes[event.dwProcessId][address];
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    if(address == base+0x24A3E0) {
                        SIZE_T count=0; DWORD frame[5]={};
                        ReadProcessMemory(process,(void *)context.Esp,frame,sizeof(frame),&count);
                        printf("Repository packet dispatch: opcode=%08lX owner=%08lX\n",frame[2],context.Ecx); fflush(stdout);
                        BYTE old=probes[event.dwProcessId][address];
                        WriteProcessMemory(process,(void *)address,&old,1,&count);
                        FlushInstructionCache(process,(void *)address,1);
                        context.Eip=(DWORD)address; context.EFlags |= 0x100;
                        pending[event.dwThreadId]=address;
                        SetThreadContext(thread,&context); CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE); continue;
                    }
                    if(address == base+0x23F810 || address == base+0x746600) {
                        SIZE_T count=0;
                        reportStartup(address == base+0x23F810
                            ? "[READY] Native client received repository synchronization reply."
                            : "[READY] Native repository synchronization completion callback entered.");
                        BYTE old=probes[event.dwProcessId][address];
                        WriteProcessMemory(process,(void *)address,&old,1,&count);
                        FlushInstructionCache(process,(void *)address,1);
                        context.Eip=(DWORD)address; context.EFlags |= 0x100;
                        pending[event.dwThreadId]=address;
                        SetThreadContext(thread,&context); CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE); continue;
                    }
                    if(address == base+0x745CF0 || address == base+0x7461FB) {
                        SIZE_T count=0; DWORD owner=address==base+0x745CF0?context.Ecx:context.Edi;
                        DWORD state=0,queued=0;
                        ReadProcessMemory(process,(void *)(owner+0x14),&state,4,&count);
                        ReadProcessMemory(process,(void *)(owner+0x2E8),&queued,4,&count);
                        static std::map<DWORD_PTR,ULONGLONG> lastQueueTrace;
                        if(!lastQueueTrace.count(address) || GetTickCount64()-lastQueueTrace[address]>=30000) {
                            lastQueueTrace[address]=GetTickCount64();
                            printf("Resource worker RVA=%08lX thread=%lu owner=%08lX state=%lu queued=%lu\n",(DWORD)(address-base),event.dwThreadId,owner,state,queued); fflush(stdout);
                        }
                        BYTE old=probes[event.dwProcessId][address];
                        WriteProcessMemory(process,(void *)address,&old,1,&count);
                        FlushInstructionCache(process,(void *)address,1);
                        context.Eip=(DWORD)address; context.EFlags |= 0x100;
                        pending[event.dwThreadId]=address;
                        SetThreadContext(thread,&context); CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE); continue;
                    }
                    if (address == base + 0x3B0E3A || address == base + 0x3B0E3C || address == base + 0x3B1E90) {
                        SIZE_T count=0;
                        DWORD pathAddress=0, frame[6]={}; char path[512]={};
                        ReadProcessMemory(process,(void *)context.Esp,frame,sizeof(frame),&count);
                        if(address != base + 0x3B1E90) {
                            ReadProcessMemory(process,(void *)(context.Ebp-0x3C),&pathAddress,4,&count);
                            ReadProcessMemory(process,(void *)pathAddress,path,sizeof(path)-1,&count);
                        }
                        printf("Asset delivery RVA=%08lX path=%s target=%08lX result=%08lX stack=%08lX,%08lX,%08lX,%08lX,%08lX,%08lX\n",
                               (DWORD)(address-base),path,context.Edx,context.Eax,frame[0],frame[1],frame[2],frame[3],frame[4],frame[5]);
                        fflush(stdout);
                        if(address == base+0x3B0E3A && strcmp(path,"/art/dynamic/spec/petmouse.dat")==0) {
                            DWORD owner=0, status=0, queued=0;
                            ReadProcessMemory(process,(void *)(context.Ecx+4),&owner,4,&count);
                            ReadProcessMemory(process,(void *)(owner+0x14),&status,4,&count);
                            ReadProcessMemory(process,(void *)(owner+0x2E8),&queued,4,&count);
                            printf("Petmouse request adapter=%08lX manager=%08lX state=%lu queued=%lu\n",context.Ecx,owner,status,queued); fflush(stdout);
                        }
                        if(GetEnvironmentVariableA("SWTOR_TEST_PETMOUSE",NULL,0) && address == base+0x3B0E3C && context.Eax==1 &&
                           strcmp(path,"/art/dynamic/spec/petmouse.dat")==0) {
                            DWORD entry=0, ids[2]={};
                            ReadProcessMemory(process,(void *)(context.Ebp-0x14),&entry,4,&count);
                            if(entry && ReadProcessMemory(process,(void *)(entry+0x10),ids,sizeof(ids),&count)) {
                                std::string data=readFile(resourceCache+path);
                                CONTEXT caller=context; BYTE *allocation=0; DWORD_PTR returned=0;
                                if(!data.empty() && startRepositoryCallback(process,data,path,base+0x3B1E90,0,context,allocation,returned)) {
                                    BYTE *result=allocation+data.size()+strlen(path)+1;
                                    WriteProcessMemory(process,result+8,ids,sizeof(ids),&count);
                                    specCallers[event.dwProcessId][returned]=caller;
                                    probes[event.dwProcessId][returned]=0xC3;
                                    reportStartup("[TEST] Delivering cached petmouse.dat through native resource callback with original request ID.");
                                    SetThreadContext(thread,&context); CloseHandle(thread);
                                    ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE);
                                    continue;
                                }
                            }
                        }
                        BYTE old=probes[event.dwProcessId][address];
                        WriteProcessMemory(process,(void *)address,&old,1,&count);
                        FlushInstructionCache(process,(void *)address,1);
                        context.Eip=(DWORD)address; context.EFlags |= 0x100;
                        pending[event.dwThreadId]=address;
                        SetThreadContext(thread,&context); CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x773040 || address == base + 0x7730BC ||
                        address == base + 0x7C01B0) {
                        SIZE_T count=0;
                        DWORD owner=address == base + 0x7730BC ? context.Esi : context.Ecx;
                        DWORD vtable=0, state=0, frame[3]={};
                        ReadProcessMemory(process,(void *)owner,&vtable,4,&count);
                        if(vtable == base + 0xCC31E4) {
                            ReadProcessMemory(process,(void *)(owner+0xC),&state,4,&count);
                            ReadProcessMemory(process,(void *)context.Esp,frame,sizeof(frame),&count);
                            printf("Character-spec pipeline RVA=%08lX owner=%08lX state=%lu return=%08lX args=%08lX,%08lX result=%08lX\n",
                                   (DWORD)(address-base),owner,state,frame[0],frame[1],frame[2],context.Eax);
                            fflush(stdout);
                        }
                        BYTE old=probes[event.dwProcessId][address];
                        WriteProcessMemory(process,(void *)address,&old,1,&count);
                        FlushInstructionCache(process,(void *)address,1);
                        context.Eip=(DWORD)address; context.EFlags |= 0x100;
                        pending[event.dwThreadId]=address;
                        SetThreadContext(thread,&context); CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x7BFD34) {
                        SIZE_T count=0;
                        DWORD destination=0, textAddress=0;
                        ReadProcessMemory(process,(void *)(context.Ebp+8),&destination,4,&count);
                        ReadProcessMemory(process,(void *)destination,&textAddress,4,&count);
                        char path[512]={};
                        ReadProcessMemory(process,(void *)textAddress,path,sizeof(path)-1,&count);
                        printf("Character-spec resource path: %s\n",path); fflush(stdout);
                        BYTE old=probes[event.dwProcessId][address];
                        WriteProcessMemory(process,(void *)address,&old,1,&count);
                        FlushInstructionCache(process,(void *)address,1);
                        context.Eip=(DWORD)address; context.EFlags |= 0x100;
                        pending[event.dwThreadId]=address;
                        SetThreadContext(thread,&context); CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE);
                        continue;
                    }
                    if (address == base + 0x3EB4A0 || address == base + 0x7261E0 ||
                        address == base + 0x738490 || address == base + 0x712CD7) {
                        SIZE_T count = 0;
                        DWORD frame[3] = {}, vtable = 0;
                        ReadProcessMemory(process, (void *)context.Esp, frame, sizeof(frame), &count);
                        ReadProcessMemory(process, (void *)context.Ecx, &vtable, 4, &count);
                        if (address == base + 0x712CD7) {
                            BYTE disabled = 0;
                            ReadProcessMemory(process, (void *)(context.Esi + 0x224), &disabled, 1, &count);
                            printf("GUI constructor owner=%08lX disabled=%u.\n", context.Esi, disabled);
                        } else if (address == base + 0x3EB4A0) {
                            if (vtable == base + 0xCB66D4 || vtable == base + 0xCB9694) {
                                DWORD path = 0;
                                ReadProcessMemory(process, (void *)frame[1], &path, 4, &count);
                                printf("GUI resource requested: %s owner=%08lX.\n", readRemoteWide(process,path).c_str(), context.Ecx);
                            }
                        } else {
                            DWORD result[15] = {};
                            char path[512] = {};
                            ReadProcessMemory(process, (void *)frame[1], result, sizeof(result), &count);
                            ReadProcessMemory(process, (void *)result[10], path, sizeof(path)-1, &count);
                            printf("GUI resource callback RVA=%08lX result=%08lX bytes=%lu path=%s.\n",
                                   (DWORD)(address-base), result[0], result[6], path);
                        }
                        fflush(stdout);
                        BYTE old = probes[event.dwProcessId][address];
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        context.Eip = (DWORD)address;
                        context.EFlags |= 0x100;
                        pending[event.dwThreadId] = address;
                        SetThreadContext(thread, &context);
                        CloseHandle(thread);
                        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, DBG_CONTINUE);
                        continue;
                    }
                    DWORD request[2] = {}; DWORD args[5] = {}; SIZE_T count = 0;
                    ReadProcessMemory(process, (void *)context.Esi, request, sizeof(request), &count);
                    ReadProcessMemory(process, (void *)context.Esp, args, sizeof(args), &count);
                    char pathBuffer[512] = {};
                    ReadProcessMemory(process, (void *)request[1], pathBuffer, sizeof(pathBuffer) - 1, &count);
                    std::string path(pathBuffer), supplied;
                    if (address == readBreakpoint[event.dwProcessId] && !path.empty() && path != lastRequested) {
                        lastRequested = path;
                        lastActivityAt = GetTickCount64();
                    }
                    if (path.find("/world/") == 0) bootstrapComplete = true;
                    if (path == "/systemgenerated/client.gom") supplied = gom;
                    else if ((path.find("/systemgenerated/") == 0 ||
                              path == "/world/livecontent/systemgenerated/3758002374/area.dat" ||
                              path == "/art/defaultassets/missing_material_d.tex" ||
                              path == "/art/defaultassets/missing_material_d.dds") &&
                             path.find("..") == std::string::npos && path.find(':') == std::string::npos) {
                        // Only files we explicitly decoded into the workspace cache can be supplied.
                        supplied = readFile(resourceCache + path);
                    }

                    BYTE old = probes[event.dwProcessId][address];
                    WriteProcessMemory(process, (void *)address, &old, 1, &count);
                    FlushInstructionCache(process, (void *)address, 1);
                    context.Eip = (DWORD)address;
                    bool compatibleLength = supplied.size() == args[2] ||
                        (path == "/systemgenerated/client.gom" && args[2] == 514980) ||
                        path == "/systemgenerated/buckets.info";
                    if (address == readBreakpoint[event.dwProcessId] && !supplied.empty() && compatibleLength) {
                        SIZE_T wrote = 0;
                        if (WriteProcessMemory(process, (void *)args[1], supplied.data(), supplied.size(), &wrote) && wrote == supplied.size()) {
                            DWORD actual = (DWORD)supplied.size();
                            WriteProcessMemory(process, (void *)(context.Ebp - 0x70), &actual, 4, &count);
                            context.Eax = 0;
                            context.Esp += 20;
                            context.Eip += 5;
                            ++suppliedCount;
                            lastSupplied = path;
                            lastActivityAt = GetTickCount64();
                            if (suppliedCount % 25 == 0 || path.find("scriptdef.list") != std::string::npos || path.find("/world/") == 0) {
                                printf("Loaded %u compatibility resources; current: %s\n", suppliedCount, path.c_str());
                                fflush(stdout);
                            }
                            if (path.find("/world/") == 0)
                                areaSuppliedAt = GetTickCount64();
                            if (path.find("/world/") == 0)
                                for (std::map<DWORD, HANDLE>::const_iterator it = processes.begin(); it != processes.end(); ++it)
                                    EnumWindows(revealGameWindow, it->first);
                        }
                    }
                    context.EFlags |= 0x100;
                    pending[event.dwThreadId] = address;
                    SetThreadContext(thread, &context);
                }
                if (thread) CloseHandle(thread);
            } else if (code == EXCEPTION_SINGLE_STEP && pending.count(event.dwThreadId)) {
                DWORD_PTR addressToRestore = pending[event.dwThreadId]; BYTE trap = 0xCC; SIZE_T count = 0;
                WriteProcessMemory(process, (void *)addressToRestore, &trap, 1, &count);
                FlushInstructionCache(process, (void *)addressToRestore, 1);
                HANDLE thread = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT, FALSE, event.dwThreadId);
                CONTEXT context = {}; context.ContextFlags = CONTEXT_CONTROL;
                if (thread && GetThreadContext(thread, &context)) {
                    context.EFlags &= ~0x100;
                    SetThreadContext(thread, &context);
                }
                if (thread) CloseHandle(thread);
                pending.erase(event.dwThreadId);
            } else if (code != EXCEPTION_BREAKPOINT && code != 0x4000001f) {
                disposition = DBG_EXCEPTION_NOT_HANDLED;
                if (worldTravelStarted && code == 0xE06D7363 && event.u.Exception.ExceptionRecord.NumberParameters >= 3) {
                    DWORD info=(DWORD)event.u.Exception.ExceptionRecord.ExceptionInformation[2], array=0, entry=0, type=0;
                    SIZE_T count=0; char name[256]={};
                    ReadProcessMemory(process,(void*)(info+12),&array,4,&count);
                    ReadProcessMemory(process,(void*)(array+4),&entry,4,&count);
                    ReadProcessMemory(process,(void*)(entry+4),&type,4,&count);
                    ReadProcessMemory(process,(void*)(type+8),name,255,&count);
                    printf("World-entry C++ exception firstChance=%lu type=%s\n",event.u.Exception.dwFirstChance,name);
                    HANDLE traceThread=OpenThread(THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,event.dwThreadId);
                    CONTEXT trace={}; trace.ContextFlags=CONTEXT_FULL;
                    if(traceThread && GetThreadContext(traceThread,&trace)) {
                        if (strcmp(name, ".?AVSerializationException@G@@") == 0)
                            captureWorldEntryException(process, event, trace);
                        // Reports the frame list and, for any frame whose arguments
                        // are a validated style-7 reader, that reader's cursor and
                        // exact bytes.
                        reportWorldEntryStack(process, traceThread, trace);
                    }
                    if(traceThread) CloseHandle(traceThread);
                    fflush(stdout);
                } else if (worldTravelStarted && code == 0xC0000005) {
                    // The observed world-entry failures after the CRT fixtures were
                    // corrected are access violations, not C++ exceptions. They
                    // previously produced no dump and no reader state at all, which
                    // left the run undiagnosable. Capture both here.
                    printf("World-entry access violation firstChance=%lu address=0x%08lX\n",
                           event.u.Exception.dwFirstChance, (DWORD)address);
                    HANDLE avThread = OpenThread(THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,event.dwThreadId);
                    CONTEXT av = {}; av.ContextFlags = CONTEXT_FULL;
                    if (avThread && GetThreadContext(avThread, &av)) {
                        captureWorldEntryException(process, event, av);
                        reportWorldEntryStack(process, avThread, av);
                    }
                    if (avThread) CloseHandle(avThread);
                    fflush(stdout);
                }
                if (!event.u.Exception.dwFirstChance) {
                    DWORD_PTR base = imageBases[event.dwProcessId];
                    printf("Client stopped with exception 0x%08lX at 0x%08lX (rva 0x%08lX).\n",
                           code, (DWORD)address,
                           address >= base && address < base + 0x02000000
                               ? (DWORD)(address - base) : 0xFFFFFFFF);
                    HANDLE failedThread = OpenThread(THREAD_GET_CONTEXT, FALSE, event.dwThreadId);
                    CONTEXT failed = {}; failed.ContextFlags = CONTEXT_FULL;
                    if (failedThread && GetThreadContext(failedThread, &failed))
                        printf("  registers: eax=%08lX ebx=%08lX ecx=%08lX edx=%08lX esi=%08lX edi=%08lX ebp=%08lX esp=%08lX\n",
                               failed.Eax, failed.Ebx, failed.Ecx, failed.Edx, failed.Esi,
                               failed.Edi, failed.Ebp, failed.Esp);
                    if (failedThread) CloseHandle(failedThread);
                    fflush(stdout);
                }
            }
        } else if (event.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT) {
            printf("Client process exited with code 0x%08lX after %u bridged resource reads.\n",
                   event.u.ExitProcess.dwExitCode, suppliedCount);
            if (process) CloseHandle(process);
            processes.erase(event.dwProcessId);
            lastActivityAt = GetTickCount64();
            if (processes.empty()) done = true;
        }
        // The legacy bootstrap races its hook setup across two processes.  The
        // original diagnostic's symbol work incidentally provided this pause.
        if (!bootstrapComplete) Sleep(10);
        ContinueDebugEvent(event.dwProcessId, event.dwThreadId, disposition);
    }
    if (!done) {
        printf("Test timeout reached after %u bridged resource reads.\n", suppliedCount);
        printf("Last supplied resource: %s\nLast requested resource: %s\n", lastSupplied.c_str(), lastRequested.c_str());
        for (auto &item : processes) {
            TerminateProcess(item.second, 99);
            CloseHandle(item.second);
        }
    }
    if (done && suppliedCount < 500) {
        puts("The legacy Nexus bootstrap exited early; retry is required.");
        return 10;
    }
    return 0;
}
