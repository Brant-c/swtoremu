#include <winsock2.h>
#include <windows.h>
#include <iphlpapi.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <fstream>
#include <iterator>
#include <map>
#include <string>
#include <vector>

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
    const SIZE_T callbackSize = 0x2C;
    const SIZE_T allocationSize = data.size() + path.size() + 1 + callbackSize + 1;
    BYTE *remote = (BYTE *)VirtualAllocEx(process, NULL, allocationSize,
                                          MEM_COMMIT | MEM_RESERVE,
                                          PAGE_EXECUTE_READWRITE);
    if (!remote) return false;
    BYTE *remotePath = remote + data.size();
    BYTE *remoteResult = remotePath + path.size() + 1;
    BYTE *remoteReturn = remoteResult + callbackSize;
    DWORD result[11] = {};
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

static BOOL CALLBACK revealGameWindow(HWND window, LPARAM ownerPid) {
    DWORD pid = 0;
    GetWindowThreadProcessId(window, &pid);
    if (pid != (DWORD)ownerPid) return TRUE;
    char title[256] = {};
    GetWindowTextA(window, title, sizeof(title));
    if (strncmp(title, "Star Wars", 9) == 0) ShowWindowAsync(window, SW_SHOW);
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
    const std::string clientDir = argv[1];
    const std::string gom = readFile(toolDir +
        "\\GomCompatibility\\ResourceCache2012\\systemgenerated\\client.gom");
    const std::string bucketList =
        readFile(toolDir + "\\GomCompatibility\\ResourceCache2012\\systemgenerated\\buckets.info");
    const std::string scriptDefinitions =
        readFile(toolDir + "\\GomCompatibility\\ResourceCache2012\\systemgenerated\\scriptdef.list");
    if (gom.size() != 514980) {
        puts("The verified 2012 client.gom is missing or has the wrong size.");
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
    startup.wShowWindow = SW_HIDE;
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
    std::map<DWORD, DWORD_PTR> pending;
    std::map<DWORD, WaitingRepositoryCall> waitingRepositoryCalls;
    std::map<DWORD, DWORD_PTR> releaseAfterShard;
    std::map<DWORD, unsigned> moduleSendCount;
    std::map<DWORD, unsigned> characterRewriteStage;
    std::map<DWORD, unsigned> gomInjectionStage;
    std::map<DWORD, DWORD> gomInjectionThread;
    std::map<DWORD, DWORD_PTR> gomReturnBreakpoint;
    std::map<DWORD, DWORD_PTR> bucketReturnBreakpoint;
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
            std::string data = readFile(toolDir +
                "\\GomCompatibility\\ResourceCache2012\\systemgenerated\\buckets\\" + name);
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
                0x34EDC7, 0x34EF91, 0x34F1DE,
                // Startup-state check after the repository status query.
                0x3AD911, 0x3AD919, 0x3AD94B, 0x3AD952,
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
                    if (address == base + 0x24477F && directShardLaunch && !repositoryAttachBypassed &&
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
                    if (address == base + 0x765BF && directShardLaunch) {
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
                        if (!repositoryResultBypassed && context.Eax != 1) {
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
                        directShardLaunch && repositoryStartupAdvanced) {
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
                            if (startupState == 4 && wrapper && waiting && !total &&
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
                        bool advanced = false;
                        // The archived files do not include the PINF prototype index
                        // required by stage 3. Stage 4 can use the recovered PBCK list
                        // and native bucket loader. Character specs also lack backing data.
                        if ((startupState == 3 || startupState == 6) && context.Eax != 1) {
                            context.Eax = 1;
                            advanced = true;
                        }
                        if (advanced) {
                            puts(startupState == 3
                                     ? "Compatibility startup: skipped the unavailable PINF prototype index."
                                     : "Compatibility startup: completed the unavailable character-spec stage.");
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
                                context.Eax &= 0xFFFFFF00;
                                context.EFlags |= 0x40;
                            }
                            else {
                                context.Eax = (context.Eax & 0xFFFFFF00) | 1;
                                context.EFlags &= ~0x40;
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
                            scriptDefinitionCompleted[event.dwProcessId]) {
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
                    if (address == base + 0x34EDC7 || address == base + 0x34EF91 ||
                        address == base + 0x34F1DE) {
                        BYTE old = probes[event.dwProcessId][address]; SIZE_T count = 0;
                        WriteProcessMemory(process, (void *)address, &old, 1, &count);
                        FlushInstructionCache(process, (void *)address, 1);
                        if (address == base + 0x34EDC7) {
                            DWORD parsedReply = 0;
                            ReadProcessMemory(process, (void *)(context.Ebp + 8), &parsedReply,
                                              sizeof(parsedReply), &count);
                            DWORD accountInfo = 0; BYTE accountPending = 0;
                            if (parsedReply) {
                                ReadProcessMemory(process, (void *)(parsedReply + 0x28), &accountInfo,
                                                  sizeof(accountInfo), &count);
                                ReadProcessMemory(process, (void *)(parsedReply + 0x70), &accountPending,
                                                  sizeof(accountPending), &count);
                                if (accountInfo && accountPending) {
                                    BYTE ready = 0;
                                    WriteProcessMemory(process, (void *)(parsedReply + 0x70), &ready,
                                                       sizeof(ready), &count);
                                    accountPending = ready;
                                    puts("Character account information is present; released the unavailable account-service wait.");
                                }
                            }
                            printf("Character-list handler started: account-info=0x%08lX pending=%u.\n",
                                   accountInfo, accountPending);
                        } else if (address == base + 0x34EF91) {
                            puts("Character-list handler accepted an empty character list.");
                        } else {
                            puts("Character-list handler completed normally.");
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
                        supplied = readFile(toolDir + "\\GomCompatibility\\ResourceCache2012" + path);
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
