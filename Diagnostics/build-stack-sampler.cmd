@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars32.bat"
cl /nologo /EHsc Diagnostics\Sample-ClientStacks.cpp /Fe:Diagnostics\Sample-ClientStacks.exe /Fo:Diagnostics\Sample-ClientStacks.obj dbghelp.lib
