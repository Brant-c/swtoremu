// ==========================================================
// Nexus - ToR Project
// 
// Usage: Rename 'MemoryMan.dll' (located in the SWToR
//   directory) to 'Nexus.dll', build this project and place
//   the built 'MemoryMan.dll' in your SWToR directory
//
// Notes: Should work with any version of the game
//   No need for manual patching
//
// Author: NoFaTe
// ==========================================================

#include <WinSock2.h>
#include <WS2tcpip.h>
#include <stdint.h>
#include <intrin.h>
#include "StdAfx.h"
#include "acpdump2.h"
#include "ToR.h"

#pragma comment(lib, "ws2_32.lib")

typedef wchar_t* (__stdcall * getValByName_t)(char* name);
getValByName_t getValByName = (getValByName_t)0x00;

//--------------------------------------------------------------------------------
int (__stdcall* RSAFunc_r)(int a2, int pRSAKey, int a4);

int __stdcall RSAFunc(int a2, int pRSAKey, int a4)
{
	__asm pushad

	Log::Write("RSAHook", "Called");

	unsigned char rawData[292] = {
		0x30, 0x82, 0x01, 0x20, 0x30, 0x0D, 0x06, 0x09, 0x2A, 0x86, 0x48, 0x86,
		0xF7, 0x0D, 0x01, 0x01, 0x01, 0x05, 0x00, 0x03, 0x82, 0x01, 0x0D, 0x00,
		0x30, 0x82, 0x01, 0x08, 0x02, 0x82, 0x01, 0x01, 0x00, 0xB2, 0x3B, 0x14,
		0xD0, 0x60, 0xC3, 0x0D, 0xDB, 0x90, 0x53, 0x29, 0x94, 0xFD, 0x63, 0xF3,
		0x57, 0x0D, 0x02, 0x55, 0x41, 0xCD, 0x08, 0x6A, 0x6F, 0xFF, 0x0D, 0x44,
		0xE5, 0x19, 0xA8, 0x04, 0xE6, 0x3C, 0x31, 0x28, 0x1C, 0x71, 0x74, 0x40,
		0xAD, 0x7B, 0xAB, 0x8F, 0xE3, 0x3E, 0x06, 0xF7, 0xBD, 0x10, 0xF5, 0x3D,
		0x8E, 0x0F, 0xA9, 0x00, 0xB8, 0xB6, 0xA0, 0x8F, 0xE4, 0xCB, 0xE4, 0x13,
		0x3D, 0x84, 0xBC, 0xE9, 0x19, 0x91, 0x6E, 0xCE, 0x58, 0x84, 0x50, 0xDC,
		0x79, 0x15, 0xD3, 0x16, 0xEE, 0x6B, 0x36, 0xEC, 0xDF, 0x81, 0x1E, 0x8F,
		0x03, 0x9B, 0x20, 0xB1, 0x8E, 0x56, 0x4E, 0x51, 0x66, 0xED, 0xC7, 0xFC,
		0x7E, 0x03, 0xC4, 0xCC, 0xD2, 0xCD, 0x31, 0x1C, 0xAC, 0x1C, 0x17, 0x3E,
		0xB3, 0xF6, 0x5F, 0xB8, 0xAA, 0x05, 0x5A, 0xAE, 0xB5, 0xB1, 0x50, 0x3E,
		0xE8, 0x90, 0x69, 0x1F, 0xBA, 0x84, 0x0E, 0xDB, 0x62, 0x58, 0x64, 0x4A,
		0x4B, 0x64, 0xE7, 0xB6, 0x5A, 0x2D, 0xA3, 0x6C, 0x8E, 0x6C, 0x26, 0x02,
		0xF6, 0x08, 0xF6, 0x7A, 0x03, 0x20, 0xC0, 0x68, 0x63, 0xB1, 0x19, 0xEF,
		0x18, 0x9A, 0x60, 0xB3, 0xDD, 0x89, 0x21, 0xF6, 0x9A, 0x01, 0x1E, 0x3D,
		0x51, 0x8F, 0x03, 0x0E, 0x5D, 0xD8, 0x96, 0x22, 0x06, 0x7C, 0x47, 0x21,
		0x66, 0xF1, 0x29, 0xBC, 0x28, 0x3E, 0x8D, 0xBE, 0xEE, 0x4B, 0x6B, 0x7D,
		0x57, 0xE1, 0x35, 0x18, 0x6A, 0x87, 0xB5, 0x1F, 0xCC, 0x17, 0xAE, 0xC7,
		0x46, 0x73, 0x79, 0x6E, 0xF8, 0xA6, 0xD9, 0xE5, 0x98, 0x52, 0xE9, 0xE6,
		0x1D, 0x8A, 0x6D, 0x0E, 0xEE, 0xBC, 0x6B, 0x93, 0xF5, 0xF8, 0x7F, 0x7D,
		0x30, 0x69, 0xB6, 0x21, 0x50, 0x3D, 0xA1, 0x27, 0x72, 0x99, 0xC8, 0x22,
		0x00, 0x51, 0xB5, 0x95, 0xB9, 0x41, 0x20, 0x7E, 0xFA, 0x93, 0x55, 0x3A,
		0x31, 0x02, 0x01, 0x11
	};

	memcpy((unsigned char *)pRSAKey, rawData, 0x124);

	__asm popad

	return RSAFunc_r(a2, pRSAKey, a4);
}
//--------------------------------------------------------------------------------
int (__cdecl* SSL_CTX_set_verify_r)(int ctx, int mode, int cb);

int __cdecl SSL_CTX_set_verify(int ctx, int mode, int cb)
{
	// Accept any SSL Certificate
	if (mode == 1)
		mode = 0;

	return SSL_CTX_set_verify_r(ctx, mode, cb);
}
//--------------------------------------------------------------------------------

char (__stdcall* GenRSAHandshake_r)(int a1, int a2, char *uUsername, char *uPassword);

char __stdcall GenRSAHandshake_stub(int a1, int a2, char *uUsername, char *uPassword)
{
	
	return GenRSAHandshake_r(a1, a2, uUsername, uPassword);
}

char __stdcall GenRSAHandshake(int a1, int a2, char *uUsername, char *uPassword)
{
	__asm pushad

	Log::Write("PassHook", "Called; Username: %s | Password: %s", (const char*)uUsername, (const char*)uPassword);

	__asm popad
	/*__asm
	{
		push ebp
		mov ebp, esp
		push dword ptr[ebp + 0x0C] // uPassword
		push dword ptr[ebp + 0x08] // uUsername
		//push uPassword
		//push uUsername
		push ecx // a2
		push eax // a1
		call GenRSAHandshake_stub
		
		mov esp, ebp
		pop ebp

		retn 8//n 8
	}*/

	return GenRSAHandshake_r(a1, a2, uUsername, uPassword);
}

//--------------------------------------------------------------------------------
typedef int (WSAAPI *getaddrinfo_t)(PCSTR pNodeName, PCSTR pServiceName, const ADDRINFOA *pHints, PADDRINFOA *ppResult);
getaddrinfo_t getaddrinfo_r = (getaddrinfo_t)getaddrinfo;

char* serverName = NULL;
char* webName = NULL;

int WSAAPI getaddrinfo_c(PCSTR pNodeName, PCSTR pServiceName, const ADDRINFOA *pHints, PADDRINFOA *ppResult) 
{
	Log::Write("WS2_32", "GetAddrInfo (%s)", (char*)pNodeName);

	/*unsigned int RandomHost = Utils::oneAtATimeHash("something.com");

	unsigned int current = Utils::oneAtATimeHash((char*)name);

	if (current == RandomHost) 
	{
		serverName = "localhost";
		hostname = serverName;

		Log::Write("WS2_32", "Redirecting to '%s'", serverName);
	}*/

	return getaddrinfo_r(pNodeName, pServiceName, pHints, ppResult);
}


typedef int (WINAPI *recv_t)(SOCKET s, LPWSABUF lpBuffers, DWORD dwBufferCount, LPDWORD lpNumberOfBytesRecvd, LPDWORD lpFlags, LPWSAOVERLAPPED lpOverlapped, LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine);
recv_t recv_r = (recv_t)WSARecv;

int WINAPI recv_c(SOCKET s, LPWSABUF lpBuffers, DWORD dwBufferCount, LPDWORD lpNumberOfBytesRecvd, LPDWORD lpFlags, LPWSAOVERLAPPED lpOverlapped, LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine)
{
	_asm pushad;

	if( lpBuffers && lpBuffers->buf && lpBuffers->len > 0 )
	{
		sockaddr_in addr;
		int len = sizeof(sockaddr_in);
		getpeername(s, (sockaddr*)&addr, &len);

		Log::Write("MainHook", "WSARecv Called [%s:%d]", inet_ntoa(addr.sin_addr), ntohs(addr.sin_port));
	}
	
	_asm popad;

	return recv_r(s, lpBuffers, dwBufferCount, lpNumberOfBytesRecvd, lpFlags, lpOverlapped, lpCompletionRoutine);
}

//--------------------------------------------------------------------------------

typedef int (WINAPI *send_t)(SOCKET s, LPWSABUF lpBuffers, DWORD dwBufferCount, LPDWORD lpNumberOfBytesSent, DWORD dwFlags, LPWSAOVERLAPPED lpOverlapped, LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine);
send_t send_r = (send_t)WSASend;

int WINAPI send_c(SOCKET s, LPWSABUF lpBuffers, DWORD dwBufferCount, LPDWORD lpNumberOfBytesSent, DWORD dwFlags, LPWSAOVERLAPPED lpOverlapped, LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine)
{
	sockaddr_in addr;
	int len = sizeof(sockaddr_in);
	getpeername(s, (sockaddr*)&addr, &len);

	Log::Write("MainHook", "WSASend Called [%s:%d]", inet_ntoa(addr.sin_addr), ntohs(addr.sin_port));

	return send_r(s, lpBuffers, dwBufferCount, lpNumberOfBytesSent, dwFlags, lpOverlapped, lpCompletionRoutine);
}

//--------------------------------------------------------------------------------

typedef int (WINAPI *sendTo_t)(SOCKET s, LPWSABUF lpBuffers, DWORD dwBufferCount, LPDWORD lpNumberOfBytesSent, DWORD dwFlags, const struct sockaddr *lpTo, int iTolen, LPWSAOVERLAPPED lpOverlapped, LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine);
sendTo_t sendTo_r = (sendTo_t)WSASendTo;

int WINAPI sendTo_c(SOCKET s, LPWSABUF lpBuffers, DWORD dwBufferCount, LPDWORD lpNumberOfBytesSent, DWORD dwFlags, const struct sockaddr *lpTo, int iTolen, LPWSAOVERLAPPED lpOverlapped, LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine)
{
	Log::Write("MainHook", "WSASendTo Called [%s:%d]", inet_ntoa(((sockaddr_in*)lpTo)->sin_addr), ntohs(((sockaddr_in*)lpTo)->sin_port));
	return sendTo_r(s, lpBuffers, dwBufferCount, lpNumberOfBytesSent, dwFlags, lpTo, iTolen, lpOverlapped, lpCompletionRoutine);
}

//--------------------------------------------------------------------------------

typedef int (WINAPI *recvFrom_t)(SOCKET s, LPWSABUF lpBuffers, DWORD dwBufferCount, LPDWORD lpNumberOfBytesRecvd, LPDWORD lpFlags, struct sockaddr *lpFrom, LPINT lpFromlen, LPWSAOVERLAPPED lpOverlapped, LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine);
recvFrom_t recvFrom_r = (recvFrom_t)WSARecvFrom;

int WINAPI recvFrom_c(SOCKET s, LPWSABUF lpBuffers, DWORD dwBufferCount, LPDWORD lpNumberOfBytesRecvd, LPDWORD lpFlags, struct sockaddr *lpFrom, LPINT lpFromlen, LPWSAOVERLAPPED lpOverlapped, LPWSAOVERLAPPED_COMPLETION_ROUTINE lpCompletionRoutine)
{
	Log::Write("MainHook", "WSARecvFrom Called [%s:%d]", inet_ntoa(((sockaddr_in*)lpFrom)->sin_addr), ntohs(((sockaddr_in*)lpFrom)->sin_port));
	return recvFrom_r(s, lpBuffers, dwBufferCount, lpNumberOfBytesRecvd, lpFlags, lpFrom, lpFromlen, lpOverlapped, lpCompletionRoutine);
}

typedef void (__thiscall * State3Setter_t)(void* pThis);
static State3Setter_t State3Setter_r = NULL;
static bool g_inState3Hook = false;

// Client 1.0.0.0 outbound CMsgF96DCDB0 wrapper. Its single argument is the
// Hero byte-vector serialized by 0x0097CB30: length at +0x0C, data at +0x10.
// Keep this opt-in because it is a version-specific diagnostic hook.
typedef void (__thiscall * AreaRpcSend_t)(void* pThis, void* blob);
static AreaRpcSend_t AreaRpcSend_r = NULL;
static DWORD g_clientImageBase = 0;
static DWORD g_clientImageSize = 0;

// Common client event bridge at static VA 0x005D12A0. It accepts an event
// class (1..4) plus a client-owned envelope, then dispatches envelope+0x14 to
// virtual slot +0x12C on the global event manager. This is diagnostic-only.
typedef void (__cdecl * EventDispatch_t)(DWORD eventClass, void* envelope);
static EventDispatch_t EventDispatch_r = NULL;
static volatile LONG g_eventDispatchCount[5] = { 0 };
static DWORD g_lastEventHash[5] = { 0 };

// Generic packed-string reader. We only log calls returning into the two
// SMSG_RESULTS fields, so this does not spam unrelated packet parsing.
typedef void (__thiscall * ReadPackedString_t)(void* reader, void* output);
static ReadPackedString_t ReadPackedString_r = NULL;

// OmegaClientObject's virtual message handler. Unlike the packed-string hook,
// this records entry before opcode selection, so a routed-but-malformed
// SMSG_RESULTS can be distinguished from a message rejected by routing.
typedef void (__thiscall * OmegaMessage_t)(void* pThis, void* messageRef,
	DWORD opcode, DWORD routeContext, void* reader);
static OmegaMessage_t OmegaMessage_r = NULL;
static volatile LONG g_omegaMessageCount = 0;

// Inbound network frame parser and the immediately following two-handle route
// lookup (client VAs 0x009F7B90 and 0x009ECAA0). These are upstream of every
// service object's virtual message handler and expose the actual values the
// client parsed from the wire, plus whether its route map found an object.
typedef void (__cdecl * ParseInboundFrame_t)(void* frame, DWORD* opcode,
	WORD* firstHandle, WORD* secondHandle);
typedef void (__thiscall * RouteLookup_t)(void* routeMap, void* outputIterator,
	void* key);
static ParseInboundFrame_t ParseInboundFrame_r = NULL;
static RouteLookup_t RouteLookup_r = NULL;
static __declspec(thread) DWORD g_parsedInboundOpcode = 0;
static __declspec(thread) WORD g_parsedInboundFirst = 0;
static __declspec(thread) WORD g_parsedInboundSecond = 0;

void __cdecl ParseInboundFrame_Hook(void* frame, DWORD* opcode,
	WORD* firstHandle, WORD* secondHandle)
{
	if (ParseInboundFrame_r)
		ParseInboundFrame_r(frame, opcode, firstHandle, secondHandle);

	__try
	{
		g_parsedInboundOpcode = opcode ? *opcode : 0;
		g_parsedInboundFirst = firstHandle ? *firstHandle : 0;
		g_parsedInboundSecond = secondHandle ? *secondHandle : 0;
		if (g_parsedInboundOpcode == 0xD5280283)
			Log::Write("InboundRouteHook",
				"phase=parsed frame=%p opcode=0x%08X first=0x%04X second=0x%04X",
				frame, g_parsedInboundOpcode, g_parsedInboundFirst, g_parsedInboundSecond);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("InboundRouteHook", "phase=parse-inspection-failed frame=%p", frame);
	}
}

void __fastcall RouteLookup_Hook(void* routeMap, void* EDX,
	void* outputIterator, void* key)
{
	if (RouteLookup_r)
		RouteLookup_r(routeMap, outputIterator, key);

	if (g_parsedInboundOpcode != 0xD5280283)
		return;

	__try
	{
		DWORD node = outputIterator ? *(DWORD*)outputIterator : 0;
		DWORD sentinel = routeMap ? (DWORD)routeMap + 4 : 0;
		DWORD keyFirst = key ? *(DWORD*)key : 0;
		DWORD keySecond = key ? *(DWORD*)((BYTE*)key + 4) : 0;
		Log::Write("InboundRouteHook",
			"phase=lookup opcode=0x%08X parsed=0x%04X/0x%04X key=0x%04X/0x%04X map=%p node=%p sentinel=%p found=%u",
			g_parsedInboundOpcode, g_parsedInboundFirst, g_parsedInboundSecond,
			keyFirst & 0xFFFF, keySecond & 0xFFFF, routeMap,
			(void*)node, (void*)sentinel, node != sentinel ? 1 : 0);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("InboundRouteHook", "phase=lookup-inspection-failed map=%p key=%p", routeMap, key);
	}
}

void __fastcall OmegaMessage_Hook(void* pThis, void* EDX, void* messageRef,
	DWORD opcode, DWORD routeContext, void* reader)
{
	LONG count = InterlockedIncrement(&g_omegaMessageCount);
	if (opcode == 0xD5280283 || count <= 100)
	{
		Log::Write("OmegaMessageHook",
			"phase=enter count=%ld this=%p messageRef=%p opcode=0x%08X routeContext=0x%08X reader=%p",
			count, pThis, messageRef, opcode, routeContext, reader);
	}

	if (OmegaMessage_r)
		OmegaMessage_r(pThis, messageRef, opcode, routeContext, reader);

	if (opcode == 0xD5280283)
		Log::Write("OmegaMessageHook", "phase=return count=%ld opcode=0x%08X", count, opcode);
}

void __fastcall ReadPackedString_Hook(void* reader, void* EDX, void* output)
{
	void* caller = _ReturnAddress();
	if (ReadPackedString_r)
		ReadPackedString_r(reader, output);

	DWORD callerRva = g_clientImageBase ? (DWORD)caller - g_clientImageBase : 0;
	if (callerRva != (0x006521CF - 0x00400000) &&
		callerRva != (0x006521DA - 0x00400000))
		return;

	__try
	{
		BYTE* object = (BYTE*)output;
		DWORD value = object ? *(DWORD*)(object + 4) : 0;
		char objectHex[3 * 16 + 1] = { 0 };
		for (DWORD i = 0; object && i < 16; ++i)
			_snprintf(objectHex + i * 3, sizeof(objectHex) - i * 3,
				"%02X%s", object[i], (i < 15) ? " " : "");
		Log::Write("SMsgResultsHook",
			"field=%u callerRva=0x%08X reader=%p output=%p value=%p object=%s",
			callerRva == (0x006521CF - 0x00400000) ? 1 : 2,
			callerRva, reader, output, (void*)value, objectHex);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("SMsgResultsHook", "inspection failed: callerRva=0x%08X output=%p", callerRva, output);
	}
}

static DWORD HashBytes(const BYTE* bytes, DWORD length)
{
	DWORD hash = 2166136261u;
	for (DWORD i = 0; i < length; ++i)
		hash = (hash ^ bytes[i]) * 16777619u;
	return hash;
}

void __cdecl EventDispatch_Hook(DWORD eventClass, void* envelope)
{
	__try
	{
		BYTE* payload = envelope ? ((BYTE*)envelope + 0x14) : NULL;
		DWORD manager = g_clientImageBase
			? *(DWORD*)(g_clientImageBase + (0x01491A54 - 0x00400000)) : 0;
		DWORD vtable = manager ? *(DWORD*)manager : 0;
		DWORD handler = vtable ? *(DWORD*)(vtable + 0x12C) : 0;
		DWORD logicalLength = payload ? *(DWORD*)(payload + 0x0C) : 0;
		BYTE* logicalBytes = (payload && logicalLength <= 4096) ? *(BYTE**)(payload + 0x10) : NULL;
		DWORD hash = logicalBytes ? HashBytes(logicalBytes, logicalLength) : 0;
		LONG count = (eventClass <= 4)
			? InterlockedIncrement(&g_eventDispatchCount[eventClass]) : 0;
		bool changed = eventClass <= 4 && g_lastEventHash[eventClass] != hash;
		if (eventClass <= 4) g_lastEventHash[eventClass] = hash;

		// Record initial traffic, every changed snapshot, and a periodic heartbeat.
		// This remains useful during a long hang without generating an unbounded log.
		if (count <= 100 || changed || (count && (count % 250) == 0))
		{
			char hex[3 * 64 + 1] = { 0 };
			for (DWORD i = 0; payload && i < 64; ++i)
				_snprintf(hex + i * 3, sizeof(hex) - i * 3, "%02X%s",
					payload[i], (i < 63) ? " " : "");
			Log::Write("EventDispatchHook",
				"class=%u count=%ld envelope=%p payload=%p logicalLen=%u hash=0x%08X changed=%u manager=%p vtable=%p handler=%p handlerRva=0x%08X bytes=%s",
				eventClass, count, envelope, payload, logicalLength, hash, changed ? 1 : 0,
				(void*)manager, (void*)vtable, (void*)handler,
				(g_clientImageBase && handler >= g_clientImageBase &&
				 handler < g_clientImageBase + g_clientImageSize)
					? handler - g_clientImageBase : 0,
				hex);
		}
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("EventDispatchHook", "inspection failed: class=%u envelope=%p", eventClass, envelope);
	}

	if (EventDispatch_r)
		EventDispatch_r(eventClass, envelope);
}

static void FormatRpcStack(char* output, size_t outputSize)
{
	if (!output || outputSize == 0) return;
	output[0] = '\0';

	PVOID frames[12] = { 0 };
	USHORT count = CaptureStackBackTrace(0, ARRAYSIZE(frames), frames, NULL);
	size_t used = 0;
	for (USHORT i = 0; i < count && used + 24 < outputSize; ++i)
	{
		DWORD address = (DWORD)frames[i];
		int written;
		if (g_clientImageBase && address >= g_clientImageBase &&
			address < g_clientImageBase + g_clientImageSize)
		{
			written = _snprintf(output + used, outputSize - used,
				"%s%08X(+%08X)", i ? ">" : "", address,
				address - g_clientImageBase);
		}
		else
		{
			written = _snprintf(output + used, outputSize - used,
				"%s%08X", i ? ">" : "", address);
		}
		if (written <= 0 || (size_t)written >= outputSize - used) break;
		used += written;
	}
}

void __fastcall AreaRpcSend_Hook(void* pThis, void* EDX, void* blob)
{
	DWORD length = 0;
	BYTE* bytes = NULL;
	__try
	{
		if (blob)
		{
			length = *(DWORD*)((BYTE*)blob + 0x0C);
			bytes = *(BYTE**)((BYTE*)blob + 0x10);
		}

		char hex[3 * 64 + 1] = { 0 };
		DWORD shown = (length < 64) ? length : 64;
		for (DWORD i = 0; bytes && i < shown; ++i)
			_snprintf(hex + i * 3, sizeof(hex) - i * 3, "%02X%s", bytes[i], (i + 1 < shown) ? " " : "");

		DWORD targetId = (bytes && length >= 5 && bytes[0] == 0xC7)
			? *(DWORD*)(bytes + 1) : 0;
		DWORD operationId = (bytes && length >= 9 && bytes[0] == 0xC7)
			? *(DWORD*)(bytes + 5) : 0;
		char stack[512] = { 0 };
		FormatRpcStack(stack, sizeof(stack));
		Log::Write("AreaRpcHook",
			"sender=%p blob=%p len=%u marker=0x%02X target=0x%08X operation=0x%08X bytes=%s%s stack=%s",
			pThis, blob, length, (bytes && length) ? bytes[0] : 0,
			targetId, operationId, hex, (length > shown) ? " ..." : "", stack);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("AreaRpcHook", "Could not inspect blob=%p caller=%p", blob, _ReturnAddress());
	}

	if (AreaRpcSend_r)
		AreaRpcSend_r(pThis, blob);
}

void __fastcall State3Setter_Hook(void* pThis, void* EDX)
{
	if (g_inState3Hook)
	{
		if (State3Setter_r) State3Setter_r(pThis);
		return;
	}
	g_inState3Hook = true;

	if (pThis)
	{
		DWORD state8C = *(DWORD*)((BYTE*)pThis + 0x8C);
		DWORD flag90 = *(DWORD*)((BYTE*)pThis + 0x90);
		Log::Write("AreaStateHook", "State3Setter called: AreaObj=%p, state[0x8C]=%u (0x%08X), flag[0x90]=%u", pThis, state8C, state8C, flag90);
	}

	// Keep this hook diagnostic-only. The previous unsafe memory mutation was
	// removed intentionally because it destabilized the client while entering the
	// world. Re-enable only after validating the correct target method/ABI.
	if (State3Setter_r)
		State3Setter_r(pThis);

	g_inState3Hook = false;
}

//--------------------------------------------------------------------------------

ToR* ToR::gInstance = NULL;

ToR* ToR::GetInstance()
{
	if(gInstance == NULL)
		gInstance = new ToR;
	return gInstance;
}

void ToR::InitHooks()
{
    // Keep original function pointers in static storage: Detours updates them
    // to trampolines only when the transaction commits successfully.
    DWORD sslAddress = Utils::FindPattern(dwEntryPoint, dwCodeSize,
        (BYTE*)"\x8B\x44\x24\x04\x8B\x4C\x24\x08\x8B\x54\x24\x0C\x89\x88\xC0\x00",
        "xxxxxxxxxxxxxxxx");
    if (!sslAddress)
    {
        Log::Write("NexusToR", "Unsupported client: SSL signature not found; no hooks installed");
        return;
    }
    SSL_CTX_set_verify_r = (int (__cdecl*)(int, int, int))sslAddress;

    HMODULE hMod = GetModuleHandle(NULL);
    if (hMod)
    {
        DWORD baseAddr = (DWORD)hMod;
		g_clientImageBase = baseAddr;
		IMAGE_DOS_HEADER* dos = (IMAGE_DOS_HEADER*)baseAddr;
		IMAGE_NT_HEADERS* nt = (IMAGE_NT_HEADERS*)(baseAddr + dos->e_lfanew);
		g_clientImageSize = nt->OptionalHeader.SizeOfImage;
		Log::Write("AreaRpcHook", "client image base=%p size=0x%08X", hMod, g_clientImageSize);
        State3Setter_r = (State3Setter_t)(baseAddr + 0x0037B140);

		char traceRpc[8] = { 0 };
		if (GetEnvironmentVariableA("SWTOR_TRACE_RPC_CALLS", traceRpc, sizeof(traceRpc)) > 0 && traceRpc[0] == '1')
		{
			BYTE* candidate = (BYTE*)(baseAddr + 0x0067FEB0);
			static const BYTE expected[] = { 0x55, 0x8B, 0xEC, 0x64, 0xA1 };
			if (memcmp(candidate, expected, sizeof(expected)) == 0)
				AreaRpcSend_r = (AreaRpcSend_t)candidate;
			else
				Log::Write("AreaRpcHook", "Unsupported client bytes at %p; RPC hook not installed", candidate);
		}

		char traceEvents[8] = { 0 };
		if (GetEnvironmentVariableA("SWTOR_TRACE_EVENT_DISPATCH", traceEvents, sizeof(traceEvents)) > 0 && traceEvents[0] == '1')
		{
			BYTE* candidate = (BYTE*)(baseAddr + (0x005D12A0 - 0x00400000));
			static const BYTE expected[] = { 0x55, 0x8B, 0xEC, 0x83, 0xE4, 0xF8 };
			if (memcmp(candidate, expected, sizeof(expected)) == 0)
				EventDispatch_r = (EventDispatch_t)candidate;
			else
				Log::Write("EventDispatchHook", "Unsupported client bytes at %p; event hook not installed", candidate);

			BYTE* stringReader = (BYTE*)(baseAddr + (0x0097D270 - 0x00400000));
			static const BYTE expectedStringReader[] = { 0x55, 0x8B, 0xEC, 0x56, 0x8B, 0xF1 };
			if (memcmp(stringReader, expectedStringReader, sizeof(expectedStringReader)) == 0)
				ReadPackedString_r = (ReadPackedString_t)stringReader;
			else
				Log::Write("SMsgResultsHook", "Unsupported client bytes at %p; result-string hook not installed", stringReader);

			BYTE* omegaMessage = (BYTE*)(baseAddr + (0x00652120 - 0x00400000));
			static const BYTE expectedOmegaMessage[] = { 0x55, 0x8B, 0xEC, 0x6A, 0xFF };
			if (memcmp(omegaMessage, expectedOmegaMessage, sizeof(expectedOmegaMessage)) == 0)
				OmegaMessage_r = (OmegaMessage_t)omegaMessage;
			else
				Log::Write("OmegaMessageHook", "Unsupported client bytes at %p; message-entry hook not installed", omegaMessage);

			BYTE* inboundParser = (BYTE*)(baseAddr + (0x009F7B90 - 0x00400000));
			static const BYTE expectedInboundParser[] = { 0x55, 0x8B, 0xEC };
			if (memcmp(inboundParser, expectedInboundParser, sizeof(expectedInboundParser)) == 0)
				ParseInboundFrame_r = (ParseInboundFrame_t)inboundParser;
			else
				Log::Write("InboundRouteHook", "Unsupported parser bytes at %p; parser hook not installed", inboundParser);

			BYTE* routeLookup = (BYTE*)(baseAddr + (0x009ECAA0 - 0x00400000));
			static const BYTE expectedRouteLookup[] = { 0x55, 0x8B, 0xEC };
			if (memcmp(routeLookup, expectedRouteLookup, sizeof(expectedRouteLookup)) == 0)
				RouteLookup_r = (RouteLookup_t)routeLookup;
			else
				Log::Write("InboundRouteHook", "Unsupported lookup bytes at %p; route hook not installed", routeLookup);
		}
    }

    LONG result = DetourTransactionBegin();
    if (result != NO_ERROR)
    {
        Log::Write("NexusToR", "Cannot begin hook transaction: %ld", result);
        return;
    }
    result = DetourUpdateThread(GetCurrentThread());
    if (result == NO_ERROR) result = DetourAttach(&(PVOID&)getaddrinfo_r, (PVOID)getaddrinfo_c);
    if (result == NO_ERROR) result = DetourAttach(&(PVOID&)recv_r, (PVOID)recv_c);
    if (result == NO_ERROR) result = DetourAttach(&(PVOID&)send_r, (PVOID)send_c);
    if (result == NO_ERROR) result = DetourAttach(&(PVOID&)sendTo_r, (PVOID)sendTo_c);
    if (result == NO_ERROR) result = DetourAttach(&(PVOID&)recvFrom_r, (PVOID)recvFrom_c);
    if (result == NO_ERROR) result = DetourAttach(&(PVOID&)SSL_CTX_set_verify_r, (PVOID)SSL_CTX_set_verify);
	if (result == NO_ERROR && AreaRpcSend_r) result = DetourAttach(&(PVOID&)AreaRpcSend_r, (PVOID)AreaRpcSend_Hook);
	if (result == NO_ERROR && EventDispatch_r) result = DetourAttach(&(PVOID&)EventDispatch_r, (PVOID)EventDispatch_Hook);
	if (result == NO_ERROR && ReadPackedString_r) result = DetourAttach(&(PVOID&)ReadPackedString_r, (PVOID)ReadPackedString_Hook);
	if (result == NO_ERROR && OmegaMessage_r) result = DetourAttach(&(PVOID&)OmegaMessage_r, (PVOID)OmegaMessage_Hook);
	if (result == NO_ERROR && ParseInboundFrame_r) result = DetourAttach(&(PVOID&)ParseInboundFrame_r, (PVOID)ParseInboundFrame_Hook);
	if (result == NO_ERROR && RouteLookup_r) result = DetourAttach(&(PVOID&)RouteLookup_r, (PVOID)RouteLookup_Hook);
    // Disabled while diagnosing a client freeze during world entry. This hook is
    // kept as a diagnostic logger only and must not intercept or mutate the area
    // object state until the call contract is verified.
    if (result == NO_ERROR && State3Setter_r) { /* Intentionally disabled */ }
    if (result != NO_ERROR)
    {
        DetourTransactionAbort();
        Log::Write("NexusToR", "Hook transaction aborted: %ld", result);
        return;
    }
    result = DetourTransactionCommit();
    if (result != NO_ERROR)
    {
        Log::Write("NexusToR", "Hook transaction failed: %ld", result);
        return;
    }
	Log::Write("NexusToR", "Network and SSL hooks installed; RPC trace=%s event trace=%s",
		AreaRpcSend_r ? "enabled" : "disabled", EventDispatch_r ? "enabled" : "disabled");
}
ToR::ToR()
{
	// Initialize the Logging module
	Log::Init();

	HANDLE hModule = GetModuleHandle(NULL);

	dwCodeSize = Utils::GetSizeOfCode( hModule );
	dwCodeOffset = Utils::OffsetToCode( hModule );
	dwEntryPoint = (DWORD)hModule + dwCodeOffset;

	// Allocate a console for game output
	Utils::AllocateConsole("Star Wars: The Old Republic");
	Log::Write("NexusToR", "Initializing NexusToR Client");

	// Initialize our Hooks
	InitHooks();
}
