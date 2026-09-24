using System;
using System.Diagnostics;
using System.Collections.Generic;
using System.Globalization;
using System.Threading;
using System.IO;
using System.Text;

namespace NexusToRServer
{
    public enum LogLevel
    {
        Debug = 1,
        Info = 2,
        Warning = 4,
        Error = 8,
        Client = 16,
        EDebug = 32
    }

    class Log
    {
        private static ConsoleColor WHITE = ConsoleColor.White;
        private static ConsoleColor RED = ConsoleColor.Red;
        private static ConsoleColor BLUE = ConsoleColor.Blue;
        private static ConsoleColor CYAN = ConsoleColor.Cyan;
        private static ConsoleColor DRED = ConsoleColor.DarkRed;
        private static ConsoleColor YELLOW = ConsoleColor.Yellow;
        private static ConsoleColor GREEN = ConsoleColor.Green;
        private static ConsoleColor DGREEN = ConsoleColor.DarkGreen;
        private static ConsoleColor DGRAY = ConsoleColor.DarkGray;
        private static ConsoleColor GRAY = ConsoleColor.Gray;

        private static readonly Queue<LogItem> LogQueue = new Queue<LogItem>();
        private static readonly object LogQueueLock = new object();

        private static string _fname;
        private static LogLevel _level;

        public static void Init(string fname, LogLevel level, bool del)
        {
            _fname = fname;
            _level = level;

            if (del)
            {
                try
                {
                    File.Delete(fname);
                }
                catch
                {
                    Log.Write(LogLevel.Warning, "Could not delete previous log file");
                }
            }

            Thread wrtThread = new Thread(new ThreadStart(LogWriter));
            wrtThread.Start();
        }

        private static void sColor(ConsoleColor color)
        {
            Console.ForegroundColor = color;
        }

        public static void Write(LogLevel level, string text)
        {
            StackFrame frame = new StackFrame(1);
            var method = frame.GetMethod();
            string caller = method.DeclaringType.Name.ToString();

            finalLog(level, caller, text);
        }

        public static void Write(LogLevel level, string text, params object[] args)
        {
            StackFrame frame = new StackFrame(1);
            var method = frame.GetMethod();
            string caller = method.DeclaringType.Name.ToString();
            text = String.Format(text, args);

            finalLog(level, caller, text);
        }

        private static void LogWriter()
        {
            while (true)
            {
                LogItem item = null;
                lock (LogQueueLock)
                {
                    if (LogQueue.Count > 0)
                        item = LogQueue.Dequeue();
                }
                if (item != null)
                    outputLog(item);
                Thread.Sleep(5);
            }
        }

        private static void finalLog(LogLevel level, string caller, string text)
        {
            LogItem _lItem = new LogItem(level, caller, text);
            lock (LogQueueLock)
                LogQueue.Enqueue(_lItem);
        }

        private static void outputLog(LogItem lItem)
        {

            DateTime thisDate = DateTime.Now;
            CultureInfo culture = new CultureInfo("en-US");

            finalWrite(String.Format("[{0}] {1}: {2}\r\n", thisDate.ToString("yyyy-MM-dd HH:mm:ss", culture), lItem.Caller, lItem.Text));

            if (!((_level & lItem.Level) == lItem.Level))
                goto Finish;

            sColor(DGRAY);
            Console.Write("[{0}] ", (thisDate.ToString("HH:mm:ss", culture)));
            sColor(GRAY);
            Console.Write("{0}: ", lItem.Caller);
            switch (lItem.Level)
            {
                case LogLevel.Debug:
                    sColor(CYAN);
                    break;
                case LogLevel.Info:
                    sColor(WHITE);
                    break;
                case LogLevel.Warning:
                    sColor(YELLOW);
                    break;
                case LogLevel.Error:
                    sColor(RED);
                    break;
                case LogLevel.Client:
                    sColor(DGREEN);
                    break;
                case LogLevel.EDebug:
                    sColor(GREEN);
                    break;
                default:
                    sColor(WHITE);
                    break;
            }
            Console.Write("{0}\r\n", lItem.Text);
            sColor(WHITE);

        Finish:
            lItem.IsDone = true;
        }

        private static void finalWrite(string inText)
        {
            try
            {
                StreamWriter _logWriter;
                _logWriter = new StreamWriter(_fname, true);
                _logWriter.Write(inText);
                _logWriter.Flush();
                _logWriter.Close();
                _logWriter.Dispose();
            }
            catch { }
        }

        private class LogItem
        {
            public LogItem(LogLevel level, string caller, string text)
            {
                this.Level = level;
                this.Caller = caller;
                this.Text = text;
                this.IsDone = false;
            }

            public LogLevel Level { get; set; }
            public string Caller { get; set; }
            public string Text { get; set; }
            public bool IsDone { get; set; }
        }
    }
}
