#include <Windows.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
struct Log { static unsigned lines; static void Write(char*, char*, ...) { ++lines; } };
unsigned Log::lines = 0;
#include "../../Client/Hook/Src/RoomSelectionTrace.h"
static unsigned registers = 0, selects = 0, activates = 0;
static BYTE area[0x500] = { 0 }, room[0x280] = { 0 };
static void* expectedName;
static __declspec(noinline) void* __fastcall RegisterStub(void* self, void*, void* name)
{
    assert(self == area && name == expectedName); ++registers;
    SetLastError(123); return room;
}
static __declspec(noinline) void __fastcall SelectStub(void* self, void*, void* requested)
{
    assert(self == area && requested == room); ++selects;
    *(DWORD*)(area + 0x298) = (DWORD)requested; SetLastError(124);
}
static __declspec(noinline) void __fastcall ActivateStub(void* self, void*, DWORD a, DWORD b, DWORD c)
{
    assert(self == room && a == 17 && b == 23 && c == 29); ++activates;
    *(DWORD*)(room + 0x8C) = 3; SetLastError(125);
}
int main()
{
    // x86 fastcall with unused EDX has the same ECX/stack cleanup shape as
    // these thiscall targets. Invoke through thiscall pointers, as Detours does.
    NativeRoomRegister_r = (NativeRoomRegister_t)RegisterStub;
    NativeRoomSelect_r = (NativeRoomSelect_t)SelectStub;
    NativeRoomActivate_r = (NativeRoomActivate_t)ActivateStub;
    const wchar_t* name = L"gnarls_new"; expectedName = &name;
    char copied[128]; RoomTraceName(&name, copied); assert(!strcmp(copied, "gnarls_new"));
    RoomTraceName((void*)1, copied); assert(!strcmp(copied, "<unreadable>"));
    assert(RoomTraceRead((void*)1, 0x90) == 0xFFFFFFFF);
    NativeRoomRegister_t registerEntry = (NativeRoomRegister_t)NativeRoomRegister_Hook;
    NativeRoomSelect_t selectEntry = (NativeRoomSelect_t)NativeRoomSelect_Hook;
    NativeRoomActivate_t activateEntry = (NativeRoomActivate_t)NativeRoomActivate_Hook;
    for (unsigned i = 0; i < 514; ++i)
    {
        assert(registerEntry(area, &name) == room); assert(GetLastError() == 123);
        *(DWORD*)(area + 0x298) = 0;
        selectEntry(area, room); assert(GetLastError() == 124);
        activateEntry(room, 17, 23, 29); assert(GetLastError() == 125);
    }
    assert(registers == 514 && selects == 514 && activates == 514);
    assert(Log::lines == 512 + 256 * 2 + 256 * 2 + 3);
    BYTE* image = (BYTE*)VirtualAlloc(NULL, 0x800000, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    assert(image);
    const BYTE* prefixes[] = { roomRegisterPrefix, roomSelectPrefix, roomActivatePrefix };
    DWORD vas[] = { 0xB90CF0, 0xB91AE0, 0xB7C390 }, relocations[] = { 12, 6, 12 };
    unsigned rejected = 0;
    for (unsigned n = 0; n < 3; ++n)
    {
        BYTE* target = image + vas[n] - 0x400000;
        memcpy(target, prefixes[n], 48);
        DWORD handler; memcpy(&handler, target + relocations[n], 4);
        handler += (DWORD)image - 0x400000; memcpy(target + relocations[n], &handler, 4);
        assert(RoomTracePrefix((DWORD)image, 0x800000, vas[n], prefixes[n], relocations[n]));
        assert(!RoomTracePrefix((DWORD)image, 47, vas[n], prefixes[n], relocations[n]));
        for (unsigned i = 0; i < 48; ++i)
        {
            target[i] ^= 1;
            assert(!RoomTracePrefix((DWORD)image, 0x800000, vas[n], prefixes[n], relocations[n]));
            ++rejected; target[i] ^= 1;
        }
    }
    VirtualFree(image, 0, MEM_RELEASE);
    printf("PASS: x86 ABI forwarding/returns, 1542 original calls including capped events, LastError, bounded fault reads, relocated prefixes, %u mutations rejected.\n", rejected);
    return 0;
}
