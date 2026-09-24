using System;
using System.IO;
using System.Threading;
using NexusToRServer;

class LogQueueStressTest
{
    static void Main(string[] args)
    {
        string path = args[0];
        Log.Init(path, (LogLevel)0, false);
        Thread[] producers = new Thread[8];
        for (int n = 0; n < producers.Length; n++)
        {
            int producer = n;
            producers[n] = new Thread(() => {
                for (int i = 0; i < 100; i++)
                    Log.Write(LogLevel.Info, "entry-{0}-{1}", producer, i);
            });
            producers[n].Start();
        }
        foreach (Thread producer in producers) producer.Join();
        DateTime deadline = DateTime.UtcNow.AddSeconds(20);
        while (DateTime.UtcNow < deadline)
        {
            try
            {
                string[] lines = File.ReadAllLines(path);
                var unique = new System.Collections.Generic.HashSet<string>();
                foreach (string line in lines)
                    unique.Add(line.Substring(line.IndexOf("entry-")));
                if (lines.Length == 800 && unique.Count == 800)
                {
                    Console.WriteLine("PASS: 800 unique messages from 8 concurrent producers.");
                    Environment.Exit(0);
                }
            }
            catch (IOException) { }
            Thread.Sleep(100);
        }
        Console.Error.WriteLine("FAIL: incomplete or duplicate log output.");
        Environment.Exit(1);
    }
}
