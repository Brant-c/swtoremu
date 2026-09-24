import ctypes, struct, sys
from pathlib import Path
pid, address, size = int(sys.argv[1]), int(sys.argv[2],16), int(sys.argv[3],0)
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.restype=ctypes.c_void_p
k.ReadProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
k.CloseHandle.argtypes=[ctypes.c_void_p]
h=k.OpenProcess(0x410,False,pid)
if not h: raise ctypes.WinError(ctypes.get_last_error())
try:
    data=ctypes.create_string_buffer(size); got=ctypes.c_size_t()
    if not k.ReadProcessMemory(h,address,data,size,ctypes.byref(got)): raise ctypes.WinError(ctypes.get_last_error())
    out=Path('Diagnostics')/f'live-code-{address:08X}'
    out.with_suffix('.bin').write_bytes(data.raw)
    coff=struct.pack('<HHIIIHH',0x14c,1,0,0,0,0,0)
    section=struct.pack('<8sIIIIIIHHI',b'.text',0,0,size,60,0,0,0,0,0x60000020)
    out.with_suffix('.obj').write_bytes(coff+section+data.raw)
    print(out)
finally:k.CloseHandle(h)
