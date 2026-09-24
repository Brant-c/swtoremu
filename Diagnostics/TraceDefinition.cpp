#include <windows.h>
#include <dbghelp.h>
#include <stdio.h>
#include <string>
#include <map>
#include <fstream>
#include <iterator>
struct Module { DWORD size; std::string path; };
static bool captured=false;
static void DialogStack(HWND window) {
 if(captured) return;
 char title[128]={}; GetWindowTextA(window,title,128); if(std::string(title)!="SWTOR") return;
 captured=true;
 DWORD pid=0; DWORD tid=GetWindowThreadProcessId(window,&pid);
 HANDLE p=OpenProcess(PROCESS_ALL_ACCESS,FALSE,pid), t=OpenThread(THREAD_ALL_ACCESS,FALSE,tid);
 if(!p||!t) return;
 SuspendThread(t); CONTEXT c={}; c.ContextFlags=CONTEXT_FULL;
 if(GetThreadContext(t,&c)) {
 SymInitialize(p,NULL,TRUE); STACKFRAME64 f={}; f.AddrPC.Offset=c.Eip; f.AddrPC.Mode=AddrModeFlat; f.AddrFrame.Offset=c.Ebp; f.AddrFrame.Mode=AddrModeFlat; f.AddrStack.Offset=c.Esp; f.AddrStack.Mode=AddrModeFlat;
 for(int i=0;i<35;i++) {
 if(!StackWalk64(IMAGE_FILE_MACHINE_I386,p,t,&f,&c,NULL,SymFunctionTableAccess64,SymGetModuleBase64,NULL)) break;
 IMAGEHLP_MODULE64 m={}; m.SizeOfStruct=sizeof(m); SymGetModuleInfo64(p,f.AddrPC.Offset,&m);
 printf("DIALOG STACK %s + 0x%lX\n",m.ImageName,(DWORD)(f.AddrPC.Offset-m.BaseOfImage));
 }
 SymCleanup(p);
 }
 ResumeThread(t); CloseHandle(t); CloseHandle(p);
}
static BOOL CALLBACK ChildText(HWND window, LPARAM) {
 char text[2048]={}; GetWindowTextA(window,text,sizeof(text));
 if(text[0]) printf("DIALOG TEXT: %s\n",text);
 return TRUE;
}
static BOOL CALLBACK WindowText(HWND window, LPARAM pid) {
 DWORD owner=0; GetWindowThreadProcessId(window,&owner);
 if(owner==(DWORD)pid && IsWindowVisible(window)) { DialogStack(window); ChildText(window,0); EnumChildWindows(window,ChildText,0); }
 return TRUE;
}
int main(int argc, char** argv) {
 if (argc != 2) return 2;
 std::string dir = argv[1]; std::ifstream gf("GomCompatibility/client.gom", std::ios::binary); std::string gom((std::istreambuf_iterator<char>(gf)),std::istreambuf_iterator<char>()); if(gom.size()!=921724) { puts("Missing verified GOM input"); return 5; }
 std::ifstream input(dir + "\\go1.bat");
 std::string command((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
 while (!command.empty() && (command.back()=='\r' || command.back()=='\n')) command.pop_back();
 if (command.empty()) return 3;
 STARTUPINFOA si = {}; si.cb=sizeof(si); PROCESS_INFORMATION pi={};
 si.dwFlags=STARTF_USESHOWWINDOW; si.wShowWindow=SW_HIDE;
 if (!CreateProcessA((dir + "\\swtor-emu.exe").c_str(), &command[0], NULL,NULL,FALSE,DEBUG_PROCESS,NULL,dir.c_str(),&si,&pi)) { printf("CreateProcess error %lu\n",GetLastError()); return 4; }
 CloseHandle(pi.hThread); CloseHandle(pi.hProcess);
 std::map<DWORD,DWORD_PTR> pending; std::map<DWORD,HANDLE> processes; std::map<DWORD,std::map<DWORD_PTR,BYTE>> probes;
 std::map<DWORD,std::map<DWORD_PTR,Module>> modules;
 ULONGLONG start=GetTickCount64(); bool done=false;
 while (!done && GetTickCount64()-start < 45000) {
  DEBUG_EVENT ev={}; if (!WaitForDebugEvent(&ev,500)) { for(auto &p:processes) EnumWindows(WindowText,p.first); fflush(stdout); continue; }
  DWORD status=DBG_CONTINUE;
  if (ev.dwDebugEventCode==CREATE_PROCESS_DEBUG_EVENT || ev.dwDebugEventCode==LOAD_DLL_DEBUG_EVENT) {
   HANDLE file; LPVOID base;
   if (ev.dwDebugEventCode==CREATE_PROCESS_DEBUG_EVENT) { processes[ev.dwProcessId]=ev.u.CreateProcessInfo.hProcess; CloseHandle(ev.u.CreateProcessInfo.hThread); file=ev.u.CreateProcessInfo.hFile; base=ev.u.CreateProcessInfo.lpBaseOfImage; printf("PROCESS %lu\n",ev.dwProcessId); }
   else {file=ev.u.LoadDll.hFile; base=ev.u.LoadDll.lpBaseOfDll;}
   char path[2048]={}; if(file) GetFinalPathNameByHandleA(file,path,sizeof(path),0);
   IMAGE_DOS_HEADER dos={}; IMAGE_NT_HEADERS32 nt={}; SIZE_T read=0;
   ReadProcessMemory(processes[ev.dwProcessId],base,&dos,sizeof(dos),&read);
   ReadProcessMemory(processes[ev.dwProcessId],(BYTE*)base+dos.e_lfanew,&nt,sizeof(nt),&read);
   modules[ev.dwProcessId][(DWORD_PTR)base]={nt.OptionalHeader.SizeOfImage,path};
   if(ev.dwDebugEventCode==CREATE_PROCESS_DEBUG_EVENT) { DWORD offsets[]={0x742624,0x573950,0x0a2814,0x42d371}; for(auto off:offsets) { DWORD_PTR a=(DWORD_PTR)base+off; BYTE old=0, trap=0xcc; SIZE_T n; ReadProcessMemory(processes[ev.dwProcessId],(void*)a,&old,1,&n); probes[ev.dwProcessId][a]=old; WriteProcessMemory(processes[ev.dwProcessId],(void*)a,&trap,1,&n); FlushInstructionCache(processes[ev.dwProcessId],(void*)a,1); } }
   if(file) CloseHandle(file);
  } else if(ev.dwDebugEventCode==CREATE_THREAD_DEBUG_EVENT) CloseHandle(ev.u.CreateThread.hThread);
  else if(ev.dwDebugEventCode==UNLOAD_DLL_DEBUG_EVENT) modules[ev.dwProcessId].erase((DWORD_PTR)ev.u.UnloadDll.lpBaseOfDll);
  else if(ev.dwDebugEventCode==EXCEPTION_DEBUG_EVENT) {
   DWORD code=ev.u.Exception.ExceptionRecord.ExceptionCode; DWORD_PTR address=(DWORD_PTR)ev.u.Exception.ExceptionRecord.ExceptionAddress;
   if(code==EXCEPTION_BREAKPOINT && probes[ev.dwProcessId].count(address)) { HANDLE th=OpenThread(THREAD_ALL_ACCESS,FALSE,ev.dwThreadId); CONTEXT cx={}; cx.ContextFlags=CONTEXT_FULL; GetThreadContext(th,&cx);
DWORD rva=0; for(auto &m:modules[ev.dwProcessId]) if(address>=m.first && address<m.first+m.second.size) rva=(DWORD)(address-m.first);
if(rva==0x573950 || rva==0xa2814) {
 SIZE_T nr=0;
 if(rva==0x573950) {
 DWORD len=0; ReadProcessMemory(processes[ev.dwProcessId],(void*)cx.Ecx,&len,4,&nr);
 if(len>=32 && len<1048576) { std::string data(len,'\0'); if(ReadProcessMemory(processes[ev.dwProcessId],(void*)cx.Ecx,&data[0],len,&nr) && nr==len) { std::ofstream out("GomCompatibility/last-runtime-field.bin",std::ios::binary); out.write(data.data(),len); unsigned short nameOff=*(unsigned short*)(data.data()+20), typeOff=*(unsigned short*)(data.data()+28), typeLen=*(unsigned short*)(data.data()+26); unsigned long long id=*(unsigned long long*)(data.data()+8); printf("FIELD id=%llu size=%lu typeOffset=%u typeLength=%u typeByte=%u name=%s\n",id,len,typeOff,typeLen,typeOff<len?(unsigned char)data[typeOff]:255,nameOff<len?data.c_str()+nameOff:"INVALID"); } }
 } else { printf("INVALID TYPE BYTE=%u EAX=%08lX\n",(unsigned)(cx.Eax&255),cx.Eax); }
 BYTE old=probes[ev.dwProcessId][address]; WriteProcessMemory(processes[ev.dwProcessId],(void*)address,&old,1,&nr); FlushInstructionCache(processes[ev.dwProcessId],(void*)address,1); cx.Eip=(DWORD)address; cx.EFlags|=0x100; pending[ev.dwThreadId]=address; SetThreadContext(th,&cx); CloseHandle(th); ContinueDebugEvent(ev.dwProcessId,ev.dwThreadId,DBG_CONTINUE); fflush(stdout); continue;
} printf("ORIGIN REG EAX=%08lX EBX=%08lX ECX=%08lX EDX=%08lX ESI=%08lX EDI=%08lX EBP=%08lX ESP=%08lX\n",cx.Eax,cx.Ebx,cx.Ecx,cx.Edx,cx.Esi,cx.Edi,cx.Ebp,cx.Esp); DWORD record[20]={}; SIZE_T rn=0; ReadProcessMemory(processes[ev.dwProcessId],(void*)cx.Esi,record,sizeof(record),&rn); for(int j=0;j<20;j++) printf("REQUEST[%02X]=%08lX\n",j*4,record[j]); DWORD frameargs[7]={}; ReadProcessMemory(processes[ev.dwProcessId],(void*)(cx.Ebp+8),frameargs,sizeof(frameargs),&rn); for(int j=0;j<7;j++) printf("FRAME[%d]=%08lX\n",j,frameargs[j]); char requested[256]={}; ReadProcessMemory(processes[ev.dwProcessId],(void*)record[1],requested,255,&rn); printf("REQUEST PATH: %s\n",requested); DWORD obj[16]={}; SIZE_T nr=0; ReadProcessMemory(processes[ev.dwProcessId],(void*)cx.Edi,obj,sizeof(obj),&nr); DWORD msgptr=0; ReadProcessMemory(processes[ev.dwProcessId],(void*)cx.Eax,&msgptr,4,&nr); char msg[1024]={}; ReadProcessMemory(processes[ev.dwProcessId],(void*)msgptr,msg,1023,&nr); printf("RESOURCE FAILURE at=%08lX status=%08lX EAX=%08lX detail=%s\n",(DWORD)address,obj[0],cx.Eax,msg); char path[1024]={}; ReadProcessMemory(processes[ev.dwProcessId],(void*)obj[10],path,1023,&nr); printf("RESOURCE NAME: %s\n",path); DWORD args[12]={}; SIZE_T got=0; HANDLE process=processes[ev.dwProcessId];
 ReadProcessMemory(process,(void*)cx.Esp,args,sizeof(args),&got);
 for(int k=0;k<6;k++) { printf("ARG[%d]=%08lX\n",k,args[k]); } for(auto &m:modules[ev.dwProcessId]) if(cx.Eax>=m.first && cx.Eax<m.first+m.second.size) printf("TARGET %s + 0x%lX\n",m.second.path.c_str(),(DWORD)(cx.Eax-m.first)); printf("CLIENT ERROR REPORT pid=%lu code=%lu caller=%08lX ECX=%08lX EAX=%08lX\n",ev.dwProcessId,args[1],args[0],cx.Ecx,cx.Eax);
 for(auto &m:modules[ev.dwProcessId]) if(args[0]>=m.first && args[0]<m.first+m.second.size) printf("ERROR CALLER %s + 0x%lX\n",m.second.path.c_str(),(DWORD)(args[0]-m.first));
 SymInitialize(process,NULL,TRUE); CONTEXT walk=cx; STACKFRAME64 frame={};
 frame.AddrPC.Offset=walk.Eip; frame.AddrPC.Mode=AddrModeFlat; frame.AddrFrame.Offset=walk.Ebp; frame.AddrFrame.Mode=AddrModeFlat; frame.AddrStack.Offset=walk.Esp; frame.AddrStack.Mode=AddrModeFlat;
 for(int i=0;i<25;i++) { if(!StackWalk64(IMAGE_FILE_MACHINE_I386,process,th,&frame,&walk,NULL,SymFunctionTableAccess64,SymGetModuleBase64,NULL)) break;
 for(auto &m:modules[ev.dwProcessId]) if(frame.AddrPC.Offset>=m.first && frame.AddrPC.Offset<m.first+m.second.size) printf("ERROR STACK %s + 0x%lX\n",m.second.path.c_str(),(DWORD)(frame.AddrPC.Offset-m.first)); }
 SymCleanup(process);
 BYTE old=probes[ev.dwProcessId][address]; SIZE_T n; WriteProcessMemory(processes[ev.dwProcessId],(void*)address,&old,1,&n); FlushInstructionCache(processes[ev.dwProcessId],(void*)address,1); cx.Eip=(DWORD)address; bool atRead=false; for(auto &m:modules[ev.dwProcessId]) if(address-m.first==0x742624) atRead=true; if(atRead && std::string(requested)=="/systemgenerated/client.gom" && args[2]==gom.size()) { SIZE_T wrote=0; if(WriteProcessMemory(process,(void*)args[1],gom.data(),gom.size(),&wrote) && wrote==gom.size()) { cx.Eax=0; cx.Esp+=20; cx.Eip+=5; puts("GOM OVERRIDE: supplied exact decoded retail bytes for this process only"); } else { puts("GOM OVERRIDE failed; original read retained"); } } cx.EFlags|=0x100; pending[ev.dwThreadId]=address; SetThreadContext(th,&cx); CloseHandle(th);  }
   if(code==EXCEPTION_SINGLE_STEP && pending.count(ev.dwThreadId)) { DWORD_PTR bp=pending[ev.dwThreadId]; BYTE trap=0xcc; SIZE_T nr=0; WriteProcessMemory(processes[ev.dwProcessId],(void*)bp,&trap,1,&nr); FlushInstructionCache(processes[ev.dwProcessId],(void*)bp,1); pending.erase(ev.dwThreadId); } else if(code!=EXCEPTION_BREAKPOINT && code!=0x4000001f) {
    printf("EXCEPTION pid=%lu code=0x%08lX firstChance=%lu address=0x%08lX\n",ev.dwProcessId,code,ev.u.Exception.dwFirstChance,(DWORD)address);
    for(auto &m:modules[ev.dwProcessId]) if(address>=m.first && address<m.first+m.second.size) printf("MODULE %s + 0x%lX\n",m.second.path.c_str(),(DWORD)(address-m.first));
    if(code==0xE06D7363 && ev.u.Exception.ExceptionRecord.NumberParameters>=3) {
    DWORD info=(DWORD)ev.u.Exception.ExceptionRecord.ExceptionInformation[2], array=0, entry=0, type=0; SIZE_T count=0; char name[256]={};
    ReadProcessMemory(processes[ev.dwProcessId],(void*)(info+12),&array,4,&count);
    ReadProcessMemory(processes[ev.dwProcessId],(void*)(array+4),&entry,4,&count);
    ReadProcessMemory(processes[ev.dwProcessId],(void*)(entry+4),&type,4,&count);
    ReadProcessMemory(processes[ev.dwProcessId],(void*)(type+8),name,255,&count);
    printf("CPP TYPE: %s\n",name); if(std::string(name)==".?AVOString@omega@@") { DWORD op=(DWORD)ev.u.Exception.ExceptionRecord.ExceptionInformation[1]; DWORD words[4]={}; SIZE_T nr=0; ReadProcessMemory(processes[ev.dwProcessId],(void*)op,words,sizeof(words),&nr); for(int j=0;j<4;j++) { char txt[1024]={}; ReadProcessMemory(processes[ev.dwProcessId],(void*)words[j],txt,1023,&nr); printf("OSTRING[%d] ptr=%08lX text=%s\n",j,words[j],txt); } }
    HANDLE thread=OpenThread(THREAD_GET_CONTEXT|THREAD_QUERY_INFORMATION,FALSE,ev.dwThreadId);
    CONTEXT ctx={}; ctx.ContextFlags=CONTEXT_FULL;
    if(thread && GetThreadContext(thread,&ctx)) {
      HANDLE process=processes[ev.dwProcessId];
      SymSetOptions(SYMOPT_DEFERRED_LOADS|SYMOPT_UNDNAME); SymInitialize(process,NULL,TRUE);
      STACKFRAME64 frame={}; frame.AddrPC.Offset=ctx.Eip; frame.AddrPC.Mode=AddrModeFlat;
      frame.AddrFrame.Offset=ctx.Ebp; frame.AddrFrame.Mode=AddrModeFlat; frame.AddrStack.Offset=ctx.Esp; frame.AddrStack.Mode=AddrModeFlat;
      for(int i=0;i<18;i++) {
        if(!StackWalk64(IMAGE_FILE_MACHINE_I386,process,thread,&frame,&ctx,NULL,SymFunctionTableAccess64,SymGetModuleBase64,NULL)) break;
        for(auto &m:modules[ev.dwProcessId]) if(frame.AddrPC.Offset>=m.first && frame.AddrPC.Offset<m.first+m.second.size) printf("STACK %s + 0x%lX\n",m.second.path.c_str(),(DWORD)(frame.AddrPC.Offset-m.first));
      }
      SymCleanup(process);
    }
    if(thread) CloseHandle(thread);
   }
   if(code==EXCEPTION_ACCESS_VIOLATION) printf("ACCESS operation=%lu address=0x%08lX\n",(DWORD)ev.u.Exception.ExceptionRecord.ExceptionInformation[0],(DWORD)ev.u.Exception.ExceptionRecord.ExceptionInformation[1]);
    status=DBG_EXCEPTION_NOT_HANDLED;
    if(!ev.u.Exception.dwFirstChance) { char name[80]; sprintf_s(name,"client-%lu.dmp",ev.dwProcessId); HANDLE dump=CreateFileA(name,GENERIC_WRITE,0,NULL,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL); if(dump!=INVALID_HANDLE_VALUE) { MiniDumpWriteDump(processes[ev.dwProcessId],ev.dwProcessId,dump,MiniDumpNormal,NULL,NULL,NULL); CloseHandle(dump); } }
   }
  } else if(ev.dwDebugEventCode==EXIT_PROCESS_DEBUG_EVENT) { printf("EXIT pid=%lu code=0x%08lX\n",ev.dwProcessId,ev.u.ExitProcess.dwExitCode); CloseHandle(processes[ev.dwProcessId]); processes.erase(ev.dwProcessId); if(processes.empty()) done=true; }
  ContinueDebugEvent(ev.dwProcessId,ev.dwThreadId,status); fflush(stdout);
 }
 if(!done) { puts("TIMEOUT: ending only processes launched by this diagnostic"); for(auto &p:processes) {TerminateProcess(p.second,99); CloseHandle(p.second);} }
 return 0;
}
















