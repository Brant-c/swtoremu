// Event argument/object reads only; no scans or extra game calls.
#include "TriggerCollisionPrefixes.h"
typedef BYTE (__thiscall * TriggerString_t)(void*, DWORD, const wchar_t*);
typedef BYTE (__thiscall * TriggerBoolean_t)(void*, DWORD, BYTE);
static TriggerString_t TriggerString_r = NULL;
static TriggerBoolean_t TriggerBoolean_r = NULL;
static volatile LONG g_triggerIdentityEvents = 0;
static volatile LONG g_triggerCollisionEvents = 0;
static volatile LONG g_triggerControls = 0;
static volatile LONG g_triggerSnapshotEvents = 0;
static PVOID volatile g_retreatTriggers[64] = { 0 };
static DWORD g_triggerVtable = 0;
static volatile LONG g_triggerTableLimit = 0;

static void TriggerTraceRemember(void* object)
{
    for (unsigned i = 0; i < 64; ++i) {
        void* current = InterlockedCompareExchangePointer(&g_retreatTriggers[i], NULL, NULL);
        if (current == object) return;
        if (!current) {
            current = InterlockedCompareExchangePointer(&g_retreatTriggers[i], object, NULL);
            if (!current || current == object) return;
        }
    }
    if (InterlockedCompareExchange(&g_triggerTableLimit, 1, 0) == 0)
        Log::Write("TriggerCollisionHook", "pid=%lu target table limit=64 reached", GetCurrentProcessId());
}

static void TriggerTraceCopy(const wchar_t* text, char* out)
{
    out[0] = 0;
    __try {
        if (!text) { strcpy(out, "<null>"); return; }
        for (unsigned i = 0; i < 127; ++i) {
            wchar_t c = text[i];
            out[i] = c >= 32 && c <= 126 ? (char)c : (c ? '?' : 0);
            out[i+1] = 0;
            if (!c) return;
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) { strcpy(out, "<unreadable>"); }
}

static bool TriggerTraceTarget(const char* parameter)
{
    return strcmp(parameter, "tyt_jedi_knight_masters_retreat") == 0;
}

static void TriggerTraceState(char* event, void* object, BYTE result)
{
    char parameter[128], name[128];
    RoomTraceName((BYTE*)object + 0x138, parameter);
    RoomTraceName((BYTE*)object + 0x110, name);
    DWORD collider = RoomTraceRead(object, 0xF0);
    Log::Write("TriggerCollisionHook", "pid=%lu %s object=%p result=%u param=%s name=%s flagsE0=%08X room=%08X collider=%08X",
        GetCurrentProcessId(), event, object, result, parameter, name,
        RoomTraceRead(object, 0xE0), RoomTraceRead(object, 0x98), collider);
    // Raw local transform cache; bit 2 clear can mean this vector is stale.
    // No world-coordinate claim or guessed getter invocation.
    Log::Write("TriggerCollisionHook", "pid=%lu %s object=%p transform24=%08X local2cBits=%08X,%08X,%08X collider2c=%08X paramHash=%08X%08X",
        GetCurrentProcessId(), event, object, RoomTraceRead(object, 0x24),
        RoomTraceRead(object, 0x2C), RoomTraceRead(object, 0x30), RoomTraceRead(object, 0x34),
        RoomTraceRead((void*)collider, 0x2C), RoomTraceRead(object, 0x14C), RoomTraceRead(object, 0x148));
}

static void TriggerTraceRoomSnapshot(char* event, void* area, void* requested)
{
    if (!RoomTraceBudget(&g_triggerSnapshotEvents, 32, "retreat-trigger-room-snapshot")) return;
    unsigned valid = 0;
    for (unsigned i = 0; i < 64; ++i) {
        void* object = InterlockedCompareExchangePointer(&g_retreatTriggers[i], NULL, NULL);
        if (!object || RoomTraceRead(object, 0) != g_triggerVtable) continue;
        char parameter[128];
        RoomTraceName((BYTE*)object + 0x138, parameter);
        if (!TriggerTraceTarget(parameter)) continue;
        ++valid;
        TriggerTraceState(event, object, 0);
    }
    Log::Write("TriggerCollisionHook", "pid=%lu %s area=%p requested=%p knownValidTargets=%u; fixed event-derived table only",
        GetCurrentProcessId(), event, area, requested, valid);
}

static BYTE __fastcall TriggerString_Hook(void* object, void*, DWORD key, const wchar_t* value)
{
    DWORD incomingError = GetLastError();
    char parameter[128] = { 0 };
    bool log = false;
    bool control = false;
    if (key == 0xD84FB395) {
        TriggerTraceCopy(value, parameter);
        if (TriggerTraceTarget(parameter))
            log = RoomTraceBudget(&g_triggerIdentityEvents, 256, "retreat-trigger-identity");
        else
            control = InterlockedIncrement(&g_triggerControls) <= 8;
    }
    SetLastError(incomingError);
    BYTE result = TriggerString_r(object, key, value);
    DWORD outgoingError = GetLastError();
    if (log) {
        TriggerTraceRemember(object);
        TriggerTraceState("identity return", object, result);
    }
    if (control)
        Log::Write("TriggerCollisionHook", "pid=%lu identity control object=%p param=%s result=%u flagsE0=%08X",
            GetCurrentProcessId(), object, parameter, result, RoomTraceRead(object, 0xE0));
    SetLastError(outgoingError);
    return result;
}

static BYTE __fastcall TriggerBoolean_Hook(void* object, void*, DWORD key, BYTE value)
{
    DWORD incomingError = GetLastError();
    bool log = false;
    if (key == 0xB4963DC1) {
        char parameter[128];
        RoomTraceName((BYTE*)object + 0x138, parameter);
        if (TriggerTraceTarget(parameter))
            log = RoomTraceBudget(&g_triggerCollisionEvents, 256, "retreat-trigger-collision");
    }
    if (log) {
        Log::Write("TriggerCollisionHook", "pid=%lu Collidable enter object=%p requested=%u", GetCurrentProcessId(), object, value);
        TriggerTraceState("collision before", object, 0);
    }
    SetLastError(incomingError);
    BYTE result = TriggerBoolean_r(object, key, value);
    DWORD outgoingError = GetLastError();
    if (log) TriggerTraceState("collision return", object, result);
    SetLastError(outgoingError);
    return result;
}

static bool TriggerTracePrefix(DWORD base, DWORD imageSize, DWORD rva, const BYTE* prefix)
{
    if (imageSize < 48 || rva > imageSize-48) return false;
    __try { return memcmp((void*)(base+rva), prefix, 48) == 0; }
    __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

static void PrepareTriggerTrace(DWORD base, DWORD imageSize)
{
    char enabled[8] = { 0 };
    if (!GetEnvironmentVariableA("SWTOR_TRACE_TRIGGER_COLLISION", enabled, sizeof(enabled)) || enabled[0] != '1') return;
    if (!TriggerTracePrefix(base, imageSize, 0x003FE1F0, triggerStringPrefix) ||
        !TriggerTracePrefix(base, imageSize, 0x003FDE70, triggerBooleanPrefix)) {
        Log::Write("TriggerCollisionHook", "UNSUPPORTED prefixes; both collision hooks disabled");
        return;
    }
    TriggerString_r = (TriggerString_t)(base+0x003FE1F0);
    TriggerBoolean_r = (TriggerBoolean_t)(base+0x003FDE70);
    g_triggerVtable = base+0x00D6116C;
    g_roomSelectionExtraTrace = TriggerTraceRoomSnapshot;
}
