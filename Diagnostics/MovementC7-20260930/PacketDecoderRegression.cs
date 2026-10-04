using System;
using System.Collections;
using System.Reflection;
using System.Runtime.Serialization;
using NexusToRServer;
using NexusToRServer.NET;
using NexusToRServer.NET.Protocol;

public static class PacketDecoderRegression
{
    static readonly Assembly Server = typeof(TORGamePacketHandler).Assembly;
    static readonly Type Movement = Server.GetType("NexusToRServer.NET.Packets.Client.CMsg61116AD5", true);
    static readonly MethodInfo Gate = typeof(TORGamePacketHandler).GetMethod("DecodeAndRun", BindingFlags.Static | BindingFlags.NonPublic);
    static void Check(bool ok, string reason) { if (!ok) throw new Exception(reason); }
    static object Field(object o, string name) { return o.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic).GetValue(o); }
    static IPacket Packet(byte[] bytes) { var p=(IPacket)Activator.CreateInstance(Movement, true); p.SetBuffers(bytes); return p; }
    static byte[] Changed(byte[] b, int at, byte value) { var result=(byte[])b.Clone(); result[at]=value; return result; }

    public sealed class Probe : TORGameClientPacket
    {
        public bool Fail; public int Runs;
        public override void ReadImplementation() { if(Fail) throw new System.IO.EndOfStreamException("probe failure"); }
        public override void RunImplementation() { Runs++; }
        public override PacketType GetType() { return PacketType.CMsg61116AD5; }
    }

    static void Rejected(byte[] bytes, int expectedOffset, string reason)
    {
        IPacket p=Packet(bytes);
        Check(!p.Read(), "accepted " + reason);
        p.Dispose();
        var client=(TORGameClient)FormatterServices.GetUninitializedObject(typeof(TORGameClient));
        client.State=ClientState.AUTHED;
        var log=Server.GetType("NexusToRServer.Log",true);
        object queue=log.GetField("LogQueue",BindingFlags.Static|BindingFlags.NonPublic).GetValue(null);
        queue.GetType().GetMethod("Clear").Invoke(queue,null);
        TORGamePacketHandler.HandlePacket(bytes, 8, PacketType.CMsg61116AD5, 0x65B30008, client);
        bool rejected=false;
        foreach(object item in (IEnumerable)queue)
        {
            string caller=(string)item.GetType().GetProperty("Caller").GetValue(item,null);
            string text=(string)item.GetType().GetProperty("Text").GetValue(item,null);
            Check(caller != "AreaPollExperiment" && caller != "PhaseExit" && caller != "PhaseInstanceRetry", "gameplay reached: " + reason);
            Check(!text.Contains("Failed running"), "Run reached: " + reason);
            if(text.StartsWith("Rejected decode"))
            {
                Check(text.Contains("opcode=0x61116AD5") && text.Contains("length="+bytes.Length+" ") &&
                    text.Contains("offset="+expectedOffset+" ") && text.Contains("reason="), "missing rejection metadata: " + text);
                Check(text.Contains(bytes.Length >= 8 ? "component=0x65B30008" : "component=unavailable"), "component metadata");
                rejected=true;
            }
        }
        Check(rejected,"missing rejection log: " + reason);
    }

    public static void Run(byte[] fixture)
    {
        Check(fixture.Length==44,"fixture size");
        IPacket p=Packet(fixture);
        Check(p.Read(),"captured C5 rejected");
        foreach(var pair in new[]{new object[]{"_heading",12},new object[]{"_x",16},new object[]{"_y",20},new object[]{"_z",24}})
            Check((float)Field(p,(string)pair[0]) == BitConverter.ToSingle(fixture,(int)pair[1]),"field changed");
        byte[] body=(byte[])Field(p,"_body");
        for(int i=0;i<body.Length;i++) Check(body[i]==fixture[i+8],"body changed");
        Check(((byte[])Field(p,"_opaqueTail")).Length==16 && p._stream.Position==44,"tail/end");
        p.Dispose();
        for(int n=0;n<fixture.Length;n++)
        {
            byte[] truncated=new byte[n]; Array.Copy(fixture,truncated,n);
            int offset=n<28 ? (n/4)*4 : 28;
            Rejected(truncated,offset,"truncation "+n);
        }
        Rejected(Changed(fixture,8,0xC7),8,"wrong variant");
        Rejected(Changed(fixture,9,1),8,"high variant byte");
        // Opcode still dispatches as movement to exercise its own decoder identity check.
        Rejected(Changed(fixture,0,0),0,"wrong opcode");
        byte[] extra=new byte[45]; Array.Copy(fixture,extra,44); extra[44]=1;
        Rejected(extra,44,"trailing byte");
        var probe=new Probe(); probe.SetBuffers(fixture); probe.Fail=true;
        Check(!(bool)Gate.Invoke(null,new object[]{probe}) && probe.Runs==0,"failed Read ran");
        probe.Fail=false;
        Check((bool)Gate.Invoke(null,new object[]{probe}) && probe.Runs==1,"valid Read did not run exactly once");
        probe.Fail=true;
        Check(!(bool)Gate.Invoke(null,new object[]{probe}) && probe.Runs==1,"reused failed Read ran");
        probe.Dispose();
        PackedTests();
    }

    static void PackedTests()
    {
        ulong u; long s;
        for(int token=0;token<256;token++)
        {
            var c=new PacketCursor(new byte[]{(byte)token});
            bool ok=c.TryReadPackedUnsigned(out u);
            Check(ok==(token<192),"unsigned singleton token "+token);
            if(ok) Check(u==(ulong)token && c.TryEnd(),"unsigned literal");
            else Check(c.FailureOffset==0 && c.Offset==0,"unsigned failure position");
            c=new PacketCursor(new byte[]{(byte)token});
            ok=c.TryReadPackedSigned(out s);
            Check(ok==(token<192 || token==208),"signed singleton token "+token);
            if(ok) Check(s==(token==208 ? long.MinValue : token) && c.TryEnd(),"signed literal");
            else Check(c.FailureOffset==0 && c.Offset==0,"signed failure position");
        }
        for(int width=1;width<=8;width++)
        {
            byte[] b=new byte[width+1]; b[0]=(byte)(199+width); b[width]=0xBE;
            var c=new PacketCursor(b);
            Check(c.TryReadPackedUnsigned(out u) && u==190 && c.TryEnd(),"packed unsigned width "+width);
            c=new PacketCursor(b);
            Check(c.TryReadPackedSigned(out s) && s==190 && c.TryEnd(),"packed positive width");
            b[0]=(byte)(191+width); c=new PacketCursor(b);
            Check(c.TryReadPackedSigned(out s) && s==-190 && c.TryEnd(),"packed negative width");
            for(int n=1;n<b.Length;n++)
            {
                byte[] shortBytes=new byte[n]; Array.Copy(b,shortBytes,n); c=new PacketCursor(shortBytes);
                Check(!c.TryReadPackedSigned(out s) && c.FailureOffset==0 && c.Offset==0,"packed truncation");
            }
        }
        var multi=new PacketCursor(new byte[]{0xC9,0x12,0x34});
        Check(multi.TryReadPackedUnsigned(out u) && u==0x1234,"packed byte order");
        var max=new PacketCursor(new byte[]{0xCF,255,255,255,255,255,255,255,255});
        Check(max.TryReadPackedUnsigned(out u) && u==ulong.MaxValue,"unsigned max");
        var overflow=new PacketCursor(new byte[]{0xCF,128,0,0,0,0,0,0,0});
        Check(!overflow.TryReadPackedSigned(out s) && overflow.FailureOffset==0,"signed overflow");
        var sticky=new PacketCursor(new byte[]{1}); uint fixedValue;
        Check(!sticky.TryReadUInt32(out fixedValue) && !sticky.TryReadPackedUnsigned(out u) && !sticky.TryEnd() && sticky.Offset==0,"sticky failure");
    }
}
