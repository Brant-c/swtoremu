using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Hero;
using Hero.Definition;
using Hero.Types;

internal static class InspectEffEventMetadata
{
    private static void DumpValue(HeroAnyValue value, string indent)
    {
        HeroList list = value as HeroList;
        if (list != null)
        {
            if (list.Data == null)
                return;
            for (int index = 0; index < list.Data.Count; index++)
            {
                Console.WriteLine("{0}[{1}] {2}", indent, index,
                    list.Data[index].Value.ValueText);
                DumpValue(list.Data[index].Value, indent + "  ");
            }
            return;
        }

        HeroClass embedded = value as HeroClass;
        if (embedded != null)
        {
            foreach (Variable variable in embedded.Variables)
            {
                Console.WriteLine("{0}field 0x{1:X16} {2} = {3}", indent,
                    variable.Field.Id, variable.Value.Type, variable.Value.ValueText);
                DumpValue(variable.Value, indent + "  ");
            }
        }
    }

    private static void DumpEffect(ulong id)
    {
        HeroNodeDef node = GOM.Instance.LookupDefinitionId(id) as HeroNodeDef;
        Console.WriteLine("effect 0x{0:X16}: {1}", id,
            node == null ? "(missing)" : node.Name);
        if (node == null)
            return;
        foreach (Variable variable in node.Variables)
        {
            Console.WriteLine("  field 0x{0:X16} {1} = {2}", variable.Field.Id,
                variable.Value.Type, variable.Value.ValueText);
            DumpValue(variable.Value, "    ");
        }
    }

    private static void DumpEnum(ulong id, string name)
    {
        HeroEnumDef definition = GOM.Instance.LookupDefinitionId(id) as HeroEnumDef;
        Console.WriteLine("enum {0} 0x{1:X16}", name, id);
        if (definition == null)
            return;
        for (int index = 0; index < definition.Values.Count; index++)
            Console.WriteLine("  {0} = {1}", index + 1, definition.Values[index]);
    }

    private static void DumpAbility(string name)
    {
        HeroNodeDef node = GOM.Instance.GetNode(name);
        Console.WriteLine("ability {0}: {1}", name,
            node == null ? "(missing)" : String.Format("0x{0:X16}", node.Id));
        if (node == null)
            return;

        foreach (Variable variable in node.Variables)
        {
            if (variable.Value is HeroList || variable.Value is HeroClass)
                continue;
            Console.WriteLine("  scalar 0x{0:X16} {1} = {2}",
                variable.Field.Id, variable.Value.Type,
                variable.Value.ValueText);
        }

        const ulong AblEffectIds = 0x4000000A1D6B4918UL;
        HeroList effects = node.Variables
            .Where(variable => variable.Field.Id == AblEffectIds)
            .Select(variable => variable.Value as HeroList)
            .FirstOrDefault();
        if (effects == null || effects.Data == null)
        {
            Console.WriteLine("  ablEffectIDs: (missing)");
            return;
        }

        for (int index = 0; index < effects.Data.Count; index++)
        {
            HeroID effect = effects.Data[index].Value as HeroID;
            Console.WriteLine("  [{0}] 0x{1:X16} {2}", index,
                effect == null ? 0UL : effect.Id,
                effect == null || GOM.Instance.LookupDefinitionId(effect.Id) == null
                    ? "(missing)"
                    : GOM.Instance.LookupDefinitionId(effect.Id).Name);
        }
    }

    private static void DumpAbilityById(ulong id)
    {
        HeroNodeDef node = GOM.Instance.LookupDefinitionId(id) as HeroNodeDef;
        Console.WriteLine("ability-id 0x{0:X16}: {1}", id,
            node == null ? "(missing)" : node.Name);
        if (node != null)
            DumpAbility(node.Name);
    }

    private static void DumpClass(HeroClassDef definition, string indent, HashSet<ulong> seen)
    {
        if (!seen.Add(definition.Id))
            return;

        Console.WriteLine("{0}class {1} id=0x{2:X16}", indent, definition.Name, definition.Id);
        foreach (DefinitionId parentId in definition.ParentClasses)
        {
            HeroClassDef parent = parentId.Definition as HeroClassDef;
            Console.WriteLine("{0}  parent 0x{1:X16} {2}", indent, parentId.Id,
                parent == null ? "(missing)" : parent.Name);
            if (parent != null)
                DumpClass(parent, indent + "    ", seen);
        }
        for (int index = 0; index < definition.Fields.Count; index++)
        {
            DefinitionId fieldId = definition.Fields[index];
            HeroFieldDef field = fieldId.Definition as HeroFieldDef;
            Console.WriteLine("{0}  [{1,2}] 0x{2:X16} {3}", indent, index, fieldId.Id,
                field == null ? "(missing)" : field.Name + " : " + field.FieldType);
        }
    }

    private static int Main(string[] args)
    {
        if (args.Length != 1)
        {
            Console.Error.WriteLine("usage: Inspect-EffEvent-Metadata <resource-cache-root>");
            return 2;
        }

        string root = args[0];
        using (FileStream gom = File.OpenRead(Path.Combine(root, "systemgenerated", "client.gom")))
            GOM.Instance.Parse(gom);
        for (int index = 0; index < 500; index++)
        {
            string path = Path.Combine(root, "systemgenerated", "buckets", index + ".bkt");
            using (FileStream bucket = File.OpenRead(path))
                GOM.Instance.LoadBucket(bucket);
        }

        DumpAbility("abl.jedi_knight.introspection");
        DumpAbility("abl.jedi_knight.force_might");
        DumpAbilityById(0xE00079A6400301F5UL);
        DumpAbilityById(0xE00081CEF00BAF68UL);
        DumpEffect(0xE0008CAE3E2BB386UL);
        DumpEffect(0xE000A38DCFFE7CC2UL);
        DumpEffect(0xE000A48DCFFE7A0DUL);
        DumpEffect(0xE000A18DCFFD8164UL);
        DumpEffect(0xE000A28DCFFE7E97UL);
        DumpEffect(0xE000A78DCFFE7716UL);
        DumpEffect(0xE000A88DCFFE7541UL);
        DumpEffect(0xE000A58DCFFE7BB8UL);
        DumpEffect(0xE000A68DCFFE79EBUL);
        DumpEffect(0xE000C3452BFEEA1CUL);
        DumpEffect(0xE000C2452BFEE9AFUL);
        DumpEffect(0xE00015A245BFAC89UL);
        DumpEffect(0xE00016A245BFAA5AUL);
        DumpEffect(0xE00017A245BFA9EFUL);
        DumpEffect(0xE00018A245BFA7A0UL);
        DumpEnum(0x4000000004A333FEUL, "effResult");
        DumpEnum(0x40000004E251D1C9UL, "effTriggerEnum");
        DumpEnum(0x40000004E251D1C7UL, "effActionEnum");
        Console.WriteLine();

        Dictionary<string, HeroDefinition> classes =
            GOM.Instance.DefinitionsByName[HeroDefinition.Types.Class];
        foreach (string name in classes.Keys
            .Where(name => name.StartsWith("effEvent", StringComparison.OrdinalIgnoreCase))
            .OrderBy(name => name))
        {
            DumpClass((HeroClassDef)classes[name], "", new HashSet<ulong>());
            Console.WriteLine();
        }

        ulong[] knownIds = {
            0x4000000062258005UL,
            0x400000006A525D00UL,
            0x400000006225807EUL, // effEventTargetDetails
            0x400000006225807FUL  // effEventActionDetails
        };
        foreach (ulong id in knownIds)
        {
            HeroClassDef known = GOM.Instance.LookupDefinitionId(id) as HeroClassDef;
            if (known != null)
            {
                DumpClass(known, "", new HashSet<ulong>());
                Console.WriteLine();
            }
        }

        foreach (HeroClassDef candidate in GOM.Instance.Definitions.Values.OfType<HeroClassDef>())
        {
            bool matches = candidate.Fields.Any(fieldId =>
            {
                HeroFieldDef field = fieldId.Definition as HeroFieldDef;
                return field != null && field.Name.StartsWith("effEvent", StringComparison.OrdinalIgnoreCase);
            });
            if (matches)
            {
                DumpClass(candidate, "", new HashSet<ulong>());
                Console.WriteLine();
            }
        }
        return 0;
    }
}
