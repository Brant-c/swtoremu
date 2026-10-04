using System;
using System.IO;
using System.Linq;
using Hero;
using Hero.Definition;
using Hero.Types;

class InspectTaxiContent
{
    static void Dump(HeroAnyValue value, string indent)
    {
        HeroList list = value as HeroList;
        if (list != null && list.Data != null) foreach (var entry in list.Data) {
            Console.WriteLine(indent + entry.Value.ValueText); Dump(entry.Value, indent + "  ");
        }
        HeroClass cls = value as HeroClass;
        if (cls != null) foreach (Variable variable in cls.Variables) {
            Console.WriteLine("{0}{1} {2} = {3}", indent, variable.Field, variable.Value.Type, variable.Value.ValueText);
            Dump(variable.Value, indent + "  ");
        }
        HeroLookupList map = value as HeroLookupList;
        if (map != null && map.Data != null) foreach (var entry in map.Data) {
            Console.WriteLine(indent + "KEY " + entry.Key.Value.ValueText);
            Dump(entry.Value, indent + "  ");
        }
    }
    static void Main(string[] args)
    {
        string root = args[0];
        using (var stream = File.OpenRead(Path.Combine(root,"systemgenerated","client.gom"))) GOM.Instance.Parse(stream);
        for (int i=0; i<500; i++) using (var stream = File.OpenRead(Path.Combine(root,"systemgenerated","buckets",i+".bkt"))) GOM.Instance.LoadBucket(stream);
        foreach (var definition in GOM.Instance.Definitions.Values.OrderBy(x => x.Name)) {
            string name = definition.Name ?? "";
            bool taxi = name.StartsWith("tax.tython.") || (name.Contains("tython") && (name.Contains("taxi") || name.Contains("tax."))) || definition.Id == 4611686040145570001UL;
            if (!taxi) continue;
            Console.WriteLine("DEF {0} 0x{1:X16} {2}", definition.Type, definition.Id, name);
            HeroEnumDef en = definition as HeroEnumDef;
            if (en != null) for (int i=0; i<en.Values.Count; i++) Console.WriteLine("  ENUM {0} {1}",i+1,en.Values[i]);
            HeroNodeDef node = definition as HeroNodeDef;
            if (node == null) continue;
            Console.WriteLine("  BASE {0}; GLOMS {1}", node.baseClass, String.Join(",",node.glomClasses));
            try { foreach (Variable variable in node.Variables) {
                var field = GOM.Instance.LookupDefinitionId(variable.Field.Id);
                Console.WriteLine("  FIELD {0:X16} {1} {2} = {3}", variable.Field.Id,field == null ? "?" : field.Name,variable.Value.Type,variable.Value.ValueText);
                Dump(variable.Value,"    ");
            } } catch(Exception ex) { Console.WriteLine("  ERROR "+ex.Message); }
        }
    }
}
