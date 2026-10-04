using System;
class HashPaths {
 static void Main() { string path; while((path=Console.ReadLine())!=null) Console.WriteLine("{0:X16}\t{1}", Hero.Repository.Hasher.Hash("/resources"+path),path); }
}
