from pathlib import Path
import struct
for name in ['swtor_main_global_1.tor','swtor_en-us_global_1.tor']:
 with (Path('AssetsConverted')/name).open('r+b') as f:f.seek(4);f.write(struct.pack('<I',6))
s=Path('Diagnostics/TraceError.cpp').read_text().replace('DWORD offsets[]={0x76800}','DWORD offsets[]={0x205870}')
s=s.replace('std::map<DWORD,std::map<DWORD_PTR,BYTE>> probes;','std::map<DWORD,std::map<DWORD_PTR,BYTE>> probes; std::map<DWORD,DWORD_PTR> stepping;')
a=s.index('DWORD args[12]={};');b=s.index('BYTE old=probes',a)
s=s[:a]+'''DWORD args[10]={}; SIZE_T got=0; HANDLE process=processes[ev.dwProcessId];
 ReadProcessMemory(process,(void*)cx.Esp,args,sizeof(args),&got);
 printf("INTERNAL LOG caller=%08lX\\n",args[0]);
 for(int j=1;j<5;j++) { char buf[1024]={}; ReadProcessMemory(process,(void*)args[j],buf,1022,&got);
 printf("ARG%d=%08lX ",j,args[j]); if(buf[0] && !buf[1]) printf("%ls\\n",(wchar_t*)buf); else printf("%s\\n",buf); }
 '''+s[b:]
s=s.replace('cx.Eip=(DWORD)address;','cx.Eip=(DWORD)address; cx.EFlags|=0x100; stepping[ev.dwThreadId]=address;')
s=s.replace('probes[ev.dwProcessId].erase(address);','')
s=s.replace('if(code!=EXCEPTION_BREAKPOINT && code!=0x4000001f) {','''if(code==EXCEPTION_SINGLE_STEP && stepping.count(ev.dwThreadId)) { BYTE trap=0xcc;SIZE_T n;DWORD_PTR bp=stepping[ev.dwThreadId];WriteProcessMemory(processes[ev.dwProcessId],(void*)bp,&trap,1,&n);FlushInstructionCache(processes[ev.dwProcessId],(void*)bp,1);stepping.erase(ev.dwThreadId); }
   else if(code!=EXCEPTION_BREAKPOINT && code!=0x4000001f) {''')
Path('Diagnostics/TraceInternal.cpp').write_text(s)
Path('Diagnostics/build-internal-trace.cmd').write_text(Path('Diagnostics/build-trace.cmd').read_text().replace('TraceClient.cpp','TraceInternal.cpp'))
