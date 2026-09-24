@echo off
tasklist /FI "IMAGENAME eq ShardListServer.exe" | find /I "ShardListServer.exe" >nul
if errorlevel 1 (
  start "SWTORClassic shard list" /D "%~dp0SharpServer\ShardListServer\bin\Debug" "%~dp0SharpServer\ShardListServer\bin\Debug\ShardListServer.exe"
)
tasklist /FI "IMAGENAME eq NexusToRServer.exe" | find /I "NexusToRServer.exe" >nul
if errorlevel 1 (
  start "SWTORClassic server" /D "%~dp0SharpServer\bin\Debug" "%~dp0SharpServer\bin\Debug\NexusToRServer.exe"
)
call "%~dp0Run-Old-Client-Compatible.cmd"
