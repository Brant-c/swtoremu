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

// Client 1.0.0.0 inbound AreaRequestRPC bridge at static VA 0x00642CA0.
// The outer message handler reaches this through the concrete virtual slot at
// 0x0113F084+4.  When the optional global interface at 0x01491A88 is null, as
// observed in-world, it forwards the message to slot +8 of the listener at
// pThis+0x2C.  Observe the routing state and arguments without decoding or
// mutating client-owned state.
typedef void (__thiscall * AreaRpcReceiveBridge_t)(void* pThis, void* context,
	void* rpcMessage);
static AreaRpcReceiveBridge_t AreaRpcReceiveBridge_r = NULL;
static volatile LONG g_areaRpcReceiveCount = 0;
static DWORD g_clientImageBase = 0;
static DWORD g_clientImageSize = 0;

// Style-5 compact signed integer reader. The inbound RPC dispatcher calls it
// at 0x005BDA90 for the composite script/method selector. Filter on that exact
// return RVA so this read-only observer does not log unrelated stream values.
typedef bool (__stdcall * PackedSigned64Read_t)(void* stream, void* output);
static PackedSigned64Read_t PackedSigned64Read_r = NULL;

// Common client event bridge at static VA 0x005D12A0. It accepts an event
// class (1..4) plus a client-owned envelope, then dispatches envelope+0x14 to
// virtual slot +0x12C on the global event manager. This is diagnostic-only.
typedef void (__cdecl * EventDispatch_t)(DWORD eventClass, void* envelope);
static EventDispatch_t EventDispatch_r = NULL;
static volatile LONG g_eventDispatchCount[5] = { 0 };
static DWORD g_lastEventHash[5] = { 0 };

// Class-1 event bridge at static VA 0x00BD4910. The bridge resolves the
// concrete recipient with 0x006340E0 and invokes virtual slot +4. Keeping the
// active recipient in TLS lets the nested AreaRpc hook identify which runtime
// object actually generated a readiness poll without changing client state.
typedef void* (__cdecl * ResolveClass1Recipient_t)();
typedef void (__cdecl * Class1EventBridge_t)(void* unused, void* payload);
static ResolveClass1Recipient_t ResolveClass1Recipient_r = NULL;
static Class1EventBridge_t Class1EventBridge_r = NULL;
static __declspec(thread) void* g_class1Recipient = NULL;
static __declspec(thread) void* g_class1Method = NULL;

// Generic replicated-field string copier at static VA 0x00923C20. Earlier
// diagnostics called this a script dispatch function, but static disassembly
// proves callers pass one source string and use ECX as the destination field.
// The additional values below are caller-stack context, not formal arguments;
// retain the sampling hook only to correlate field application with the poll.
typedef DWORD (__thiscall * ScriptDispatch_t)(void* pThis, DWORD a1, DWORD a2,
	DWORD a3, DWORD a4, DWORD a5, DWORD a6, DWORD a7, DWORD a8);
static ScriptDispatch_t ScriptDispatch_r = NULL;
static volatile LONG g_scriptDispatchCount = 0;
struct ScriptDispatchSample
{
	DWORD tick;
	DWORD callerRva;
	DWORD pThis;
	DWORD args[8];
	DWORD result;
};
static __declspec(thread) ScriptDispatchSample g_scriptSamples[16] = { 0 };
static __declspec(thread) DWORD g_scriptSampleNext = 0;
static __declspec(thread) ScriptDispatchSample g_activeScriptDispatch[16] = { 0 };
static __declspec(thread) DWORD g_activeScriptDepth = 0;
static void FormatRpcStack(char* output, size_t outputSize);
static volatile LONG g_readinessVmDeepDumped = 0;
static volatile LONG g_readinessCodeDumped = 0;

static void LogReadinessMemory(const char* label, DWORD address)
{
	if (!address)
	{
		Log::Write("ReadinessVmHook", "%s=null", label);
		return;
	}

	__try
	{
		BYTE* bytes = (BYTE*)address;
		char hex[3 * 64 + 1] = { 0 };
		char ascii[65] = { 0 };
		for (DWORD i = 0; i < 64; ++i)
		{
			_snprintf(hex + i * 3, sizeof(hex) - i * 3,
				"%02X%s", bytes[i], (i < 63) ? " " : "");
			ascii[i] = (bytes[i] >= 0x20 && bytes[i] <= 0x7E)
				? (char)bytes[i] : '.';
		}
		Log::Write("ReadinessVmHook", "%s=%p bytes=%s ascii=%s",
			label, (void*)address, hex, ascii);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("ReadinessVmHook", "%s=%p unreadable", label, (void*)address);
	}
}

static void LogReadinessPointers(const char* label, DWORD address)
{
	if (!address) return;
	__try
	{
		DWORD* values = (DWORD*)address;
		for (DWORD i = 0; i < 16; ++i)
		{
			DWORD candidate = values[i];
			if (candidate < 0x00010000) continue;
			MEMORY_BASIC_INFORMATION info = { 0 };
			if (!VirtualQuery((void*)candidate, &info, sizeof(info)) ||
				info.State != MEM_COMMIT || (info.Protect & (PAGE_NOACCESS | PAGE_GUARD)))
				continue;
			char childLabel[64] = { 0 };
			_snprintf(childLabel, sizeof(childLabel), "%s[%02X]", label, i * 4);
			LogReadinessMemory(childLabel, candidate);
		}
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("ReadinessVmHook", "%s=%p pointer-scan-failed", label, (void*)address);
	}
}

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

// Central GOM definition lookup at static VA 0x004A95B0. The second explicit
// argument points to a 64-bit type ID. Keep this observer opt-in and filter
// before calling any logging code: this routine is hot during normal loading.
// It is read-only and never changes the lookup key, result, or returned value.
typedef DWORD (__thiscall * GomDefinitionLookup_t)(void* pThis, void* output,
	const ULONGLONG* typeId);
static GomDefinitionLookup_t GomDefinitionLookup_r = NULL;
static volatile LONG g_loadingGomLookupCount = 0;

// HeroClass::getField at static VA 0x004F5A00. The two DWORD arguments form
// the requested 64-bit field ID and output receives the client-owned field
// value interface. This observer never calls the getter independently and
// never modifies the class, output, or returned interface.
typedef void* (__thiscall * HeroClassGetField_t)(void* pThis, void* output,
	DWORD fieldLow, DWORD fieldHigh);
static HeroClassGetField_t HeroClassGetField_r = NULL;
static volatile LONG g_playerFieldAccessCount = 0;
	// Area message dispatcher at static VA 0x0064ED70. Signature derived from
	// Diagnostics/swtor-disasm.txt: __thiscall with FOUR stack args. arg2
	// ([ebp+0Ch]) is the message opcode; arg4 ([ebp+14h]) is the byte reader.
	// arg1/arg3 are branch-local out-params. No arg5/arg6 (0 refs). Hook is
	// __fastcall(pThis,EDX,...) with a __thiscall typedef, like AreaRpcSend_Hook.
	typedef void (__thiscall * AreaMessageDispatch_t)(void* pThis, DWORD arg1, DWORD arg2, DWORD arg3, void* arg4);
	static AreaMessageDispatch_t AreaMessageDispatch_r = NULL;
	static volatile LONG g_areaMessageCount = 0;

// Opt-in April HeroScript lifecycle observer.  These functions are loaded into
// executable private memory rather than the main image, so locate them by the
// byte-exact prologues in the preserved April .scpt resources.  The signatures
// below are the generated cdecl contracts (Me, replication argument / phase
// name id).  The hooks only log and forward unchanged.
typedef void (__cdecl * PhaseLifecycleMethod_t)(void* me, DWORD argument);
static PhaseLifecycleMethod_t PhaseInfoDestroy_r = NULL;
static PhaseLifecycleMethod_t UpdateGatewayForInstance_r = NULL;
static PhaseLifecycleMethod_t PlayerPhaseDataCreate_r = NULL;
static PhaseLifecycleMethod_t PlayerPhaseDataDestroy_r = NULL;
static volatile LONG g_phaseLifecycleInstallState = 0;
static volatile LONG g_phaseInfoDestroyDepth = 0;
static bool g_tracePhaseLifecycle = false;

static void TryInstallPhaseLifecycleHooks();



// HM.SetNodeFieldEnum at static VA 0x005D9FF0. This binding is verified from
// the patched call target in the loaded _BaseClientClassMethods module, not
// inferred from a neighboring native routine. The third argument is the enum
// value itself; the native helper passes its address into the typed assignment
// path. This observer forwards all three arguments unchanged.
typedef void (__cdecl * SetNodeFieldEnum_t)(void* node, DWORD fieldOperand,
	DWORD enumValue);
static SetNodeFieldEnum_t SetNodeFieldEnum_r = NULL;
static volatile LONG g_enumFieldWriteCount = 0;

static const char* PlayerFieldName(ULONGLONG id)
{
	switch (id)
	{
	case 0x4000000365D249CBULL: return "chrIsMe";
	case 0x400000045A767612ULL: return "_GameState";
	case 0x400000077CDF593BULL: return "chrCharacterPlayMode";
	case 0x4000000886E130D2ULL: return "chrCharacterPhaseMode";
	case 0x4000000D5DF53477ULL: return "chrPlayerLoaded";
	case 0x40000020F9D88CE0ULL: return "ablUserModalActiveSpecs";
	case 0x4000000C5FA2056AULL: return "phsCurrentInstanceNameID";
	case 0x4000000C5FA20570ULL: return "phsActiveInstances";
	case 0x40000012338B5ACCULL: return "phsActivePhaseData";
	case 0x40000002641F28CCULL: return "phsPhase";
	case 0x4000000C5FA6998BULL: return "phsPhasedInstanceToTrigger";
	case 0x40000013D713DE2BULL: return "phsGatewayList";
	case 0x4000000255DB920AULL: return "phsPhases";
	case 0x40000000009654C3ULL: return "guiHud2";
	case 0x40000000009C971FULL: return "gfxLoaded";
	default: return NULL;
	}
}

void* __fastcall HeroClassGetField_Hook(void* pThis, void* EDX, void* output,
	DWORD fieldLow, DWORD fieldHigh)
{
	void* result = HeroClassGetField_r
		? HeroClassGetField_r(pThis, output, fieldLow, fieldHigh) : NULL;
	ULONGLONG id = ((ULONGLONG)fieldHigh << 32) | fieldLow;
	const char* name = PlayerFieldName(id);
	if (!name) return result;

	__try
	{
		DWORD valueInterface = output ? *(DWORD*)output : 0;
		DWORD words[8] = { 0 };
		if (valueInterface)
			for (DWORD i = 0; i < ARRAYSIZE(words); ++i)
				words[i] = *(DWORD*)((BYTE*)valueInterface + i * 4);
		char stack[512] = { 0 };
		FormatRpcStack(stack, sizeof(stack));
		LONG count = InterlockedIncrement(&g_playerFieldAccessCount);
		Log::Write("PlayerFieldHook",
			"count=%ld name=%s id=0x%08X%08X class=%p output=%p interface=%p result=%p words=%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X stack=%s",
			count, name, fieldHigh, fieldLow, pThis, output,
			(void*)valueInterface, result, words[0], words[1], words[2], words[3],
			words[4], words[5], words[6], words[7], stack);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("PlayerFieldHook",
			"name=%s id=0x%08X%08X class=%p output=%p result=%p inspection-failed",
			name, fieldHigh, fieldLow, pThis, output, result);
	}
	return result;
}

void __cdecl SetNodeFieldEnum_Hook(void* node, DWORD fieldOperand,
	DWORD enumValue)
{
	// In the recovered loaded _BaseClientClassMethods module the return address
	// after this call is exactly 0x7A bytes after _SetGameState's unique
	// prologue. Validate both ends so unrelated SetNodeFieldEnum calls remain
	// completely silent; the unfiltered helper is extremely hot during enum
	// initialization.
	BYTE* caller = (BYTE*)_ReturnAddress();
	bool isBaseClientSetGameState = false;
	__try
	{
		static const BYTE methodPrologue[] =
			{ 0x53, 0x57, 0x56, 0x83, 0xEC, 0x10, 0xC7, 0x04, 0x24, 0x1F, 0, 0, 0 };
		static const BYTE afterCall[] =
			{ 0x83, 0xC4, 0x10, 0x5E, 0x5F, 0x5B };
		isBaseClientSetGameState = caller &&
			memcmp(caller - 0x7A, methodPrologue, sizeof(methodPrologue)) == 0 &&
			memcmp(caller, afterCall, sizeof(afterCall)) == 0;
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		isBaseClientSetGameState = false;
	}
	if (isBaseClientSetGameState)
	{
		char stack[512] = { 0 };
		FormatRpcStack(stack, sizeof(stack));
		LONG count = InterlockedIncrement(&g_enumFieldWriteCount);
		Log::Write("SetNodeFieldEnumHook",
			"count=%ld method=_BaseClient._SetGameState caller=%p node=%p fieldOperand=0x%08X enumValue=%u stack=%s",
			count, caller, node, fieldOperand, enumValue, stack);
	}
	if (SetNodeFieldEnum_r)
		SetNodeFieldEnum_r(node, fieldOperand, enumValue);
}

struct LoadingGomId
{
	ULONGLONG id;
	const char* name;
};

static const LoadingGomId g_loadingGomIds[] =
{
	{ 0x40000009C9065DB8ULL, "guiGFxLoadingScreen" },
	{ 0x4000000A90024EB7ULL, "guiGfxLoadingProgressBarOn" },
	{ 0x4000003509BC9B13ULL, "guiGfxLoadingStringTableTimer" },
	{ 0x4000000E661E635BULL, "guiGfxLoadingFadeTimer" },
	{ 0x4000000A69705858ULL, "guiGfxLoadingAssetLoadingTimer" },
	{ 0x4000000CB7723D57ULL, "guiGfxLoadingAssetTimeoutAt" },
	{ 0x4000000A69705859ULL, "guiGfxLoadingAssetLoadingTimerZeroCounter" },
	{ 0x4000000A69705857ULL, "guiGfxLoadingFadedOut" },
	{ 0x4000000A6970585AULL, "guiGfxLoadingNewFadeOut" },
	{ 0x4000000A90024EB8ULL, "guiGfxLoadingRepositorAssetCount" },
	{ 0x4000003551CDB3D1ULL, "guiLoadingStageProgress" },
	{ 0x4000000A51B758D7ULL, "guiAssetsLoadedTimer" }
};

static const char* LoadingGomName(ULONGLONG id)
{
	for (DWORD i = 0; i < ARRAYSIZE(g_loadingGomIds); ++i)
		if (g_loadingGomIds[i].id == id) return g_loadingGomIds[i].name;
	return NULL;
}

DWORD __fastcall GomDefinitionLookup_Hook(void* pThis, void* EDX,
	void* output, const ULONGLONG* typeId)
{
	ULONGLONG id = 0;
	const char* name = NULL;
	__try
	{
		if (typeId)
		{
			id = *typeId;
			name = LoadingGomName(id);
		}
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		name = NULL;
	}

	DWORD result = GomDefinitionLookup_r
		? GomDefinitionLookup_r(pThis, output, typeId) : 0;
	if (!name) return result;

	__try
	{
		DWORD first = output ? *(DWORD*)output : 0;
		DWORD second = output ? *(DWORD*)((BYTE*)output + 4) : 0;
		char stack[512] = { 0 };
		FormatRpcStack(stack, sizeof(stack));
		LONG count = InterlockedIncrement(&g_loadingGomLookupCount);
		Log::Write("LoadingGomHook",
			"count=%ld name=%s id=0x%08X%08X manager=%p output=%p values=%08X,%08X result=0x%08X stack=%s",
			count, name, (DWORD)(id >> 32), (DWORD)id, pThis, output,
			first, second, result, stack);
		if (first) LogReadinessMemory(name, first);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("LoadingGomHook",
			"name=%s id=0x%08X%08X result=0x%08X output-inspection-failed",
			name, (DWORD)(id >> 32), (DWORD)id, result);
	}
	return result;
}

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
		if (g_parsedInboundOpcode == 0xD5280283 ||
			g_parsedInboundOpcode == 0x0D446E80 ||  // CRT (area client replication transaction)
			g_parsedInboundOpcode == 0xA1D9E226 ||  // AreaAwarenessEntered
			g_parsedInboundOpcode == 0x1CA72F2D ||  // AreaSendAwarenessRange
			g_parsedInboundOpcode == 0x0ADFF9BF ||  // AreaRequestRPC
			g_parsedInboundOpcode == 0x0E71623B)    // AreaHackPack
			Log::Write("InboundRouteHook",
				"phase=parsed frame=%p opcode=0x%08X first=0x%04X second=0x%04X",
				frame, g_parsedInboundOpcode, g_parsedInboundFirst, g_parsedInboundSecond);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("InboundRouteHook", "phase=parse-inspection-failed frame=%p", frame);
	}
}

static void LogPhaseLifecycleArgument(const char* method, const char* phase,
	void* me, DWORD argument)
{
	__try
	{
		DWORD words[6] = { 0 };
		if (me)
			for (DWORD i = 0; i < ARRAYSIZE(words); ++i)
				words[i] = *(DWORD*)((BYTE*)me + i * sizeof(DWORD));
		Log::Write("PhaseLifecycleHook",
			"method=%s phase=%s me=%p argument=0x%08X words=%08X,%08X,%08X,%08X,%08X,%08X destroyDepth=%ld",
			method, phase, me, argument, words[0], words[1], words[2],
			words[3], words[4], words[5], g_phaseInfoDestroyDepth);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("PhaseLifecycleHook",
			"method=%s phase=%s me=%p argument=0x%08X inspection-failed destroyDepth=%ld",
			method, phase, me, argument, g_phaseInfoDestroyDepth);
	}
}

void __cdecl PhaseInfoDestroy_Hook(void* me, DWORD argument)
{
	InterlockedIncrement(&g_phaseInfoDestroyDepth);
	LogPhaseLifecycleArgument("phsPhaseInfo.OnReplicationNodeDestroy", "enter",
		me, argument);
	if (PhaseInfoDestroy_r) PhaseInfoDestroy_r(me, argument);
	LogPhaseLifecycleArgument("phsPhaseInfo.OnReplicationNodeDestroy", "return",
		me, argument);
	InterlockedDecrement(&g_phaseInfoDestroyDepth);
}

void __cdecl UpdateGatewayForInstance_Hook(void* me, DWORD argument)
{
	if (g_phaseInfoDestroyDepth > 0)
		LogPhaseLifecycleArgument("phsOracle.UpdateGatewayForInstance",
			"called-from-phase-info-destroy", me, argument);
	if (UpdateGatewayForInstance_r) UpdateGatewayForInstance_r(me, argument);
}

void __cdecl PlayerPhaseDataCreate_Hook(void* me, DWORD argument)
{
	LogPhaseLifecycleArgument("phsPlayerPhaseData.OnReplicationNodeCreate",
		"enter", me, argument);
	if (PlayerPhaseDataCreate_r) PlayerPhaseDataCreate_r(me, argument);
	LogPhaseLifecycleArgument("phsPlayerPhaseData.OnReplicationNodeCreate",
		"return", me, argument);
}

void __cdecl PlayerPhaseDataDestroy_Hook(void* me, DWORD argument)
{
	LogPhaseLifecycleArgument("phsPlayerPhaseData.OnReplicationNodeDestroy",
		"enter", me, argument);
	if (PlayerPhaseDataDestroy_r) PlayerPhaseDataDestroy_r(me, argument);
	LogPhaseLifecycleArgument("phsPlayerPhaseData.OnReplicationNodeDestroy",
		"return", me, argument);
}

static bool MatchesLifecyclePattern(const BYTE* candidate,
	const BYTE* pattern, SIZE_T length)
{
	for (SIZE_T i = 0; i < length; ++i)
	{
		if (candidate[i] != pattern[i]) return false;
		// Pinned resources use E8 FC FF FF FF for unresolved external calls.
		// The loader relocates only the rel32 operand; retain the CALL opcode
		// and every other byte of the longer method prefix as exact evidence.
		if (pattern[i] == 0xE8 && i + 4 < length &&
			pattern[i + 1] == 0xFC && pattern[i + 2] == 0xFF &&
			pattern[i + 3] == 0xFF && pattern[i + 4] == 0xFF)
			i += 4;
	}
	return true;
}

static DWORD FindExecutablePattern(const BYTE* pattern, SIZE_T length,
	DWORD* matchCount)
{
	DWORD first = 0;
	DWORD count = 0;
	ULONGLONG address = 0x00010000;
	MEMORY_BASIC_INFORMATION info = { 0 };
	// This large-address-aware April client materialises script bodies above
	// 2 GB. Keep arithmetic wide so the final 32-bit region cannot wrap.
	while (address < 0x100000000ULL &&
		VirtualQuery((void*)(DWORD)address, &info, sizeof(info)) == sizeof(info))
	{
		DWORD protection = info.Protect & 0xFF;
		bool executable = protection == PAGE_EXECUTE ||
			protection == PAGE_EXECUTE_READ ||
			protection == PAGE_EXECUTE_READWRITE ||
			protection == PAGE_EXECUTE_WRITECOPY;
		// HeroScript native bodies are materialised in private executable
		// allocations.  Excluding MEM_IMAGE is essential: the byte-pattern
		// constants below live in this hook DLL's image and would otherwise
		// self-match as four adjacent false method addresses.
		if (info.State == MEM_COMMIT && info.Type == MEM_PRIVATE && executable &&
			!(info.Protect & (PAGE_GUARD | PAGE_NOACCESS)) &&
			info.RegionSize >= length)
		{
			BYTE* end = (BYTE*)info.BaseAddress + info.RegionSize - length + 1;
			__try
			{
				for (BYTE* cursor = (BYTE*)info.BaseAddress; cursor < end; ++cursor)
				{
					if (*cursor == pattern[0] &&
						MatchesLifecyclePattern(cursor, pattern, length))
					{
						if (!first) first = (DWORD)cursor;
						++count;
					}
				}
			}
			__except (EXCEPTION_EXECUTE_HANDLER)
			{
				// Retry on the next CRT if an executable allocation changes.
			}
		}
		ULONGLONG next = (ULONGLONG)(DWORD)info.BaseAddress + info.RegionSize;
		if (next <= address) break;
		address = next;
	}
	if (matchCount) *matchCount = count;
	return first;
}

static void TryInstallPhaseLifecycleHooks()
{
	if (!g_tracePhaseLifecycle ||
		InterlockedCompareExchange(&g_phaseLifecycleInstallState, 1, 0) != 0)
		return;

	// SHA-256-pinned April resources and decrypted payload offsets:
	//   phsPhaseInfoClassMethods     65A4399D0102A007.scpt +0x0B78
	//   phsOracleClassMethods        C10C1F8290BE3551.scpt +0x32E3
	//   phsPlayerPhaseData methods   9308DE76F6AAF774.scpt +0x00B1/+0x03A1
	static const BYTE phaseInfoDestroyPattern[] =
		{ 0x55, 0x53, 0x57, 0x56, 0x83, 0xEC, 0x4C, 0xC7,
		  0x04, 0x24, 0x3F, 0x00, 0x00, 0x00, 0xE8, 0xFC,
		  0xFF, 0xFF, 0xFF, 0x8D, 0x74, 0x24, 0x40, 0x89,
		  0x74, 0x24, 0x04, 0xC7, 0x04, 0x24, 0x02, 0x00,
		  0x00, 0x00, 0xE8, 0xFC, 0xFF, 0xFF, 0xFF, 0x8D,
		  0x7C, 0x24, 0x38, 0x89, 0x7C, 0x24, 0x04, 0xC7,
		  0x04, 0x24, 0x02, 0x00, 0x00, 0x00 };
	static const BYTE updateGatewayPattern[] =
		{ 0x55, 0x53, 0x57, 0x56, 0x83, 0xEC, 0x6C, 0xC7,
		  0x04, 0x24, 0x4A, 0x01, 0x00, 0x00, 0xE8, 0xFC,
		  0xFF, 0xFF, 0xFF, 0x8D, 0x74, 0x24, 0x60, 0x89,
		  0x74, 0x24, 0x04, 0xC7, 0x04, 0x24, 0x11, 0x00,
		  0x00, 0x00, 0xE8, 0xFC, 0xFF, 0xFF, 0xFF, 0x8D,
		  0x7C, 0x24, 0x58, 0x89, 0x7C, 0x24, 0x04, 0xC7,
		  0x04, 0x24, 0x06, 0x00, 0x00, 0x00 };
	static const BYTE playerPhaseCreatePattern[] =
		{ 0x56, 0x83, 0xEC, 0x18, 0xC7, 0x04, 0x24, 0x05,
		  0x00, 0x00, 0x00, 0xE8, 0xFC, 0xFF, 0xFF, 0xFF,
		  0x8D, 0x74, 0x24, 0x10, 0x89, 0x74, 0x24, 0x04,
		  0xC7, 0x44, 0x24, 0x0C, 0xC6, 0x7C, 0x00, 0xE0,
		  0xC7, 0x44, 0x24, 0x08, 0xEC, 0x0D, 0xE7, 0xD0,
		  0xC7, 0x04, 0x24, 0x02, 0x00, 0x00, 0x00, 0xE8,
		  0xFC, 0xFF, 0xFF, 0xFF, 0x8B, 0x44, 0x24, 0x20 };
	static const BYTE playerPhaseDestroyPattern[] =
		{ 0x55, 0x53, 0x57, 0x56, 0x83, 0xEC, 0x2C, 0xC7,
		  0x04, 0x24, 0x1B, 0x00, 0x00, 0x00, 0xE8, 0xFC,
		  0xFF, 0xFF, 0xFF, 0x8B, 0x74, 0x24, 0x40, 0x89,
		  0x34, 0x24, 0xC7, 0x44, 0x24, 0x04, 0x01, 0x00,
		  0x00, 0x00, 0xE8, 0xFC, 0xFF, 0xFF, 0xFF, 0x89,
		  0x04, 0x24, 0xC7, 0x44, 0x24, 0x04, 0x02, 0x00,
		  0x00, 0x00, 0xE8, 0xFC, 0xFF, 0xFF, 0xFF, 0x09 };

	DWORD destroyCount = 0, updateCount = 0, createCount = 0,
		destroyPhaseDataCount = 0;
	DWORD destroy = FindExecutablePattern(phaseInfoDestroyPattern,
		sizeof(phaseInfoDestroyPattern), &destroyCount);
	DWORD update = FindExecutablePattern(updateGatewayPattern,
		sizeof(updateGatewayPattern), &updateCount);
	DWORD create = FindExecutablePattern(playerPhaseCreatePattern,
		sizeof(playerPhaseCreatePattern), &createCount);
	DWORD destroyPhaseData = FindExecutablePattern(playerPhaseDestroyPattern,
		sizeof(playerPhaseDestroyPattern), &destroyPhaseDataCount);

	if (destroyCount != 1 || updateCount != 1 || createCount != 1 ||
		destroyPhaseDataCount != 1)
	{
		Log::Write("PhaseLifecycleHook",
			"discovery pending/ambiguous phaseInfoDestroy=%p/%u updateGateway=%p/%u playerPhaseCreate=%p/%u playerPhaseDestroy=%p/%u",
			(void*)destroy, destroyCount, (void*)update, updateCount,
			(void*)create, createCount, (void*)destroyPhaseData,
			destroyPhaseDataCount);
		InterlockedExchange(&g_phaseLifecycleInstallState, 0);
		return;
	}

	const DWORD addresses[] = { destroy, update, create, destroyPhaseData };
	const SIZE_T lengths[] = { sizeof(phaseInfoDestroyPattern),
		sizeof(updateGatewayPattern), sizeof(playerPhaseCreatePattern),
		sizeof(playerPhaseDestroyPattern) };
	for (SIZE_T i = 0; i < ARRAYSIZE(addresses); ++i)
		for (SIZE_T j = i + 1; j < ARRAYSIZE(addresses); ++j)
			if ((ULONGLONG)addresses[i] < (ULONGLONG)addresses[j] + lengths[j] &&
				(ULONGLONG)addresses[j] < (ULONGLONG)addresses[i] + lengths[i])
			{
				Log::Write("PhaseLifecycleHook", "discovery rejected: method prefixes overlap");
				InterlockedExchange(&g_phaseLifecycleInstallState, 0);
				return;
			}

	PhaseInfoDestroy_r = (PhaseLifecycleMethod_t)destroy;
	UpdateGatewayForInstance_r = (PhaseLifecycleMethod_t)update;
	PlayerPhaseDataCreate_r = (PhaseLifecycleMethod_t)create;
	PlayerPhaseDataDestroy_r = (PhaseLifecycleMethod_t)destroyPhaseData;

	LONG result = DetourTransactionBegin();
	if (result == NO_ERROR) result = DetourUpdateThread(GetCurrentThread());
	if (result == NO_ERROR) result = DetourAttach(
		&(PVOID&)PhaseInfoDestroy_r, (PVOID)PhaseInfoDestroy_Hook);
	if (result == NO_ERROR) result = DetourAttach(
		&(PVOID&)UpdateGatewayForInstance_r, (PVOID)UpdateGatewayForInstance_Hook);
	if (result == NO_ERROR) result = DetourAttach(
		&(PVOID&)PlayerPhaseDataCreate_r, (PVOID)PlayerPhaseDataCreate_Hook);
	if (result == NO_ERROR) result = DetourAttach(
		&(PVOID&)PlayerPhaseDataDestroy_r, (PVOID)PlayerPhaseDataDestroy_Hook);
	if (result == NO_ERROR) result = DetourTransactionCommit();
	else DetourTransactionAbort();

	if (result == NO_ERROR)
	{
		InterlockedExchange(&g_phaseLifecycleInstallState, 2);
		Log::Write("PhaseLifecycleHook",
			"installed discovery=private-full32-relocated-prefix-v2 phaseInfoDestroy=%p updateGateway=%p playerPhaseCreate=%p playerPhaseDestroy=%p",
			(void*)destroy, (void*)update, (void*)create, (void*)destroyPhaseData);
	}
	else
	{
		InterlockedExchange(&g_phaseLifecycleInstallState, 3);
		Log::Write("PhaseLifecycleHook", "install failed result=%ld", result);
	}
}

void __fastcall AreaMessageDispatch_Hook(void* pThis, void* EDX, DWORD arg1, DWORD arg2, DWORD arg3, void* arg4)
	{
		bool isCrt = (arg2 == 0x0D446E80);
		LONG count = isCrt ? InterlockedIncrement(&g_areaMessageCount) : 0;
		if (isCrt)
		{
			DWORD member = 0, consumer = 0, gate = 0, applyFunc = 0;
			__try
			{
				member = *(DWORD*)((BYTE*)pThis + 0x0C);
				consumer = member ? *(DWORD*)((BYTE*)member + 0x40) : 0;
				gate = *(DWORD*)((BYTE*)pThis + 0x38);
				{ DWORD vt = gate ? *(DWORD*)gate : 0; applyFunc = vt ? *(DWORD*)((BYTE*)vt + 0xB4) : 0; }
			}
			__except (EXCEPTION_EXECUTE_HANDLER) { consumer = 0; gate = 0; applyFunc = 0; }
			DWORD consumerRva = (g_clientImageBase && consumer >= g_clientImageBase && consumer < g_clientImageBase + g_clientImageSize) ? consumer - g_clientImageBase : 0;
			DWORD applyRva = (g_clientImageBase && applyFunc >= g_clientImageBase && applyFunc < g_clientImageBase + g_clientImageSize) ? applyFunc - g_clientImageBase : 0;
			Log::Write("CrtApplyHook", "crt count=%ld pThis=%p opcode=0x%08X reader=%p consumer=0x%08X consumerRva=0x%08X gate=0x%08X apply=0x%08X applyRva=0x%08X", count, pThis, arg2, arg4, consumer, consumerRva, gate, applyFunc, applyRva);
		}
		if (AreaMessageDispatch_r) AreaMessageDispatch_r(pThis, arg1, arg2, arg3, arg4);
		if (isCrt)
		{
			Log::Write("CrtApplyHook", "crt count=%ld applied pThis=%p", count, pThis);
			// Script method bodies are allocated while CRTs are applied. Retry the
			// byte-exact discovery after each successful CRT until all four named
			// lifecycle callbacks are present, then install the observer once.
			TryInstallPhaseLifecycleHooks();
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
		void* caller = _ReturnAddress();
		DWORD callerRva = (g_clientImageBase && (DWORD)caller >= g_clientImageBase &&
			(DWORD)caller < g_clientImageBase + g_clientImageSize)
			? (DWORD)caller - g_clientImageBase : 0;
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
			char stack[1024] = { 0 };
			FormatRpcStack(stack, sizeof(stack));
			char hex[3 * 64 + 1] = { 0 };
			for (DWORD i = 0; payload && i < 64; ++i)
				_snprintf(hex + i * 3, sizeof(hex) - i * 3, "%02X%s",
					payload[i], (i < 63) ? " " : "");
			Log::Write("EventDispatchHook",
				"class=%u count=%ld caller=%p callerRva=0x%08X envelope=%p payload=%p logicalLen=%u hash=0x%08X changed=%u manager=%p vtable=%p handler=%p handlerRva=0x%08X bytes=%s stack=%s",
				eventClass, count, caller, callerRva, envelope, payload, logicalLength, hash, changed ? 1 : 0,
				(void*)manager, (void*)vtable, (void*)handler,
				(g_clientImageBase && handler >= g_clientImageBase &&
				 handler < g_clientImageBase + g_clientImageSize)
					? handler - g_clientImageBase : 0,
				hex, stack);
		}
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("EventDispatchHook", "inspection failed: class=%u envelope=%p", eventClass, envelope);
	}

	if (EventDispatch_r)
		EventDispatch_r(eventClass, envelope);
}

void __cdecl Class1EventBridge_Hook(void* unused, void* payload)
{
	void* previousRecipient = g_class1Recipient;
	void* previousMethod = g_class1Method;
	__try
	{
		void* recipient = ResolveClass1Recipient_r ? ResolveClass1Recipient_r() : NULL;
		void* vtable = recipient ? *(void**)recipient : NULL;
		void* method = vtable ? *(void**)((BYTE*)vtable + 4) : NULL;
		g_class1Recipient = recipient;
		g_class1Method = method;
		Log::Write("Class1BridgeHook",
			"phase=enter recipient=%p vtable=%p method=%p methodRva=0x%08X unused=%p payload=%p",
			recipient, vtable, method,
			(g_clientImageBase && (DWORD)method >= g_clientImageBase &&
			 (DWORD)method < g_clientImageBase + g_clientImageSize)
				? (DWORD)method - g_clientImageBase : 0,
			unused, payload);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("Class1BridgeHook", "phase=inspection-failed payload=%p", payload);
	}

	if (Class1EventBridge_r)
		Class1EventBridge_r(unused, payload);

	Log::Write("Class1BridgeHook", "phase=return recipient=%p payload=%p",
		g_class1Recipient, payload);
	g_class1Recipient = previousRecipient;
	g_class1Method = previousMethod;
}

DWORD __fastcall ScriptDispatch_Hook(void* pThis, void* EDX, DWORD a1, DWORD a2,
	DWORD a3, DWORD a4, DWORD a5, DWORD a6, DWORD a7, DWORD a8)
{
	LONG count = InterlockedIncrement(&g_scriptDispatchCount);
	void* caller = _ReturnAddress();
	DWORD callerRva = g_clientImageBase ? (DWORD)caller - g_clientImageBase : 0;
	if (count <= 20)
		Log::Write("ScriptDispatchHook",
			"phase=enter count=%ld this=%p callerRva=0x%08X args=%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X",
			count, pThis, callerRva, a1, a2, a3, a4, a5, a6, a7, a8);

	// This stack signature repeatedly encloses the readiness poll. It identifies
	// a chrPlayerCharacter replication path, but does not identify a Hero method.
	// Dump the correlated objects without modifying them.
	if (a3 == 0x7D03034B && a4 == 0xD000199A)
	{
		Log::Write("ReadinessVmHook",
			"phase=enter this=%p callerRva=0x%08X character=%08X%08X method=%08X%08X contexts=%08X,%08X,%08X,%08X",
			pThis, callerRva, a2, a1, a4, a3, a5, a6, a7, a8);
		LogReadinessMemory("this", (DWORD)pThis);
		LogReadinessMemory("context5", a5);
		LogReadinessMemory("context6", a6);
		LogReadinessMemory("context7", a7);
		LogReadinessMemory("context8", a8);
		if (InterlockedCompareExchange(&g_readinessVmDeepDumped, 1, 0) == 0)
		{
			Log::Write("ReadinessVmHook", "phase=deep-dump begin");
			LogReadinessPointers("this.ptr", (DWORD)pThis);
			LogReadinessPointers("context5.ptr", a5);
			LogReadinessPointers("context6.ptr", a6);
			LogReadinessPointers("context7.ptr", a7);
			Log::Write("ReadinessVmHook", "phase=deep-dump end");
		}
		char stack[512] = { 0 };
		FormatRpcStack(stack, sizeof(stack));
		Log::Write("ReadinessVmHook", "phase=enter stack=%s", stack);
	}

	DWORD activeIndex = g_activeScriptDepth < ARRAYSIZE(g_activeScriptDispatch)
		? g_activeScriptDepth : ARRAYSIZE(g_activeScriptDispatch) - 1;
	ScriptDispatchSample* active = &g_activeScriptDispatch[activeIndex];
	active->tick = GetTickCount();
	active->callerRva = callerRva;
	active->pThis = (DWORD)pThis;
	active->args[0] = a1; active->args[1] = a2; active->args[2] = a3; active->args[3] = a4;
	active->args[4] = a5; active->args[5] = a6; active->args[6] = a7; active->args[7] = a8;
	active->result = 0;
	++g_activeScriptDepth;

	DWORD result = ScriptDispatch_r
		? ScriptDispatch_r(pThis, a1, a2, a3, a4, a5, a6, a7, a8) : 0;
	if (g_activeScriptDepth) --g_activeScriptDepth;
	active->result = result;

	ScriptDispatchSample* sample = &g_scriptSamples[g_scriptSampleNext % ARRAYSIZE(g_scriptSamples)];
	sample->tick = GetTickCount();
	sample->callerRva = callerRva;
	sample->pThis = (DWORD)pThis;
	sample->args[0] = a1; sample->args[1] = a2; sample->args[2] = a3; sample->args[3] = a4;
	sample->args[4] = a5; sample->args[5] = a6; sample->args[6] = a7; sample->args[7] = a8;
	sample->result = result;
	++g_scriptSampleNext;

	if (count <= 20)
		Log::Write("ScriptDispatchHook",
			"phase=return count=%ld callerRva=0x%08X result=0x%08X",
			count, callerRva, result);
	return result;
}

static void FormatRpcStack(char* output, size_t outputSize)
{
	if (!output || outputSize == 0) return;
	output[0] = '\0';

	PVOID frames[32] = { 0 };
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

// Capture executable frames outside the main client image once. These may be
// hooks or other loaded modules; they are correlation evidence only and must
// not be labelled as generated Hero code without separately identifying their
// allocation/module owner.
static void LogGeneratedRpcFrames()
{
	PVOID frames[16] = { 0 };
	USHORT count = CaptureStackBackTrace(0, ARRAYSIZE(frames), frames, NULL);
	for (USHORT i = 0; i < count; ++i)
	{
		DWORD address = (DWORD)frames[i];
		MEMORY_BASIC_INFORMATION info = { 0 };
		if (!VirtualQuery((void*)address, &info, sizeof(info)) ||
			info.State != MEM_COMMIT)
			continue;
		if (g_clientImageBase && address >= g_clientImageBase &&
			address < g_clientImageBase + g_clientImageSize)
			continue;
		DWORD protection = info.Protect & 0xff;
		if (protection != PAGE_EXECUTE && protection != PAGE_EXECUTE_READ &&
			protection != PAGE_EXECUTE_READWRITE && protection != PAGE_EXECUTE_WRITECOPY)
			continue;
		char label[64] = { 0 };
		_snprintf(label, sizeof(label), "external-exec-frame[%u]-minus32", i);
		LogReadinessMemory(label, address >= 32 ? address - 32 : address);
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
		if (operationId == 0xF5F540F2)
		{
			if (InterlockedCompareExchange(&g_readinessCodeDumped, 1, 0) == 0)
				LogGeneratedRpcFrames();
			Log::Write("ReadinessActiveHook", "depth=%u", g_activeScriptDepth);
			DWORD activeCount = g_activeScriptDepth < ARRAYSIZE(g_activeScriptDispatch)
				? g_activeScriptDepth : ARRAYSIZE(g_activeScriptDispatch);
			for (DWORD i = 0; i < activeCount; ++i)
			{
				ScriptDispatchSample* active = &g_activeScriptDispatch[i];
				Log::Write("ReadinessActiveHook",
					"depth=%u ageMs=%u this=%p callerRva=0x%08X args=%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X",
					i + 1, GetTickCount() - active->tick, (void*)active->pThis,
					active->callerRva, active->args[0], active->args[1],
					active->args[2], active->args[3], active->args[4], active->args[5],
					active->args[6], active->args[7]);
			}
			DWORD available = g_scriptSampleNext < ARRAYSIZE(g_scriptSamples)
				? g_scriptSampleNext : ARRAYSIZE(g_scriptSamples);
			DWORD now = GetTickCount();
			for (DWORD offset = available; offset > 0; --offset)
			{
				DWORD sequence = g_scriptSampleNext - offset;
				ScriptDispatchSample* sample = &g_scriptSamples[sequence % ARRAYSIZE(g_scriptSamples)];
				Log::Write("ReadinessContextHook",
					"sequence=%u ageMs=%u callerRva=0x%08X args=%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X result=0x%08X",
					sequence, now - sample->tick, sample->callerRva,
					sample->args[0], sample->args[1], sample->args[2], sample->args[3],
					sample->args[4], sample->args[5], sample->args[6], sample->args[7],
					sample->result);
			}
		}
		char stack[512] = { 0 };
		FormatRpcStack(stack, sizeof(stack));
		Log::Write("AreaRpcHook",
			"sender=%p blob=%p len=%u marker=0x%02X target=0x%08X operation=0x%08X class1Recipient=%p class1Method=%p class1MethodRva=0x%08X bytes=%s%s stack=%s",
			pThis, blob, length, (bytes && length) ? bytes[0] : 0,
			targetId, operationId, g_class1Recipient, g_class1Method,
			(g_clientImageBase && (DWORD)g_class1Method >= g_clientImageBase &&
			 (DWORD)g_class1Method < g_clientImageBase + g_clientImageSize)
				? (DWORD)g_class1Method - g_clientImageBase : 0,
			hex, (length > shown) ? " ..." : "", stack);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("AreaRpcHook", "Could not inspect blob=%p caller=%p", blob, _ReturnAddress());
	}

	if (AreaRpcSend_r)
		AreaRpcSend_r(pThis, blob);
}

void __fastcall AreaRpcReceiveBridge_Hook(void* pThis, void* EDX,
	void* context, void* rpcMessage)
{
	LONG count = InterlockedIncrement(&g_areaRpcReceiveCount);
	__try
	{
		DWORD interfaceObject = g_clientImageBase
			? *(DWORD*)(g_clientImageBase + (0x01491A88 - 0x00400000)) : 0;
		DWORD interfaceVtable = interfaceObject ? *(DWORD*)interfaceObject : 0;
		DWORD slots[5] = { 0 };
		if (interfaceVtable)
			for (DWORD i = 0; i < ARRAYSIZE(slots); ++i)
				slots[i] = *(DWORD*)(interfaceVtable + i * sizeof(DWORD));
		DWORD listenerObject = pThis ? *(DWORD*)((BYTE*)pThis + 0x2C) : 0;
		DWORD listenerVtable = listenerObject ? *(DWORD*)listenerObject : 0;
		DWORD listenerSlots[10] = { 0 };
		if (listenerVtable)
			for (DWORD i = 0; i < ARRAYSIZE(listenerSlots); ++i)
				listenerSlots[i] = *(DWORD*)(listenerVtable + i * sizeof(DWORD));
		BYTE listenerMode = listenerObject ? *(BYTE*)(listenerObject + 0x0C) : 0;

		// 0x00715760 wraps the received byte range in an engine stream, then
		// dispatches it through slot +0x74 of this process-global service.
		// Resolve the concrete virtual target here without altering the call.
		DWORD rpcServiceRoot = g_clientImageBase
			? *(DWORD*)(g_clientImageBase + (0x014926F0 - 0x00400000)) : 0;
		DWORD rpcServiceLink = rpcServiceRoot ? *(DWORD*)(rpcServiceRoot + 0x04) : 0;
		DWORD rpcServiceOffset = rpcServiceLink ? *(DWORD*)(rpcServiceLink + 0x04) : 0;
		DWORD rpcServiceObject = rpcServiceRoot
			? rpcServiceRoot + rpcServiceOffset + 0x04 : 0;
		DWORD rpcServiceVtable = rpcServiceObject ? *(DWORD*)rpcServiceObject : 0;
		DWORD rpcServiceDispatch = rpcServiceVtable
			? *(DWORD*)(rpcServiceVtable + 0x74) : 0;

		char messageHex[3 * 64 + 1] = { 0 };
		BYTE* messageBytes = (BYTE*)rpcMessage;
		for (DWORD i = 0; messageBytes && i < 64; ++i)
			_snprintf(messageHex + i * 3, sizeof(messageHex) - i * 3,
				"%02X%s", messageBytes[i], (i < 63) ? " " : "");
		DWORD blobLength = rpcMessage ? *(DWORD*)((BYTE*)rpcMessage + 0x0C) : 0;
		BYTE* blobBytes = (rpcMessage && blobLength <= 4096)
			? *(BYTE**)((BYTE*)rpcMessage + 0x10) : NULL;
		char blobHex[3 * 64 + 1] = { 0 };
		DWORD blobShown = blobLength < 64 ? blobLength : 64;
		for (DWORD i = 0; blobBytes && i < blobShown; ++i)
			_snprintf(blobHex + i * 3, sizeof(blobHex) - i * 3,
				"%02X%s", blobBytes[i], (i + 1 < blobShown) ? " " : "");

		char stack[512] = { 0 };
		FormatRpcStack(stack, sizeof(stack));
		Log::Write("AreaRpcReceiveHook",
			"count=%ld bridge=%p context=%p message=%p interface=%p vtable=%p slots=%p/%p/%p/%p/%p slotRvas=%08X/%08X/%08X/%08X/%08X listener=%p listenerMode=%u listenerVtable=%p listenerSlots=%p/%p/%p/%p/%p/%p/%p/%p/%p/%p listenerSlotRvas=%08X/%08X/%08X/%08X/%08X/%08X/%08X/%08X/%08X/%08X rpcServiceRoot=%p rpcServiceObject=%p rpcServiceVtable=%p rpcServiceDispatch=%p rpcServiceDispatchRva=%08X blobLen=%u blob=%s messageBytes=%s stack=%s",
			count, pThis, context, rpcMessage, (void*)interfaceObject,
			(void*)interfaceVtable, (void*)slots[0], (void*)slots[1],
			(void*)slots[2], (void*)slots[3], (void*)slots[4],
			(g_clientImageBase && slots[0] >= g_clientImageBase && slots[0] < g_clientImageBase + g_clientImageSize) ? slots[0] - g_clientImageBase : 0,
			(g_clientImageBase && slots[1] >= g_clientImageBase && slots[1] < g_clientImageBase + g_clientImageSize) ? slots[1] - g_clientImageBase : 0,
			(g_clientImageBase && slots[2] >= g_clientImageBase && slots[2] < g_clientImageBase + g_clientImageSize) ? slots[2] - g_clientImageBase : 0,
			(g_clientImageBase && slots[3] >= g_clientImageBase && slots[3] < g_clientImageBase + g_clientImageSize) ? slots[3] - g_clientImageBase : 0,
			(g_clientImageBase && slots[4] >= g_clientImageBase && slots[4] < g_clientImageBase + g_clientImageSize) ? slots[4] - g_clientImageBase : 0,
			(void*)listenerObject, listenerMode, (void*)listenerVtable,
			(void*)listenerSlots[0], (void*)listenerSlots[1], (void*)listenerSlots[2],
			(void*)listenerSlots[3], (void*)listenerSlots[4], (void*)listenerSlots[5],
			(void*)listenerSlots[6], (void*)listenerSlots[7], (void*)listenerSlots[8],
			(void*)listenerSlots[9],
			(g_clientImageBase && listenerSlots[0] >= g_clientImageBase && listenerSlots[0] < g_clientImageBase + g_clientImageSize) ? listenerSlots[0] - g_clientImageBase : 0,
			(g_clientImageBase && listenerSlots[1] >= g_clientImageBase && listenerSlots[1] < g_clientImageBase + g_clientImageSize) ? listenerSlots[1] - g_clientImageBase : 0,
			(g_clientImageBase && listenerSlots[2] >= g_clientImageBase && listenerSlots[2] < g_clientImageBase + g_clientImageSize) ? listenerSlots[2] - g_clientImageBase : 0,
			(g_clientImageBase && listenerSlots[3] >= g_clientImageBase && listenerSlots[3] < g_clientImageBase + g_clientImageSize) ? listenerSlots[3] - g_clientImageBase : 0,
			(g_clientImageBase && listenerSlots[4] >= g_clientImageBase && listenerSlots[4] < g_clientImageBase + g_clientImageSize) ? listenerSlots[4] - g_clientImageBase : 0,
			(g_clientImageBase && listenerSlots[5] >= g_clientImageBase && listenerSlots[5] < g_clientImageBase + g_clientImageSize) ? listenerSlots[5] - g_clientImageBase : 0,
			(g_clientImageBase && listenerSlots[6] >= g_clientImageBase && listenerSlots[6] < g_clientImageBase + g_clientImageSize) ? listenerSlots[6] - g_clientImageBase : 0,
			(g_clientImageBase && listenerSlots[7] >= g_clientImageBase && listenerSlots[7] < g_clientImageBase + g_clientImageSize) ? listenerSlots[7] - g_clientImageBase : 0,
			(g_clientImageBase && listenerSlots[8] >= g_clientImageBase && listenerSlots[8] < g_clientImageBase + g_clientImageSize) ? listenerSlots[8] - g_clientImageBase : 0,
			(g_clientImageBase && listenerSlots[9] >= g_clientImageBase && listenerSlots[9] < g_clientImageBase + g_clientImageSize) ? listenerSlots[9] - g_clientImageBase : 0,
			(void*)rpcServiceRoot, (void*)rpcServiceObject,
			(void*)rpcServiceVtable, (void*)rpcServiceDispatch,
			(g_clientImageBase && rpcServiceDispatch >= g_clientImageBase && rpcServiceDispatch < g_clientImageBase + g_clientImageSize) ? rpcServiceDispatch - g_clientImageBase : 0,
			blobLength, blobHex, messageHex, stack);
	}
	__except (EXCEPTION_EXECUTE_HANDLER)
	{
		Log::Write("AreaRpcReceiveHook",
			"inspection failed: count=%ld bridge=%p context=%p message=%p",
			count, pThis, context, rpcMessage);
	}

	if (AreaRpcReceiveBridge_r)
		AreaRpcReceiveBridge_r(pThis, context, rpcMessage);
}

bool __stdcall PackedSigned64Read_Hook(void* stream, void* output)
{
	void* caller = _ReturnAddress();
	bool result = PackedSigned64Read_r
		? PackedSigned64Read_r(stream, output) : false;
	DWORD callerRva = g_clientImageBase ? (DWORD)caller - g_clientImageBase : 0;
	if (callerRva == (0x005BDA95 - 0x00400000))
	{
		__try
		{
			DWORD low = result && output ? *(DWORD*)output : 0;
			DWORD high = result && output ? *(DWORD*)((BYTE*)output + 4) : 0;
			Log::Write("AreaRpcSelectorHook",
				"success=%u selector=%08X:%08X stream=%p output=%p callerRva=0x%08X",
				result ? 1 : 0, high, low, stream, output, callerRva);
		}
		__except (EXCEPTION_EXECUTE_HANDLER)
		{
			Log::Write("AreaRpcSelectorHook",
				"inspection failed success=%u stream=%p output=%p callerRva=0x%08X",
				result ? 1 : 0, stream, output, callerRva);
		}
	}
	return result;
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

			BYTE* receiveBridge = (BYTE*)(baseAddr + (0x00642CA0 - 0x00400000));
			static const BYTE expectedReceiveBridge[] =
				{ 0x55, 0x8B, 0xEC, 0x56, 0x8B, 0xF1, 0x8B, 0x0D };
			if (memcmp(receiveBridge, expectedReceiveBridge, sizeof(expectedReceiveBridge)) == 0)
				AreaRpcReceiveBridge_r = (AreaRpcReceiveBridge_t)receiveBridge;
			else
				Log::Write("AreaRpcReceiveHook",
					"Unsupported client bytes at %p; inbound RPC bridge hook not installed",
					receiveBridge);

			BYTE* packedSigned64Read = (BYTE*)(baseAddr + (0x004C9A10 - 0x00400000));
			static const BYTE expectedPackedSigned64Read[] =
				{ 0x55, 0x8B, 0xEC, 0x83, 0xEC, 0x08 };
			if (memcmp(packedSigned64Read, expectedPackedSigned64Read,
				sizeof(expectedPackedSigned64Read)) == 0)
				PackedSigned64Read_r = (PackedSigned64Read_t)packedSigned64Read;
			else
				Log::Write("AreaRpcSelectorHook",
					"Unsupported client bytes at %p; selector observer not installed",
					packedSigned64Read);
		}

		char traceEvents[8] = { 0 };
		char tracePhaseLifecycle[8] = { 0 };
		g_tracePhaseLifecycle =
			GetEnvironmentVariableA("SWTOR_TRACE_PHASE_LIFECYCLE",
				tracePhaseLifecycle, sizeof(tracePhaseLifecycle)) > 0 &&
			tracePhaseLifecycle[0] == '1';
		if (g_tracePhaseLifecycle)
			Log::Write("PhaseLifecycleHook",
				"enabled; discovery will begin after each applied CRT");

		if (GetEnvironmentVariableA("SWTOR_TRACE_EVENT_DISPATCH", traceEvents, sizeof(traceEvents)) > 0 && traceEvents[0] == '1')
		{
			BYTE* candidate = (BYTE*)(baseAddr + (0x005D12A0 - 0x00400000));
			static const BYTE expected[] = { 0x55, 0x8B, 0xEC, 0x83, 0xE4, 0xF8 };
			if (memcmp(candidate, expected, sizeof(expected)) == 0)
				EventDispatch_r = (EventDispatch_t)candidate;
			else
				Log::Write("EventDispatchHook", "Unsupported client bytes at %p; event hook not installed", candidate);

			BYTE* class1Bridge = (BYTE*)(baseAddr + (0x00BD4910 - 0x00400000));
			static const BYTE expectedClass1Bridge[] = { 0x55, 0x8B, 0xEC, 0xE8 };
			if (memcmp(class1Bridge, expectedClass1Bridge, sizeof(expectedClass1Bridge)) == 0)
			{
				Class1EventBridge_r = (Class1EventBridge_t)class1Bridge;
				ResolveClass1Recipient_r = (ResolveClass1Recipient_t)
					(baseAddr + (0x006340E0 - 0x00400000));
			}
			else
				Log::Write("Class1BridgeHook", "Unsupported client bytes at %p; bridge hook not installed", class1Bridge);

			BYTE* scriptDispatch = (BYTE*)(baseAddr + (0x005BE0E0 - 0x00400000));
			static const BYTE expectedScriptDispatch[] = { 0x55, 0x8B, 0xEC, 0x6A, 0xFF };
			if (memcmp(scriptDispatch, expectedScriptDispatch, sizeof(expectedScriptDispatch)) == 0)
				ScriptDispatch_r = (ScriptDispatch_t)scriptDispatch;
			else
				Log::Write("ScriptDispatchHook", "Unsupported client bytes at %p; script hook not installed", scriptDispatch);

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

			// Area message dispatcher (CRT apply path). Prologue verified from
			// Diagnostics/swtor-disasm.txt at 0x0064ED70: 55 8B EC 6A FF.
			BYTE* areaDispatch = (BYTE*)(baseAddr + (0x0064ED70 - 0x00400000));
			static const BYTE expectedAreaDispatch[] = { 0x55, 0x8B, 0xEC, 0x6A, 0xFF };
			if (memcmp(areaDispatch, expectedAreaDispatch, sizeof(expectedAreaDispatch)) == 0)
				AreaMessageDispatch_r = (AreaMessageDispatch_t)areaDispatch;
			else
				Log::Write("CrtApplyHook", "Unsupported client bytes at %p; CRT-apply observer not installed", areaDispatch);

			BYTE* routeLookup = (BYTE*)(baseAddr + (0x009ECAA0 - 0x00400000));
			static const BYTE expectedRouteLookup[] = { 0x55, 0x8B, 0xEC };
			if (memcmp(routeLookup, expectedRouteLookup, sizeof(expectedRouteLookup)) == 0)
				RouteLookup_r = (RouteLookup_t)routeLookup;
			else
				Log::Write("InboundRouteHook", "Unsupported lookup bytes at %p; route hook not installed", routeLookup);
		}

		char traceLoadingScreen[8] = { 0 };
		if (GetEnvironmentVariableA("SWTOR_TRACE_LOADING_SCREEN", traceLoadingScreen,
			sizeof(traceLoadingScreen)) > 0 && traceLoadingScreen[0] == '1')
		{
			BYTE* gomLookup = (BYTE*)(baseAddr + (0x004A95B0 - 0x00400000));
			static const BYTE expectedGomLookup[] = { 0x55, 0x8B, 0xEC, 0x6A, 0xFF };
			if (memcmp(gomLookup, expectedGomLookup, sizeof(expectedGomLookup)) == 0)
				GomDefinitionLookup_r = (GomDefinitionLookup_t)gomLookup;
			else
				Log::Write("LoadingGomHook",
					"Unsupported client bytes at %p; loading-screen GOM observer not installed",
					gomLookup);
		}

		char tracePlayerFields[8] = { 0 };
		if (GetEnvironmentVariableA("SWTOR_TRACE_PLAYER_FIELDS", tracePlayerFields,
			sizeof(tracePlayerFields)) > 0 && tracePlayerFields[0] == '1')
		{
			BYTE* getField = (BYTE*)(baseAddr + (0x004F5A00 - 0x00400000));
			static const BYTE expectedGetField[] =
				{ 0x55, 0x8B, 0xEC, 0x83, 0xE4, 0xF8, 0x6A, 0xFF };
			if (memcmp(getField, expectedGetField, sizeof(expectedGetField)) == 0)
				HeroClassGetField_r = (HeroClassGetField_t)getField;
			else
				Log::Write("PlayerFieldHook",
					"Unsupported client bytes at %p; player-field observer not installed",
					getField);

			BYTE* setEnum = (BYTE*)(baseAddr + (0x005D9FF0 - 0x00400000));
			static const BYTE expectedSetEnum[] =
				{ 0x55, 0x8B, 0xEC, 0x83, 0xE4, 0xF8, 0x8B, 0x4D, 0x08 };
			if (memcmp(setEnum, expectedSetEnum, sizeof(expectedSetEnum)) == 0)
				SetNodeFieldEnum_r = (SetNodeFieldEnum_t)setEnum;
			else
				Log::Write("SetNodeFieldEnumHook",
					"Unsupported client bytes at %p; enum-field write observer not installed",
					setEnum);
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
	if (result == NO_ERROR && AreaRpcReceiveBridge_r) result = DetourAttach(&(PVOID&)AreaRpcReceiveBridge_r, (PVOID)AreaRpcReceiveBridge_Hook);
	if (result == NO_ERROR && PackedSigned64Read_r) result = DetourAttach(&(PVOID&)PackedSigned64Read_r, (PVOID)PackedSigned64Read_Hook);
	if (result == NO_ERROR && EventDispatch_r) result = DetourAttach(&(PVOID&)EventDispatch_r, (PVOID)EventDispatch_Hook);
	if (result == NO_ERROR && Class1EventBridge_r) result = DetourAttach(&(PVOID&)Class1EventBridge_r, (PVOID)Class1EventBridge_Hook);
	if (result == NO_ERROR && ScriptDispatch_r) result = DetourAttach(&(PVOID&)ScriptDispatch_r, (PVOID)ScriptDispatch_Hook);
	if (result == NO_ERROR && ReadPackedString_r) result = DetourAttach(&(PVOID&)ReadPackedString_r, (PVOID)ReadPackedString_Hook);
	if (result == NO_ERROR && OmegaMessage_r) result = DetourAttach(&(PVOID&)OmegaMessage_r, (PVOID)OmegaMessage_Hook);
	if (result == NO_ERROR && ParseInboundFrame_r) result = DetourAttach(&(PVOID&)ParseInboundFrame_r, (PVOID)ParseInboundFrame_Hook);
	if (result == NO_ERROR && AreaMessageDispatch_r) result = DetourAttach(&(PVOID&)AreaMessageDispatch_r, (PVOID)AreaMessageDispatch_Hook);
	if (result == NO_ERROR && RouteLookup_r) result = DetourAttach(&(PVOID&)RouteLookup_r, (PVOID)RouteLookup_Hook);
	if (result == NO_ERROR && GomDefinitionLookup_r) result = DetourAttach(&(PVOID&)GomDefinitionLookup_r, (PVOID)GomDefinitionLookup_Hook);
	if (result == NO_ERROR && HeroClassGetField_r) result = DetourAttach(&(PVOID&)HeroClassGetField_r, (PVOID)HeroClassGetField_Hook);
	if (result == NO_ERROR && SetNodeFieldEnum_r) result = DetourAttach(&(PVOID&)SetNodeFieldEnum_r, (PVOID)SetNodeFieldEnum_Hook);
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
	Log::Write("NexusToR", "Network and SSL hooks installed; RPC trace=%s event trace=%s loading-screen trace=%s player-field read=%s write=%s CRT-apply=%s",
		AreaRpcSend_r ? "enabled" : "disabled", EventDispatch_r ? "enabled" : "disabled",
		GomDefinitionLookup_r ? "enabled" : "disabled",
		HeroClassGetField_r ? "enabled" : "disabled",
		SetNodeFieldEnum_r ? "enabled" : "disabled",
		AreaMessageDispatch_r ? "enabled" : "disabled");
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
