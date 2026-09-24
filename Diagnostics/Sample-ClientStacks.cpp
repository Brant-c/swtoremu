#include <windows.h>
#include <tlhelp32.h>
#include <dbghelp.h>
#include <stdio.h>
#include <stdlib.h>
// Read-only stack sampling of an already running diagnostic client.
// Each thread is resumed immediately after its context/stack have been read.
int main(int argc, char** argv) {
    if(argc != 2) return 2;
    DWORD pid = strtoul(argv[1], 0, 10);
    HANDLE process = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if(!process) return 3;
    SymSetOptions(SYMOPT_DEFERRED_LOADS | SYMOPT_FAIL_CRITICAL_ERRORS);
    SymInitialize(process, NULL, TRUE);
    HANDLE modules=CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, pid);
    MODULEENTRY32 firstModule={}; firstModule.dwSize=sizeof(firstModule);
    DWORD imageBase=Module32First(modules, &firstModule) ? (DWORD)firstModule.modBaseAddr : 0;
    CloseHandle(modules);
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    THREADENTRY32 entry = {}; entry.dwSize = sizeof(entry);
    if(Thread32First(snapshot, &entry)) do {
        if(entry.th32OwnerProcessID != pid) continue;
        HANDLE thread = OpenThread(THREAD_GET_CONTEXT | THREAD_SUSPEND_RESUME | THREAD_QUERY_INFORMATION, FALSE, entry.th32ThreadID);
        if(!thread) continue;
        if(SuspendThread(thread) == (DWORD)-1) { CloseHandle(thread); continue; }
        CONTEXT context = {}; context.ContextFlags = CONTEXT_FULL;
        if(GetThreadContext(thread, &context)) {
            printf("THREAD %lu EIP=%08lX\n", entry.th32ThreadID, context.Eip);
            if(imageBase && context.Eip >= imageBase && context.Eip < imageBase+0xC00000) {
                printf("  REG EAX=%08lX EBX=%08lX ECX=%08lX EDX=%08lX ESI=%08lX EDI=%08lX EBP=%08lX ESP=%08lX\n", context.Eax,context.Ebx,context.Ecx,context.Edx,context.Esi,context.Edi,context.Ebp,context.Esp);
                DWORD stack[8192]={}; SIZE_T size=0;
                ReadProcessMemory(process,(void*)context.Esp,stack,sizeof(stack),&size);
                for(unsigned i=0;i<size/4;++i) {
                    DWORD rva=stack[i]-imageBase;
                    if(rva>=0x300000 && rva<0x380000)
                        printf("  STACK-CANDIDATE +%04X nativeVA=%08lX\n",i*4,rva+0x400000);
                }
            }
            STACKFRAME64 frame = {};
            frame.AddrPC.Offset=context.Eip; frame.AddrPC.Mode=AddrModeFlat;
            frame.AddrFrame.Offset=context.Ebp; frame.AddrFrame.Mode=AddrModeFlat;
            frame.AddrStack.Offset=context.Esp; frame.AddrStack.Mode=AddrModeFlat;
            for(int n=0; n<30; ++n) {
                if(!StackWalk64(IMAGE_FILE_MACHINE_I386, process, thread, &frame, &context, NULL, SymFunctionTableAccess64, SymGetModuleBase64, NULL)) break;
                IMAGEHLP_MODULE64 module={}; module.SizeOfStruct=sizeof(module);
                SymGetModuleInfo64(process, frame.AddrPC.Offset, &module);
                printf("  %s + %08lX\n", module.ModuleName, (DWORD)(frame.AddrPC.Offset-module.BaseOfImage));
            }
        }
        ResumeThread(thread); CloseHandle(thread);
    } while(Thread32Next(snapshot, &entry));
    CloseHandle(snapshot); SymCleanup(process); CloseHandle(process);
    return 0;
}
