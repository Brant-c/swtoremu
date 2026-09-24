import ctypes
k=ctypes.WinDLL('kernel32',use_last_error=True); n=ctypes.WinDLL('ntdll')
k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];k.OpenProcess.restype=ctypes.c_void_p
k.CloseHandle.argtypes=[ctypes.c_void_p]
n.NtSuspendProcess.argtypes=[ctypes.c_void_p];n.NtSuspendProcess.restype=ctypes.c_long
h=k.OpenProcess(0x0800,False,26876)
if not h:raise ctypes.WinError(ctypes.get_last_error())
try:
 status=n.NtSuspendProcess(h)
 if status:raise RuntimeError(hex(status & 0xffffffff))
 print('Conversion process 26876 suspended; output files preserved.')
finally:k.CloseHandle(h)
