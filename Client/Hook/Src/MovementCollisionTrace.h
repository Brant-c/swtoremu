// Passive April-client movement contacts. No extra queries or object writes.
#include "MovementCollisionPrefixes.h"
typedef BYTE (__cdecl * MovementSweep_t)(const float*, const float*, void*, float*, void*, BYTE);
typedef int (__cdecl * MovementSupport_t)(void*, void*, float, float, DWORD, BYTE, float*, float*);
typedef int (__stdcall * MovementGround_t)(void*);
static MovementSweep_t MovementSweep_r = NULL;
static MovementSupport_t MovementSupport_r = NULL;
static MovementGround_t MovementGround_r = NULL;
static DWORD g_movementBase = 0;
static volatile LONG g_movementSamples = 0, g_supportSamples = 0, g_movementCoverage = 0;
static __declspec(thread) DWORD g_lastMovementSample = 0, g_lastSupportSample = 0;
static __declspec(thread) DWORD g_supportPlayer = 0;

static DWORD MovementPlayer()
{
    __try {
        DWORD owner = *(DWORD*)(g_movementBase + 0x010929DC);
        return owner ? *(DWORD*)(owner + 4) : 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
}

static bool MovementNearDoor(const float* p)
{
    // Captured engine coordinates; broad enough to include approach/retreat.
    return p[0] > -70 && p[0] < -58 && p[1] > -15 && p[1] < 5 && p[2] > -135 && p[2] < -115;
}

static void MovementInspectHits(void* results, LONG sample)
{
    __try {
        DWORD begin = *(DWORD*)results, end = *(DWORD*)((BYTE*)results + 4);
        if (end < begin || (end - begin) % 0xE0 || end - begin > 256 * 0xE0) {
            Log::Write("MovementCollisionHook", "sample=%ld invalid-result-range begin=%08X end=%08X", sample, begin, end);
            return;
        }
        DWORD count = (end - begin) / 0xE0;
        Log::Write("MovementCollisionHook", "sample=%ld hits=%u shown=%u", sample, count, count < 4 ? count : 4);
        for (DWORD i = 0; i < count && i < 4; ++i) {
            BYTE* hit = (BYTE*)(begin + i * 0xE0);
            // Same internal result object used by native ray wrapper C15380.
            // +80 is the optional HBNode interface; wrapper subtracts4 then
            // dereferences +94 to obtain the Hero node reference storage.
            DWORD interfacePtr = *(DWORD*)(hit + 0x80);
            DWORD object = interfacePtr >= 4 ? interfacePtr - 4 : 0;
            DWORD low = 0, high = 0, room = 0, collider = 0, knownTrigger = 0;
            bool identityReadable = true;
            __try {
                if (object) {
                    DWORD reference = *(DWORD*)(object + 0x94);
                    if (reference) { low = *(DWORD*)reference; high = *(DWORD*)(reference + 4); }
                    room = *(DWORD*)(object + 0x98);
                    collider = *(DWORD*)(object + 0xF0);
                    for (unsigned j = 0; j < 64; ++j)
                        if ((DWORD)g_retreatTriggers[j] == object) knownTrigger = 1;
                }
            } __except (EXCEPTION_EXECUTE_HANDLER) { identityReadable = false; }
            Log::Write("MovementCollisionHook", "sample=%ld hit=%u interface80=%08X object=%08X identityReadable=%u node=%08X%08X room98=%08X colliderF0=%08X knownRetreatTrigger=%u state8=%u stateC=%u state10=%u",
                sample, i, interfacePtr, object, identityReadable ? 1 : 0, high, low, room, collider, knownTrigger,
                *(DWORD*)(hit + 8), *(DWORD*)(hit + 0xC), *(DWORD*)(hit + 0x10));
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log::Write("MovementCollisionHook", "sample=%ld hit-inspection-failed", sample);
    }
}

static BYTE __cdecl MovementSweep_Hook(const float* start, const float* proposed, void* bounds, float* output, void* results, BYTE queryFlag)
{
    DWORD incomingError = GetLastError();
    DWORD caller = (DWORD)_ReturnAddress();
    bool log = false;
    DWORD player = 0, playerRoom = 0;
    float before[3] = { 0 }, wanted[3] = { 0 };
    LONG sample = 0;
    __try {
        if (caller == g_movementBase + 0x00337737) {
            player = MovementPlayer();
            DWORD behavior = player ? *(DWORD*)(player + 0x220) : 0;
            if (behavior && start == (float*)(behavior + 0xF0)) {
                if (InterlockedCompareExchange(&g_movementCoverage, 1, 0) == 0)
                    Log::Write("MovementCollisionHook", "coverage=local-player-normal-update player=%08X start=%.4f,%.4f,%.4f", player, start[0], start[1], start[2]);
                DWORD now = GetTickCount();
                float dx = proposed[0] - start[0], dy = proposed[1] - start[1], dz = proposed[2] - start[2];
                if (MovementNearDoor(start) && dx * dx + dy * dy + dz * dz > 0.000001f && (!g_lastMovementSample || now - g_lastMovementSample >= 250)) {
                    g_lastMovementSample = now;
                    sample = InterlockedIncrement(&g_movementSamples);
                    log = sample <= 48;
                    if (log) {
                        memcpy(before, start, sizeof(before)); memcpy(wanted, proposed, sizeof(wanted));
                        playerRoom = *(DWORD*)(player + 0x98);
                    }
                    if (sample == 49) Log::Write("MovementCollisionHook", "movement-sample-limit=48 reached");
                }
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) { log = false; }
    SetLastError(incomingError);
    BYTE result = MovementSweep_r(start, proposed, bounds, output, results, queryFlag);
    DWORD outgoingError = GetLastError();
    if (log) {
        __try {
            Log::Write("MovementCollisionHook", "sample=%ld tick=%lu player=%08X playerRoom98=%08X collision=%u flag=%u start=%.4f,%.4f,%.4f proposed=%.4f,%.4f,%.4f output=%.4f,%.4f,%.4f",
                sample, GetTickCount(), player, playerRoom, result, queryFlag, before[0], before[1], before[2], wanted[0], wanted[1], wanted[2], output[0], output[1], output[2]);
            if (results) MovementInspectHits(results, sample);
        } __except (EXCEPTION_EXECUTE_HANDLER) { Log::Write("MovementCollisionHook", "sample=%ld output-inspection-failed", sample); }
    }
    SetLastError(outgoingError);
    return result;
}

static int __cdecl MovementSupport_Hook(void* manager, void* bounds, float height, float slope, DWORD category, BYTE flag, float* output, float* normal)
{
    DWORD incomingError = GetLastError(), caller = (DWORD)_ReturnAddress();
    bool log = false;
    DWORD player = 0;
    LONG sample = 0;
    __try {
        if (caller == g_movementBase + 0x003394E4 || caller == g_movementBase + 0x0033966D) {
            player = MovementPlayer();
            const float* position = player ? (float*)(player + 0x2C) : NULL;
            DWORD now = GetTickCount();
            if (player && g_supportPlayer == player && position && MovementNearDoor(position) && g_lastMovementSample && now - g_lastMovementSample <= 500 && (!g_lastSupportSample || now - g_lastSupportSample >= 250)) {
                g_lastSupportSample = now;
                sample = InterlockedIncrement(&g_supportSamples);
                log = sample <= 48;
                if (sample == 49) Log::Write("MovementCollisionHook", "support-sample-limit=48 reached");
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) { log = false; }
    SetLastError(incomingError);
    int result = MovementSupport_r(manager, bounds, height, slope, category, flag, output, normal);
    DWORD outgoingError = GetLastError();
    if (log) {
        __try {
            Log::Write("MovementCollisionHook", "supportSample=%ld tick=%lu callerRva=%08X player=%08X sameCharacter=1 result=%d outputValid=%u height=%.4f slope=%.4f output=%.4f,%.4f,%.4f normal=%.4f,%.4f,%.4f",
                sample, GetTickCount(), caller - g_movementBase, player, result, result != 0 ? 1 : 0, height, slope, result ? output[0] : 0, result ? output[1] : 0, result ? output[2] : 0, result ? normal[0] : 0, result ? normal[1] : 0, result ? normal[2] : 0);
        } __except (EXCEPTION_EXECUTE_HANDLER) { Log::Write("MovementCollisionHook", "supportSample=%ld output-inspection-failed", sample); }
    }
    SetLastError(outgoingError);
    return result;
}

static int __stdcall MovementGround_Hook(void* controller)
{
    DWORD incomingError = GetLastError(), previous = g_supportPlayer;
    g_supportPlayer = 0;
    __try {
        DWORD behavior = *(DWORD*)((BYTE*)controller + 0xC);
        DWORD character = behavior ? *(DWORD*)(behavior + 0xB8) : 0;
        if (character && character == MovementPlayer()) g_supportPlayer = character;
    } __except (EXCEPTION_EXECUTE_HANDLER) { g_supportPlayer = 0; }
    SetLastError(incomingError);
    int result = MovementGround_r(controller);
    DWORD outgoingError = GetLastError();
    g_supportPlayer = previous;
    SetLastError(outgoingError);
    return result;
}

static void PrepareMovementTrace(DWORD base, DWORD imageSize)
{
    char enabled[8] = { 0 };
    if (!GetEnvironmentVariableA("SWTOR_TRACE_MOVEMENT_COLLISION", enabled, sizeof(enabled)) || enabled[0] != '1') return;
    if (!RoomTracePrefix(base, imageSize, 0x007B7450, movementSweepPrefix, 9) ||
        !RoomTracePrefix(base, imageSize, 0x00CEF540, movementSupportPrefix, 25) ||
        imageSize < 0x338FB0 || memcmp((void*)(base + 0x338F80), movementGroundPrefix, 48) != 0) {
        Log::Write("MovementCollisionHook", "UNSUPPORTED native prefixes; movement diagnostic disabled"); return;
    }
    g_movementBase = base;
    MovementSweep_r = (MovementSweep_t)(base + 0x003B7450);
    MovementSupport_r = (MovementSupport_t)(base + 0x008EF540);
    MovementGround_r = (MovementGround_t)(base + 0x00338F80);
    Log::Write("MovementCollisionHook", "prepared passive diagnostic; max48 movement+48 support samples; max4 hits/sample; 250ms sampling; local player matched");
}
