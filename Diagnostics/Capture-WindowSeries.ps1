param(
    [int]$TotalSeconds = 600,
    [int]$IntervalSeconds = 20,
    [string]$OutDirectory = 'D:\SWTORClassic\swtoremu\Diagnostics\shots'
)

Add-Type -ReferencedAssemblies System.Drawing @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public class WinShot {
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdcBlt, uint nFlags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", CharSet=CharSet.Auto)] public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc proc, IntPtr lParam);
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }

    public static IntPtr FindWindow() {
        IntPtr found = IntPtr.Zero;
        EnumWindows(delegate(IntPtr hWnd, IntPtr lParam) {
            if (!IsWindowVisible(hWnd)) return true;
            System.Text.StringBuilder sb = new System.Text.StringBuilder(256);
            GetWindowText(hWnd, sb, 256);
            string title = sb.ToString();
            if (title.StartsWith("Star Wars")) { found = hWnd; return false; }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    public static string Capture(IntPtr handle, string path) {
        RECT rc; GetWindowRect(handle, out rc);
        int w = rc.Right - rc.Left, h = rc.Bottom - rc.Top;
        if (w <= 0 || h <= 0) return "zero-size";
        using (Bitmap bmp = new Bitmap(w, h)) {
            using (Graphics g = Graphics.FromImage(bmp)) {
                IntPtr dc = g.GetHdc();
                bool ok = PrintWindow(handle, dc, 2);
                g.ReleaseHdc(dc);
                if (!ok) return "printwindow-failed";
            }
            ImageCodecInfo jpg = null;
            foreach (ImageCodecInfo c in ImageCodecInfo.GetImageEncoders())
                if (c.FormatID == ImageFormat.Jpeg.Guid) jpg = c;
            EncoderParameters p = new EncoderParameters(1);
            p.Param[0] = new EncoderParameter(System.Drawing.Imaging.Encoder.Quality, 50L);
            bmp.Save(path, jpg, p);
        }
        return "ok";
    }
}
'@

if (!(Test-Path $OutDirectory)) { New-Item -ItemType Directory -Path $OutDirectory | Out-Null }
Get-ChildItem $OutDirectory -Filter '*.jpg' -ErrorAction SilentlyContinue | Remove-Item -Force

$start = Get-Date
$index = 0
$wasPresent = $false
while (((Get-Date) - $start).TotalSeconds -lt $TotalSeconds) {
    $hwnd = [WinShot]::FindWindow()
    $stamp = (Get-Date).ToString('HH:mm:ss')
    if ($hwnd -eq [IntPtr]::Zero) {
        if ($wasPresent) { Write-Output "$stamp window gone (client exited)" }
        $wasPresent = $false
        Start-Sleep -Seconds $IntervalSeconds
        continue
    }
    $wasPresent = $true
    $index++
    $path = Join-Path $OutDirectory ('shot-{0:d3}.jpg' -f $index)
    $result = [WinShot]::Capture($hwnd, $path)
    $size = 0
    if (Test-Path $path) { $size = (Get-Item $path).Length }
    Write-Output ("{0} handled={1} result={2} bytes={3} file={4}" -f $stamp, $hwnd, $result, $size, (Split-Path $path -Leaf))
    Start-Sleep -Seconds $IntervalSeconds
}
Write-Output 'capture loop finished'
