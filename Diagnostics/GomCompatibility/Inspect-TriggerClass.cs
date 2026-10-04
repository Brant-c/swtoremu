using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Hero;
using Hero.Definition;

internal static class InspectTriggerClass
{
    private static readonly HashSet<ulong> Visited = new HashSet<ulong>();

    private static void DumpClass(HeroClassDef definition, string indent)
    {
        Console.WriteLine("{0}class 0x{1:X16} {2} (fields={3})", indent,
            definition.Id, definition.Name, definition.Fields.Count);
        if (!Visited.Add(definition.Id))
        {
            Console.WriteLine("{0}  (recursion stopped)", indent);
            return;
        }

        foreach (var fieldId in definition.Fields.OrderBy(fieldId => fieldId.Id))
        {
            HeroFieldDef field = fieldId.Definition as HeroFieldDef;
            Console.WriteLine("{0}  field 0x{1:X16} {2} : {3}", indent, fieldId.Id,
                field == null ? "(unknown)" : field.Name,
                field == null ? "?" : field.FieldType.ToString());
        }

        IEnumerable<HeroClassDef> embedded = definition.Fields
            .Select(fieldId => fieldId.Definition as HeroFieldDef)
            .Where(field => field != null)
            .SelectMany(field => Embedded(field));
        foreach (HeroClassDef child in embedded)
            DumpClass(child, indent + "    ");
    }

    private static IEnumerable<HeroClassDef> Embedded(HeroFieldDef field)
    {
        // Only follow direct class components; lists and maps are reported by
        // name only so the output stays bounded and readable.
        HeroType type = field.FieldType;
        if (type == null || type.Type != HeroTypes.Class)
            yield break;
        if (type.Id == null || type.Id.Id == 0UL)
            yield break;

        HeroClassDef resolved =
            GOM.Instance.LookupDefinitionId(type.Id.Id) as HeroClassDef;
        if (resolved != null)
            yield return resolved;
    }

    private static int Main(string[] args)
    {
        if (args.Length != 1)
        {
            Console.Error.WriteLine("usage: Inspect-TriggerClass <resource-cache-root>");
            return 2;
        }

        string root = args[0];
        using (FileStream gom = File.OpenRead(Path.Combine(root, "systemgenerated", "client.gom")))
            GOM.Instance.Parse(gom);
        for (int index = 0; index < 500; index++)
        {
            string path = Path.Combine(root, "systemgenerated", "buckets", index + ".bkt");
            if (!File.Exists(path))
                break;
            using (FileStream bucket = File.OpenRead(path))
                GOM.Instance.LoadBucket(bucket);
        }

        Console.WriteLine("--- classes owning a TriggerParam / TriggerClassType field ---");
        foreach (HeroClassDef candidate in GOM.Instance.Definitions.Values.OfType<HeroClassDef>())
        {
            bool matches = candidate.Fields.Any(fieldId =>
            {
                HeroFieldDef field = fieldId.Definition as HeroFieldDef;
                return field != null &&
                    (field.Name == "TriggerParam" ||
                     field.Name == "TriggerClassType" ||
                     field.Name == "TriggerScript");
            });
            if (!matches)
                continue;
            DumpClass(candidate, "");
            Console.WriteLine();
        }

        Console.WriteLine("--- engine trigger classes by known id ---");
        foreach (ulong id in new ulong[]
        {
            3758000125UL,          // TriggerInstance (0xDFFE87FD, from the phase script)
            4611686025669311862UL, // HBNode
            4611686033869670001UL, // hydTriggerEntity
            4611686040883670000UL, // mapTrigger
            4611686029857367645UL, // phsGateway
        })
        {
            HeroClassDef definition = GOM.Instance.LookupDefinitionId(id) as HeroClassDef;
            if (definition == null)
            {
                Console.WriteLine("0x{0:X16} (not a class in this cache)", id);
                continue;
            }
            DumpClass(definition, "");
            Console.WriteLine();
        }

        return 0;
    }
}
