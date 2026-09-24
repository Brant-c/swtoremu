using System;

static class HashTrace
{
    static uint U(uint v) { return v; }

    static void Main(string[] args)
    {
        string path = args[0];
        byte[] data = System.Text.Encoding.ASCII.GetBytes(path.ToLowerInvariant());
        uint eax = 0, ecx = 0, edx = 0;
        uint ebx = (uint)(data.Length + 0xDEADBEEF);
        uint edi = ebx, esi = ebx;
        Console.WriteLine("init ebx={0:X8} edi={1:X8} esi={2:X8}", ebx, edi, esi);
        int i = 0;
        while (i + 12 < data.Length)
        {
            edi = (uint)(BitConverter.ToUInt32(data, i + 4) + edi);
            esi = (uint)(BitConverter.ToUInt32(data, i + 8) + esi);
            edx = (uint)(BitConverter.ToUInt32(data, i) - esi);
            edx = (uint)((edx + ebx) ^ (esi >> 28) ^ (esi << 4));
            esi += edi;
            edi = (uint)((edi - edx) ^ (edx >> 26) ^ (edx << 6));
            edx += esi;
            esi = (uint)((esi - edi) ^ (edi >> 24) ^ (edi << 8));
            edi += edx;
            ebx = (uint)((edx - esi) ^ (esi >> 16) ^ (esi << 16));
            esi += edi;
            edi = (uint)((edi - ebx) ^ (ebx >> 13) ^ (ebx << 19));
            ebx += esi;
            esi = (uint)((esi - edi) ^ (edi >> 28) ^ (edi << 4));
            edi += ebx;
            i += 12;
            Console.WriteLine("loop i={0} ebx={1:X8} edi={2:X8} esi={3:X8}", i, ebx, edi, esi);
        }
        int tail = data.Length - i;
        Console.WriteLine("tail={0}", tail);
        if (tail > 0)
        {
            for (int p = 0; p < tail; p++)
            {
                byte value = data[i + p];
                if (p < 4) ebx += (uint)(value << (8 * p));
                else if (p < 8) edi += (uint)(value << (8 * (p - 4)));
                else esi += (uint)(value << (8 * (p - 8)));
                Console.WriteLine("acc p={0} v={2:X2} ebx={1:X8}", p, ebx, value);
                Console.WriteLine("acc p={0} edi={1:X8}", p, edi);
                Console.WriteLine("acc p={0} esi={1:X8}", p, esi);
            }
            esi = (uint)((esi ^ edi) - ((edi >> 18) ^ (edi << 14)));
            Console.WriteLine("t1 esi={0:X8}", esi);
            ecx = (uint)((esi ^ ebx) - ((esi >> 21) ^ (esi << 11)));
            Console.WriteLine("t2 ecx={0:X8}", ecx);
            edi = (uint)((edi ^ ecx) - ((ecx >> 7) ^ (ecx << 25)));
            Console.WriteLine("t3 edi={0:X8}", edi);
            esi = (uint)((esi ^ edi) - ((edi >> 16) ^ (edi << 16)));
            Console.WriteLine("t4 esi={0:X8}", esi);
            edx = (uint)((esi ^ ecx) - ((esi >> 28) ^ (esi << 4)));
            Console.WriteLine("t5 edx={0:X8}", edx);
            edi = (uint)((edi ^ edx) - ((edx >> 18) ^ (edx << 14)));
            Console.WriteLine("t6 edi={0:X8}", edi);
            eax = (uint)((edi ^ edx) - ((edi >> 8) ^ (edi << 24)));
            Console.WriteLine("t7 eax={0:X8}", eax);
        }
        Console.WriteLine("hash {0:X8}{1:X8}", edi, eax);
    }
}
