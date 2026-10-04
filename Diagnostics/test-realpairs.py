import sys, importlib.util

def u32(x): return x & 0xFFFFFFFF

def bitmath(s, h1s=0, h2s=0):
    s = s + '\0'
    length = len(s) - 1
    b = [ord(c) for c in s]
    p = 0
    hp2 = u32(h1s + length + 0xdeadbeef)
    hp3 = u32(h1s + length + 0xdeadbeef)
    hp1 = u32(h2s + hp2)
    def g32(o):
        i = p + o
        return u32(b[i] | (b[i+1]<<8) | (b[i+2]<<16) | (b[i+3]<<24))
    def g16(o):
        i = p + o
        return u32(b[i] | (b[i+1]<<8))
    def g8(o): return b[p+o]
    ln = length
    if ln > 12:
        it = (ln-13)//12 + 1
        while it > 0:
            it -= 1
            t1=g32(0); t2=u32(g32(4)+hp2); t3=u32(g32(8)+hp1)
            v12=u32((t3*16)^(t3>>28)^u32(hp3+t1-t3)); v13=u32(t2+t3); v16=u32(v13+v12)
            v17=u32((v12<<6)^(v12>>26)^u32(t2-v12)); v18=u32((v17>>24)^u32(v13-v17))
            v20=u32(v16+v17); v21=u32((v17<<8)^v18)
            v22=u32((v21<<16)^(v21>>16)^u32(v16-v21)); v23=u32(v20+v21)
            v24=u32((v22>>13)^(v22<<19)^u32(v20-v22))
            hp3=u32(v23+v22); hp1=u32((v24*16)^(v24>>28)^u32(v23-v24)); hp2=u32(hp3+v24)
            ln-=12; p+=12
    res='bitmath'
    if ln==12: hp1=u32(hp1+g32(8)); ln=8
    if ln==8:  hp2=u32(hp2+g32(4)); ln=4
    if ln==4:  hp3=u32(hp3+g32(0))
    elif ln==11: hp1=u32(hp1+g32(0)); hp2=u32(hp2+g32(4)); hp3=u32(hp3+(g32(8)&0xffffff))
    elif ln==10: hp1=u32(hp1+g16(8)); hp2=u32(hp2+g32(4)); hp3=u32(hp3+g32(0))
    elif ln==9:  hp1=u32(hp1+g8(8)); hp2=u32(hp2+g32(4)); hp3=u32(hp3+g32(0))
    elif ln==7:  hp2=u32(hp2+(g32(4)&0xffffff)); hp3=g32(0)
    elif ln==6:  hp2=u32(hp2+g16(4)); hp3=u32(hp3+g32(0))
    elif ln==5:  hp2=u32(hp2+g8(4)); hp3=u32(hp3+g32(0))
    elif ln==3:  hp3=u32(hp3+(g32(0)&0xffffff))
    elif ln==2:  hp3=u32(hp3+g16(0))
    elif ln==0:  res='final'
    elif ln==1:  res='continue'
    if res=='final': return hp1, hp2
    if res=='continue': hp3=u32(hp3+g8(0))
    v52=u32(u32(hp2^hp1)-u32((hp2<<14)^(hp2>>18)))
    v53=u32(u32(hp3^v52)-u32((v52<<11)^(v52>>21)))
    v54=u32(u32(v53^hp2)-u32((v53>>7)^(v53<<25)))
    v55=u32(u32(v54^v52)-u32((v54<<16)^(v54>>16)))
    v56=u32(u32(v53^v55)-u32((v55*16)^(v55>>28)))
    hp2=u32(u32(v56^v54)-u32((v56<<14)^(v56>>18)))
    hp1=u32(u32(hp2^v55)-u32((hp2>>8)^(hp2<<24)))
    return hp1, hp2

pairs = [
    (0x699FAC0E, "AssetCreated"),
    (0x0D446E80, "ClientReplicationTransaction"),
    (0x0E71623B, "HackPackFromArea"),
    (0xBBC9DC07, "HackDataRequestFromArea"),
    (0x10FF67AB, "LogDebug"),
]

print("name | variant | h1 h2 | opcode | match")
for op, name in pairs:
    for label, s in [("as-is", name), ("lower", name.lower())]:
        for seeds in [(0,0),(0xdeadbeef,0)]:
            a, b = bitmath(s, seeds[0], seeds[1])
            if a == op or b == op:
                print("MATCH bitmath %r seeds=%s %s" % (s, seeds, label))
