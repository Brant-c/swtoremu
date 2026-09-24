from pathlib import Path
p=Path('Diagnostics/TraceClient.cpp');s=p.read_text()
s=s.replace('std::map<DWORD_PTR,BYTE> probes;','std::map<DWORD,std::map<DWORD_PTR,BYTE>> probes;')
s=s.replace('DWORD offsets[]={0x818ec}', 'DWORD offsets[]={0x76800}')
s=s.replace('probes[a]=old','probes[ev.dwProcessId][a]=old')
s=s.replace('probes.count(address)','probes[ev.dwProcessId].count(address)').replace('probes[address]','probes[ev.dwProcessId][address]').replace('probes.erase(address)','probes[ev.dwProcessId].erase(address)')
a=s.index('printf("PROBE address=');b=s.index('BYTE old=probes',a)
s=s[:a]+'''DWORD args[12]={}; SIZE_T got=0; HANDLE process=processes[ev.dwProcessId];
 ReadProcessMemory(process,(void*)cx.Esp,args,sizeof(args),&got);
 printf("CLIENT ERROR REPORT pid=%lu code=%lu caller=%08lX ECX=%08lX EAX=%08lX\\n",ev.dwProcessId,args[1],args[0],cx.Ecx,cx.Eax);
 for(auto &m:modules[ev.dwProcessId]) if(args[0]>=m.first && args[0]<m.first+m.second.size) printf("ERROR CALLER %s + 0x%lX\\n",m.second.path.c_str(),(DWORD)(args[0]-m.first));
 SymInitialize(process,NULL,TRUE); CONTEXT walk=cx; STACKFRAME64 frame={};
 frame.AddrPC.Offset=walk.Eip; frame.AddrPC.Mode=AddrModeFlat; frame.AddrFrame.Offset=walk.Ebp; frame.AddrFrame.Mode=AddrModeFlat; frame.AddrStack.Offset=walk.Esp; frame.AddrStack.Mode=AddrModeFlat;
 for(int i=0;i<25;i++) { if(!StackWalk64(IMAGE_FILE_MACHINE_I386,process,th,&frame,&walk,NULL,SymFunctionTableAccess64,SymGetModuleBase64,NULL)) break;
 for(auto &m:modules[ev.dwProcessId]) if(frame.AddrPC.Offset>=m.first && frame.AddrPC.Offset<m.first+m.second.size) printf("ERROR STACK %s + 0x%lX\\n",m.second.path.c_str(),(DWORD)(frame.AddrPC.Offset-m.first)); }
 SymCleanup(process);
 '''+s[b:]
Path('Diagnostics/TraceError.cpp').write_text(s)
b=Path('Diagnostics/build-trace.cmd').read_text().replace('TraceClient.cpp','TraceError.cpp');Path('Diagnostics/build-error-trace.cmd').write_text(b)
