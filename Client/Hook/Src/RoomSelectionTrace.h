// April-client native events only. No scans, extra native calls, or writes to
// game objects. ABIs and field offsets: Diagnostics/RoomSelection-20260930.
typedef void* (__thiscall * NativeRoomRegister_t)(void*, void*);
typedef void (__thiscall * NativeRoomSelect_t)(void*, void*);
typedef void (__thiscall * NativeRoomActivate_t)(void*, DWORD, DWORD, DWORD);
static NativeRoomRegister_t NativeRoomRegister_r = NULL;
static NativeRoomSelect_t NativeRoomSelect_r = NULL;
static NativeRoomActivate_t NativeRoomActivate_r = NULL;
static volatile LONG g_roomRegisterEvents = 0;
static volatile LONG g_roomSelectEvents = 0;
static volatile LONG g_roomActivateEvents = 0;
// Optional bounded snapshot of objects already identified by native events.
static void (*g_roomSelectionExtraTrace)(char*, void*, void*) = NULL;

static DWORD RoomTraceRead(void* object, DWORD offset)
{
    if (!object) return 0;
    __try { return *(DWORD*)((BYTE*)object + offset); }
    __except (EXCEPTION_EXECUTE_HANDLER) { return 0xFFFFFFFF; }
}

static void RoomTraceName(void* nameObject, char* name)
{
    name[0] = 0;
    __try
    {
        const wchar_t* text = nameObject ? *(const wchar_t**)nameObject : NULL;
        if (!text) { strcpy(name, "<null>"); return; }
        for (unsigned i = 0; i < 127; ++i)
        {
            wchar_t c = text[i];
            name[i] = c >= 32 && c <= 126 ? (char)c : (c ? '?' : 0);
            name[i + 1] = 0;
            if (!c) return;
        }
    }
    __except (EXCEPTION_EXECUTE_HANDLER) { strcpy(name, "<unreadable>"); }
}

static bool RoomTraceBudget(volatile LONG* counter, LONG limit, char* event)
{
    LONG count = InterlockedIncrement(counter);
    if (count == limit + 1)
        Log::Write("NativeRoomHook", "pid=%lu %s limit=%ld reached; further events omitted", GetCurrentProcessId(), event, limit);
    return count <= limit;
}

static void* __fastcall NativeRoomRegister_Hook(void* area, void*, void* nameObject)
{
    DWORD incomingError = GetLastError();
    bool log = RoomTraceBudget(&g_roomRegisterEvents, 512, "register");
    char name[128] = { 0 };
    if (log) RoomTraceName(nameObject, name);
    SetLastError(incomingError);
    void* room = NativeRoomRegister_r(area, nameObject);
    DWORD outgoingError = GetLastError();
    if (log)
        Log::Write("NativeRoomHook", "pid=%lu register area=%p room=%p name=%s state8c=%08X state90=%08X",
            GetCurrentProcessId(), area, room, name, RoomTraceRead(room, 0x8C), RoomTraceRead(room, 0x90));
    SetLastError(outgoingError);
    return room;
}

static void __fastcall NativeRoomSelect_Hook(void* area, void*, void* room)
{
    DWORD incomingError = GetLastError();
    DWORD oldRoom = RoomTraceRead(area, 0x298);
    bool log = oldRoom != (DWORD)room && RoomTraceBudget(&g_roomSelectEvents, 256, "select");
    if (log)
        Log::Write("NativeRoomHook", "pid=%lu select enter area=%p old=%08X requested=%p state8c=%08X state90=%08X",
            GetCurrentProcessId(), area, oldRoom, room, RoomTraceRead(room, 0x8C), RoomTraceRead(room, 0x90));
    if (log && g_roomSelectionExtraTrace) g_roomSelectionExtraTrace("room-select before", area, room);
    SetLastError(incomingError);
    NativeRoomSelect_r(area, room);
    DWORD outgoingError = GetLastError();
    if (log)
        Log::Write("NativeRoomHook", "pid=%lu select return area=%p selected=%08X requested=%p state8c=%08X state90=%08X",
            GetCurrentProcessId(), area, RoomTraceRead(area, 0x298), room, RoomTraceRead(room, 0x8C), RoomTraceRead(room, 0x90));
    if (log && g_roomSelectionExtraTrace) g_roomSelectionExtraTrace("room-select return", area, room);
    SetLastError(outgoingError);
}

static void __fastcall NativeRoomActivate_Hook(void* room, void*, DWORD a, DWORD b, DWORD c)
{
    DWORD incomingError = GetLastError();
    bool log = RoomTraceBudget(&g_roomActivateEvents, 256, "activate");
    if (log)
        Log::Write("NativeRoomHook", "pid=%lu activate enter room=%p args=%08X,%08X,%08X state8c=%08X state90=%08X",
            GetCurrentProcessId(), room, a, b, c, RoomTraceRead(room, 0x8C), RoomTraceRead(room, 0x90));
    SetLastError(incomingError);
    NativeRoomActivate_r(room, a, b, c);
    DWORD outgoingError = GetLastError();
    if (log)
        Log::Write("NativeRoomHook", "pid=%lu activate return room=%p state8c=%08X state90=%08X",
            GetCurrentProcessId(), room, RoomTraceRead(room, 0x8C), RoomTraceRead(room, 0x90));
    SetLastError(outgoingError);
}

// 48-byte exact prefixes; only the embedded SEH-handler VA is relocated.
static const BYTE roomRegisterPrefix[] = {
    0x55, 0x8B, 0xEC, 0x64, 0xA1, 0x00, 0x00, 0x00, 0x00, 0x6A, 0xFF, 0x68, 0x83, 0xF9, 0xF9, 0x00,
    0x50, 0x64, 0x89, 0x25, 0x00, 0x00, 0x00, 0x00, 0x83, 0xEC, 0x1C, 0x53, 0x56, 0x57, 0x8B, 0x7D,
    0x08, 0x8B, 0xF1, 0x57, 0x8D, 0x45, 0x08, 0x8D, 0x9E, 0xD8, 0x03, 0x00, 0x00, 0x50, 0x8B, 0xCB };
static const BYTE roomSelectPrefix[] = {
    0x55, 0x8B, 0xEC, 0x6A, 0xFF, 0x68, 0xCE, 0xFB, 0xF9, 0x00, 0x64, 0xA1, 0x00, 0x00, 0x00, 0x00,
    0x50, 0x64, 0x89, 0x25, 0x00, 0x00, 0x00, 0x00, 0x81, 0xEC, 0xA8, 0x00, 0x00, 0x00, 0x53, 0x56,
    0x33, 0xDB, 0x89, 0x5D, 0xF0, 0x57, 0x8B, 0x7D, 0x08, 0x8B, 0xF1, 0x3B, 0xBE, 0x98, 0x02, 0x00 };
static const BYTE roomActivatePrefix[] = {
    0x55, 0x8B, 0xEC, 0x64, 0xA1, 0x00, 0x00, 0x00, 0x00, 0x6A, 0xFF, 0x68, 0x8E, 0xDA, 0xF9, 0x00,
    0x50, 0x64, 0x89, 0x25, 0x00, 0x00, 0x00, 0x00, 0x83, 0xEC, 0x50, 0x56, 0x57, 0x8B, 0xF1, 0xBF,
    0x03, 0x00, 0x00, 0x00, 0x39, 0xBE, 0x8C, 0x00, 0x00, 0x00, 0x75, 0x21, 0x8B, 0x45, 0x0C, 0x8B };

static bool RoomTracePrefix(DWORD base, DWORD imageSize, DWORD va, const BYTE* prefix, DWORD relocation)
{
    DWORD rva = va - 0x00400000;
    if (imageSize < 48 || rva > imageSize - 48) return false;
    BYTE expected[48];
    memcpy(expected, prefix, sizeof(expected));
    DWORD handler;
    memcpy(&handler, expected + relocation, sizeof(handler));
    handler += base - 0x00400000;
    memcpy(expected + relocation, &handler, sizeof(handler));
    __try { return memcmp((void*)(base + rva), expected, sizeof(expected)) == 0; }
    __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

static void PrepareRoomTrace(DWORD base, DWORD imageSize)
{
    char enabled[8] = { 0 };
    if (!GetEnvironmentVariableA("SWTOR_TRACE_ROOM_SELECTION", enabled, sizeof(enabled)) || enabled[0] != '1') return;
    if (!RoomTracePrefix(base, imageSize, 0x00B90CF0, roomRegisterPrefix, 12) ||
        !RoomTracePrefix(base, imageSize, 0x00B91AE0, roomSelectPrefix, 6) ||
        !RoomTracePrefix(base, imageSize, 0x00B7C390, roomActivatePrefix, 12))
    {
        Log::Write("NativeRoomHook", "UNSUPPORTED prefixes; all three room hooks disabled");
        return;
    }
    NativeRoomRegister_r = (NativeRoomRegister_t)(base + 0x00790CF0);
    NativeRoomSelect_r = (NativeRoomSelect_t)(base + 0x00791AE0);
    NativeRoomActivate_r = (NativeRoomActivate_t)(base + 0x0077C390);
}
