#include <Windows.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
struct Log { static unsigned lines; static void Write(char*, char*, ...) { ++lines; } };
unsigned Log::lines = 0;
#include "../../Client/Hook/Src/RoomSelectionTrace.h"
#include "../../Client/Hook/Src/TriggerCollisionTrace.h"
static BYTE object[0x300] = { 0 };
static unsigned stringCalls = 0, booleanCalls = 0;
static const wchar_t* expectedString;
static BYTE expectedBoolean;
static DWORD expectedKey;
static BYTE __fastcall StringStub(void* self, void*, DWORD key, const wchar_t* value)
{
    assert(self == object && key == expectedKey && value == expectedString);
    ++stringCalls;
    *(const wchar_t**)(object+0x138) = value;
    SetLastError(321); return 0xA5;
}
static BYTE __fastcall BooleanStub(void* self, void*, DWORD key, BYTE value)
{
    assert(self == object && key == expectedKey && value == expectedBoolean);
    ++booleanCalls;
    *(DWORD*)(object+0xE0) = value & 1 ? 0x1000 : 0;
    SetLastError(322); return 0xC3;
}
int main()
{
    TriggerString_r = (TriggerString_t)StringStub;
    TriggerBoolean_r = (TriggerBoolean_t)BooleanStub;
    TriggerString_t stringEntry = (TriggerString_t)TriggerString_Hook;
    TriggerBoolean_t booleanEntry = (TriggerBoolean_t)TriggerBoolean_Hook;
    expectedString = L"tyt_jedi_knight_masters_retreat";
    char copied[128]; TriggerTraceCopy(expectedString, copied);
    assert(TriggerTraceTarget(copied));
    TriggerTraceCopy((const wchar_t*)1, copied); assert(!strcmp(copied,"<unreadable>"));
    for (unsigned i = 0; i < 258; ++i) {
        expectedKey = 0xD84FB395;
        assert(stringEntry(object, expectedKey, expectedString) == 0xA5); assert(GetLastError()==321);
        expectedKey = 0xB4963DC1; expectedBoolean = (BYTE)(i & 1);
        assert(booleanEntry(object, expectedKey, expectedBoolean) == 0xC3); assert(GetLastError()==322);
    }
    assert(stringCalls==258 && booleanCalls==258);
    assert(Log::lines==256*2 + 256*5 + 2); // Includes explicit cap markers.
    *(DWORD*)object = 0x116116C; g_triggerVtable = 0x116116C;
    unsigned snapshotBefore = Log::lines;
    TriggerTraceRoomSnapshot("test snapshot", NULL, NULL);
    assert(Log::lines == snapshotBefore+3); // Two state lines and one summary.
    unsigned before = Log::lines;
    expectedKey=0x12345678;
    assert(booleanEntry(object,expectedKey,expectedBoolean)==0xC3);
    expectedString=L"unrelated_phase"; expectedKey=0xD84FB395;
    assert(stringEntry(object,expectedKey,expectedString)==0xA5);
    assert(Log::lines==before+1); // One positive-control identity, no target dump.
    before=Log::lines;expectedKey=0xB4963DC1;
    assert(booleanEntry(object,expectedKey,expectedBoolean)==0xC3);assert(Log::lines==before);
    TriggerTraceRoomSnapshot("unrelated snapshot", NULL, NULL);
    assert(Log::lines==before+1); // Revalidates parameter, omits reused/unrelated object.
    BYTE* image=(BYTE*)VirtualAlloc(NULL,0x500000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    assert(image);
    const BYTE* prefixes[]={triggerStringPrefix,triggerBooleanPrefix};
    DWORD rvas[]={0x3FE1F0,0x3FDE70};
    unsigned mutations=0;
    for(unsigned n=0;n<2;++n) {
        memcpy(image+rvas[n],prefixes[n],48);
        assert(TriggerTracePrefix((DWORD)image,0x500000,rvas[n],prefixes[n]));
        assert(!TriggerTracePrefix((DWORD)image,47,rvas[n],prefixes[n]));
        for(unsigned i=0;i<48;++i) {
            image[rvas[n]+i]^=1;
            assert(!TriggerTracePrefix((DWORD)image,0x500000,rvas[n],prefixes[n]));
            ++mutations;image[rvas[n]+i]^=1;
        }
    }
    VirtualFree(image,0,MEM_RELEASE);
    printf("PASS x86 forwarding/AL return, %u original calls, caps/filter/positive control, LastError, fault reads, %u prefix mutations.\n",stringCalls+booleanCalls,mutations);
}
