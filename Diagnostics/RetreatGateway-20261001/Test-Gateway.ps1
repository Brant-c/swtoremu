$ErrorActionPreference = 'Stop'
$source = Get-Content -LiteralPath (Join-Path $PSScriptRoot '../../SharpServer/AreaServer/RetreatGatewayState.cs') -Raw
$checks = @'
namespace NexusToRServer.AreaServer {
 public static class GatewayChecks {
  static void Expect(int actual, int expected, string name) { if(actual != expected) throw new System.Exception(name + ": " + actual); }
  public static void Run() {
   var gate = new RetreatGatewayState();
   float center = RetreatGatewayState.GatewayX;
   Expect(gate.Observe(-64.8741f,-6.9f,-127.67f),0,"initial interior");
   for(int cycle=0;cycle<20;cycle++) {
    Expect(gate.Observe(center+0.1f,-6.9f,-126.9f),1,"outbound");
    Expect(gate.Observe(center+0.02f,-6.9f,-126.9f),0,"outside jitter");
    Expect(gate.Observe(center-0.02f,-6.9f,-126.9f),0,"inside jitter");
    Expect(gate.Observe(center-0.1f,-6.9f,-126.9f),-1,"inbound");
    Expect(gate.Observe(center-0.02f,-6.9f,-126.9f),0,"inside stationary");
   }
   var remote = new RetreatGatewayState();
   Expect(remote.Observe(center-1,-6.9f,-140),0,"remote initial");
   Expect(remote.Observe(center+1,-6.9f,-140),0,"remote crossing");
   var invalid = new RetreatGatewayState();
   Expect(invalid.Observe(center-1,-6.9f,-126.9f),0,"valid history");
   Expect(invalid.Observe(float.NaN,-6.9f,-126.9f),0,"NaN rejected");
   Expect(invalid.Observe(center+1,float.PositiveInfinity,-126.9f),0,"Infinity rejected");
   Expect(invalid.Observe(center+1,-6.9f,-126.9f),1,"invalid does not poison history");
   var diagonal = new RetreatGatewayState();
   diagonal.Observe(center-0.1f,-6.9f,-140);
   Expect(diagonal.Observe(center+2,-6.9f,-126.9f),0,"endpoint in corridor but plane outside");
   var rapid = new RetreatGatewayState();
   rapid.Observe(center-2,-6.9f,-126.9f);
   Expect(rapid.Observe(center+2,-6.9f,-126.9f),1,"large valid step");
   Expect(rapid.Observe(center-2,-6.9f,-126.9f),-1,"large return");
  }
 }
}
'@
Add-Type -TypeDefinition ($source + [Environment]::NewLine + $checks)
[NexusToRServer.AreaServer.GatewayChecks]::Run()
'PASS: 20 repeated cycles, jitter, remote and diagonal crossings, large steps, invalid coordinates'
