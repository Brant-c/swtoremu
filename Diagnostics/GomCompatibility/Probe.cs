using System;
using System.IO;
using Hero;
class Probe {
    static int Main(string[] args) {
        int records = 0, accepted = 0, failed = 0, ignored = 0;
        if (args.Length > 1) {
            Repository.Instance.AddFile(args[1]);
            using (var actual = Repository.Instance.GetFile("/resources/systemgenerated/client.gom")) {
                if (actual == null) throw new InvalidDataException("Original repository reader could not resolve client.gom");
                byte[] expected = File.ReadAllBytes(args[0]);
                if (actual.Length != expected.Length) throw new InvalidDataException("Length mismatch");
                for (int i = 0; i < expected.Length; i++) if (actual.ReadByte() != expected[i]) throw new InvalidDataException("Payload mismatch");
                Console.WriteLine("Original archive reader: filename hash lookup and every payload byte PASS");
            }
        }
        using (var stream = File.OpenRead(args[0]))
        using (var reader = new BinaryReader(stream)) {
            while (stream.Position < stream.Length) {
                uint magic = reader.ReadUInt32(); int version = reader.ReadInt32();
                if (magic != 0x424c4244 || (version != 1 && version != 2)) throw new InvalidDataException("Unsupported chunk");
                while (true) {
                    long start = stream.Position; int length = reader.ReadInt32();
                    if (length == 0) break;
                    if (length < 4 || start + length > stream.Length) throw new InvalidDataException("Invalid length");
                    stream.Position = start; byte[] data = reader.ReadBytes(length); records++;
                    try {
                        var def = Hero.Definition.HeroDefinition.Create(data, version);
                        if (def == null) ignored++;
                        else { GOM.Instance.ParseDefinition(data, version); accepted++; }
                    } catch (Exception ex) {
                        failed++;
                        if (failed <= 12) Console.WriteLine("FAIL record={0} offset={1} length={2}: {3}", records, start, length, ex);
                    }
                    stream.Position = (start + length + 7) & ~7L;
                }
            }
        }
        Console.WriteLine("Records={0}; accepted={1}; ignored={2}; failed={3}; definitions={4}", records, accepted, ignored, failed, GOM.Instance.Definitions.Count);
        foreach (var pair in GOM.Instance.DefinitionsByName) Console.WriteLine("{0}: {1}", pair.Key, pair.Value.Count);
        return failed == 0 ? 0 : 1;
    }
}
