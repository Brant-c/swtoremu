using System;
using System.IO;
using System.Linq;
using Hero;
using Hero.Definition;

class DumpClasses {
    static int Main(string[] args) {
        if (args.Length != 1) { Console.Error.WriteLine("usage: Dump-Classes <resource-cache-root>"); return 2; }
        string root = args[0];
        using (FileStream gom = File.OpenRead(Path.Combine(root, "systemgenerated", "client.gom")))
            GOM.Instance.Parse(gom);
        for (int index = 0; index < 500; index++) {
            string path = Path.Combine(root, "systemgenerated", "buckets", index + ".bkt");
            if (!File.Exists(path)) break;
            using (FileStream bucket = File.OpenRead(path))
                GOM.Instance.LoadBucket(bucket);
        }
        foreach (var def in GOM.Instance.Definitions.Values.OrderBy(d => d.Id)) {
            Console.WriteLine("{0}\t0x{1:X16}\t{2}", def.Type, def.Id, def.Name);
        }
        return 0;
    }
}
