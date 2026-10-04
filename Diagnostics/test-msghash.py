import sys

def u32(x): return x & 0xFFFFFFFF

def bitmath_hash(s, hashOne=0, hashTwo=0):
    s = s + '\0'
    length = len(s) - 1
    b = [ord(c) for c in s]
    p = 0
    hp2 = u32(hashOne + length + 0xdeadbeef)
    hp3 = u32(hashOne + length + 0xdeadbeef)
    hp1 = u32(hashTwo + hp2)
    def g32(o):
        i = p + o
        return u32(b[i] | (b[i+1]<<8) | (b[i+2]<<16) | (b[i+3]<<24))
    def g16(o):
        i = p + o
        return u32(b[i] | (b[i+1]<<8))
    def g8(o):
        return b[p + o]
    ln = length
    if ln > 12:
        iters = (ln - 13)//12 + 1
        while iters > 0:
            iters -= 1
            t1 = g32(0); t2 = u32(g32(4) + hp2); t3 = u32(g32(8) + hp1)
            v12 = u32((t3*16) ^ (t3>>28) ^ u32(hp3 + t1 - t3))
            v13 = u32(t2 + t3); v16 = u32(v13 + v12)
            v17 = u32((v12<<6) ^ (v12>>26) ^ u32(t2 - v12))
            v18 = u32((v17>>24) ^ u32(v13 - v17))
            v20 = u32(v16 + v17); v21 = u32((v17<<8) ^ v18)
            v22 = u32((v21<<16) ^ (v21>>16) ^ u32(v16 - v21))
            v23 = u32(v20 + v21)
            v24 = u32((v22>>13) ^ (v22<<19) ^ u32(v20 - v22))
            hp3 = u32(v23 + v22)
            hp1 = u32((v24*16) ^ (v24>>28) ^ u32(v23 - v24))
            hp2 = u32(hp3 + v24)
            ln -= 12; p += 12
    res = 'bitmath'
    if ln == 12:
        hp1 = u32(hp1 + g32(8)); ln = 8
    if ln == 8:
        hp2 = u32(hp2 + g32(4)); ln = 4
    if ln == 4:
        hp3 = u32(hp3 + g32(0))
    elif ln == 11:
        hp1 = u32(hp1 + g32(0)); hp2 = u32(hp2 + g32(4)); hp3 = u32(hp3 + (g32(8) & 0xffffff))
    elif ln == 10:
        hp1 = u32(hp1 + g16(8)); hp2 = u32(hp2 + g32(4)); hp3 = u32(hp3 + g32(0))
    elif ln == 9:
        hp1 = u32(hp1 + g8(8)); hp2 = u32(hp2 + g32(4)); hp3 = u32(hp3 + g32(0))
    elif ln == 7:
        hp2 = u32(hp2 + (g32(4) & 0xffffff)); hp3 = g32(0)
    elif ln == 6:
        hp2 = u32(hp2 + g16(4)); hp3 = u32(hp3 + g32(0))
    elif ln == 5:
        hp2 = u32(hp2 + g8(4)); hp3 = u32(hp3 + g32(0))
    elif ln == 3:
        hp3 = u32(hp3 + (g32(0) & 0xffffff))
    elif ln == 2:
        hp3 = u32(hp3 + g16(0))
    elif ln == 0:
        res = 'final'
    elif ln == 1:
        res = 'continue'
    if res == 'final':
        return hp1, hp2
    if res == 'continue':
        hp3 = u32(hp3 + g8(0))
    v52 = u32(u32(hp2 ^ hp1) - u32((hp2<<14) ^ (hp2>>18)))
    v53 = u32(u32(hp3 ^ v52) - u32((v52<<11) ^ (v52>>21)))
    v54 = u32(u32(v53 ^ hp2) - u32((v53>>7) ^ (v53<<25)))
    v55 = u32(u32(v54 ^ v52) - u32((v54<<16) ^ (v54>>16)))
    v56 = u32(u32(v53 ^ v55) - u32((v55*16) ^ (v55>>28)))
    hp2 = u32(u32(v56 ^ v54) - u32((v56<<14) ^ (v56>>18)))
    hp1 = u32(u32(hp2 ^ v55) - u32((hp2>>8) ^ (hp2<<24)))
    return hp1, hp2

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
]

for seed in [(0,0), (0xdeadbeef,0), (0,0xdeadbeef)]:
    print("=== bitmath seed=(%08X,%08X) ===" % seed)
    for op, name in pairs:
        h1, h2 = bitmath_hash(name, seed[0], seed[1])
        print("%-36s h1=%08X h2=%08X op=%08X %s" % (name, h1, h2, op, "MATCH" if (h1==op or h2==op) else ""))
