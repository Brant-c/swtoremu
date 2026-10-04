import sys

def u32(x): return x & 0xFFFFFFFF

def classic(s, seed):
    eax = edx = ebx = esi = edi = 0
    b = s.encode('latin-1')
    ebx = edi = esi = u32(len(s) + seed)
    n = len(s)
    i = 0
    while i + 12 < n:
        edi = u32(u32((b[i+7]<<24)|(b[i+6]<<16)|(b[i+5]<<8)|b[i+4]) + edi)
        esi = u32(u32((b[i+11]<<24)|(b[i+10]<<16)|(b[i+9]<<8)|b[i+8]) + esi)
        edx = u32(u32((b[i+3]<<24)|(b[i+2]<<16)|(b[i+1]<<8)|b[i]) - esi)
        edx = u32(u32(edx + ebx) ^ (esi>>28) ^ (esi<<4))
        esi = u32(esi + edi)
        edi = u32(u32(edi - edx) ^ (edx>>26) ^ (edx<<6))
        edx = u32(edx + esi)
        esi = u32(u32(esi - edi) ^ (edi>>24) ^ (edi<<8))
        edi = u32(edi + edx)
        ebx = u32(u32(edx - esi) ^ (esi>>16) ^ (esi<<16))
        esi = u32(esi + edi)
        edi = u32(u32(edi - ebx) ^ (ebx>>13) ^ (ebx<<19))
        ebx = u32(ebx + esi)
        esi = u32(u32(esi - edi) ^ (edi>>28) ^ (edi<<4))
        edi = u32(edi + ebx)
        i += 12
    rem = n - i
    if rem > 0:
        if rem >= 12: esi = u32(esi + (b[i+11]<<24)); rem = 11
        if rem >= 11: esi = u32(esi + (b[i+10]<<16)); rem = 10
        if rem >= 10: esi = u32(esi + (b[i+9]<<8)); rem = 9
        if rem >= 9:  esi = u32(esi + b[i+8]); rem = 8
        if rem >= 8:  edi = u32(edi + (b[i+7]<<24)); rem = 7
        if rem >= 7:  edi = u32(edi + (b[i+6]<<16)); rem = 6
        if rem >= 6:  edi = u32(edi + (b[i+5]<<8)); rem = 5
        if rem >= 5:  edi = u32(edi + b[i+4]); rem = 4
        if rem >= 4:  ebx = u32(ebx + (b[i+3]<<24)); rem = 3
        if rem >= 3:  ebx = u32(ebx + (b[i+2]<<16)); rem = 2
        if rem >= 2:  ebx = u32(ebx + (b[i+1]<<8)); rem = 1
        if rem >= 1:  ebx = u32(ebx + b[i])
        esi = u32(u32(esi ^ edi) - u32((edi>>18) ^ (edi<<14)))
        ecx = u32(u32(esi ^ ebx) - u32((esi>>21) ^ (esi<<11)))
        edi = u32(u32(edi ^ ecx) - u32((ecx>>7) ^ (ecx<<25)))
        esi = u32(u32(esi ^ edi) - u32((edi>>16) ^ (edi<<16)))
        edx = u32(u32(esi ^ ecx) - u32((esi>>28) ^ (esi<<4)))
        edi = u32(u32(edi ^ edx) - u32((edx>>18) ^ (edx<<14)))
        eax = u32(u32(esi ^ edi) - u32((edi>>8) ^ (edi<<24)))
        return edi, eax   # ph, sh
    return esi, eax       # ph, sh

pairs = [
    (0x0D446E80, "AreaClientReplicationTransaction"),
    (0x0ADFF9BF, "AreaRequestRPC"),
    (0x0E71623B, "AreaHackPack"),
    (0xA1D9E226, "AreaAwarenessEntered"),
    (0x1CA72F2D, "AreaSendAwarenessRange"),
    (0xCFBFFBCB, "AreaSetCharacter"),
    (0x944511BF, "AreaTeleportCharacter"),
    (0x6BA87A93, "AreaTalk"),
    (0x30CCCB47, "AreaDisconnect"),
    (0x8F0A39AA, "AreaUpdateTimeSource"),
    (0x2B4792AE, "CharacterSetRendezvousPoint"),
    (0x2B4792AE, "SetCharacterRendezvousPoint"),
    (0xADEAFCA3, "ChangeCharacterState"),
]

for seed in [0, 0xdeadbeef]:
    for lower in [False, True]:
        print("=== classic seed=0x%X lower=%s ===" % (seed, lower))
        for op, name in pairs:
            s = name.lower() if lower else name
            ph, sh = classic(s, seed)
            m = "MATCH" if (ph == op or sh == op) else ""
            print("%08X ph=%08X sh=%08X %-34s %s" % (op, ph, sh, name, m))
