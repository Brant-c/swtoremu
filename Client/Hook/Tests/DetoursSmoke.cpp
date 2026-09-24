#include <windows.h>
#include <detours.h>
#include <stdio.h>
__declspec(noinline) int Target(int value) { return value + 1; }
static int (*Original)(int) = Target;
static int Replacement(int value) { return Original(value) + 10; }
int main() {
    int (*volatile invoke)(int) = Target;
    if (invoke(1) != 2) return 1;
    if (DetourTransactionBegin() != NO_ERROR) return 2;
    if (DetourUpdateThread(GetCurrentThread()) != NO_ERROR) return 3;
    if (DetourAttach(&(PVOID&)Original, (PVOID)Replacement) != NO_ERROR) return 4;
    if (DetourTransactionCommit() != NO_ERROR) return 5;
    if (invoke(1) != 12) return 6;
    if (DetourTransactionBegin() != NO_ERROR) return 7;
    if (DetourUpdateThread(GetCurrentThread()) != NO_ERROR) return 8;
    if (DetourDetach(&(PVOID&)Original, (PVOID)Replacement) != NO_ERROR) return 9;
    if (DetourTransactionCommit() != NO_ERROR) return 10;
    if (invoke(1) != 2) return 11;
    puts("PASS: x86 hook, original trampoline, and detach");
    return 0;
}
