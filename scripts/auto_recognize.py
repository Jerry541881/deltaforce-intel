#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键全自动：启动WeGame -> 点击 -> 截图 -> .NET OCR识别(带坐标) -> 上传
绕过 PowerShell 的 WinRT 异步坑，改用 Add-Type 编译 C# 同步调用
"""
import os
import re
import sys
import json
import time
import tempfile
import subprocess
import upload_codes as uc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHOT_PATH = os.path.join(BASE_DIR, "last_code_shot.png")
MAPS = ["零号大坝", "长弓溪谷", "巴克什", "航天基地", "潮汐监狱", "AZ3"]

DEFAULT = {
    "wegame_exe": r"D:\Program Files (x86)\WeGame\wegame.exe",
    "game_icon": None, "code_entry": None, "shot_region": None,
    "wait_startup": 40, "wait_click": 6, "wait_popup": 3,
}

# C# 源码：编译后同步调用 WinRT OCR，输出 文本|左|上|宽|高
CSHARP = r'''
using System;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices.WindowsRuntime;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage;
using Windows.Storage.Streams;
using Windows.Globalization;

public class OcrRunner {
    public static void Main(string[] args) {
        if (args.Length < 1) { Console.WriteLine("ERR|no path"); return; }
        string path = args[0];
        try {
            var file = StorageFile.GetFileFromPathAsync(path).AsTask().GetAwaiter().GetResult();
            var stream = file.OpenAsync(FileAccessMode.Read).AsTask().GetAwaiter().GetResult();
            var decoder = BitmapDecoder.CreateAsync(stream).AsTask().GetAwaiter().GetResult();
            var bitmap = decoder.GetSoftwareBitmapAsync().AsTask().GetAwaiter().GetResult();

            OcrEngine engine = null;
            try { engine = OcrEngine.TryCreateFromLanguage(new Language("en-US")); } catch { }
            if (engine == null) { engine = OcrEngine.TryCreateFromUserProfileLanguages(); }
            if (engine == null) { Console.WriteLine("ERR|engine null"); return; }

            var result = engine.RecognizeAsync(bitmap).AsTask().GetAwaiter().GetResult();
            foreach (var line in result.Lines) {
                foreach (var w in line.Words) {
                    var b = w.BoundingRect;
                    Console.WriteLine(string.Format("{0}|{1}|{2}|{3}|{4}",
                        w.Text, (int)b.X, (int)b.Y, (int)b.Width, (int)b.Height));
                }
            }
            Console.WriteLine("DONE|" + result.Lines.Count);
        } catch (Exception ex) {
            Console.WriteLine("ERR|" + ex.GetType().Name + "|" + ex.Message.Replace("\n", " "));
        }
    }
}
'''


def run_ps(script, timeout=180):
    ps_path = os.path.join(tempfile.gettempdir(), "ar_%d.ps1" % os.getpid())
    with open(ps_path, "w", encoding="utf-8-sig") as f:
        f.write(script)
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path],
            capture_output=True, timeout=timeout
        )
        raw = (r.stdout or b"") + (r.stderr or b"")
        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return raw.decode("gbk", errors="ignore")
    except Exception as e:
        print("[PowerShell] 失败:", e)
        return ""


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, shell=True, timeout=timeout)
        raw = (r.stdout or b"") + (r.stderr or b"")
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("gbk", errors="ignore")
    except Exception:
        return ""


def load_config():
    cfg = dict(DEFAULT)
    p = os.path.join(BASE_DIR, "wegame_config.json")
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def compile_ocr():
    """编译 C# OCR 程序（只编译一次，结果缓存到临时目录）"""
    exe = os.path.join(tempfile.gettempdir(), "winocr.exe")
    src = os.path.join(tempfile.gettempdir(), "winocr.cs")
    if os.path.exists(exe):
        return exe
    with open(src, "w", encoding="utf-8-sig") as f:
        f.write(CSHARP)

    refs = [
        "System.Runtime.WindowsRuntime.dll",
        "Windows.Foundation.FoundationContract.winmd",
        "Windows.Graphics.Imaging.ImagingContract.winmd",
        "Windows.Media.Ocr.OcrContract.winmd",
        "Windows.Storage.StorageContract.winmd",
        "Windows.Globalization.GlobalizationContract.winmd",
    ]
    ref_str = " ".join('-r:"%s"' % r for r in refs)
    ps = f'''
$ErrorActionPreference = "Stop"
$csc = Get-ChildItem -Path "$env:WINDIR\\Microsoft.NET\\Framework*" -Filter "csc.exe" -Recurse -ErrorAction SilentlyContinue |
       Where-Object {{ $_.FullName -like "*Framework64*" }} | Select-Object -First 1
if ($null -eq $csc) {{
    $csc = Get-ChildItem -Path "$env:WINDIR\\Microsoft.NET\\Framework*" -Filter "csc.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
}}
if ($null -eq $csc) {{ Write-Output "NOCSC"; exit 1 }}
Write-Output ("CSC=" + $csc.FullName)
& $csc.FullName /nologo /optimize /target:exe /out:"{exe}" {ref_str} "{src}" 2>&1 | Out-String
if ($LASTEXITCODE -eq 0) {{ Write-Output "BUILD_OK" }} else {{ Write-Output "BUILD_FAIL" }}
'''
    out = run_ps(ps, timeout=180)
    print("[编译]", out.strip()[:800])
    if "BUILD_OK" not in out:
        return None
    return exe


def ocr_with_pos(img_path):
    """返回 [(text, x, y, w, h), ...]"""
    exe = compile_ocr()
    if not exe:
        print("[OCR] 编译失败，无法识别")
        return []
    r = subprocess.run([exe, img_path], capture_output=True, timeout=180)
    out = (r.stdout or b"").decode("utf-8", errors="ignore")
    items = []
    for line in out.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        if line.startswith("ERR|") or line.startswith("DONE|"):
            if line.startswith("ERR|"):
                print("[OCR错误]", line)
            continue
        p = line.split("|")
        if len(p) < 5:
            continue
        try:
            items.append((p[0], int(p[1]), int(p[2]), int(p[3]), int(p[4])))
        except ValueError:
            continue
    return items


def activate_wegame():
    out = run_ps(r'''
Add-Type -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr hWnd);
[DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr hWnd, int nCmdShow);
[DllImport("user32.dll")] public static extern bool IsIconic(System.IntPtr hWnd);
'@ -Name W -Namespace Native
$procs = Get-Process -Name wegame -ErrorAction SilentlyContinue
if (-not $procs) { Write-Output "notfound"; exit }
$h = 0
foreach ($p in $procs) { if ($p.MainWindowHandle -ne 0) { $h = $p.MainWindowHandle; break } }
if ($h -eq 0) { Write-Output "nohwnd"; exit }
if ([Native.W]::IsIconic($h)) { [Native.W]::ShowWindow($h, 9) | Out-Null }
Start-Sleep -Milliseconds 500
[Native.W]::ShowWindow($h, 9) | Out-Null
Start-Sleep -Milliseconds 300
if ([Native.W]::SetForegroundWindow($h)) { Write-Output "activated" } else { Write-Output "failed" }
''', timeout=40)
    print("[窗口]", out or "(无输出)")
    return "activated" in out


def click(x, y):
    run_ps(f'''
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({int(x)}, {int(y)})
Add-Type -MemberDefinition '[DllImport("user32.dll")] public static extern void mouse_event(int flags, int dx, int dy, int cButtons, int extraInfo);' -Name U -Namespace W
Start-Sleep -Milliseconds 300
[W.U]::mouse_event(0x00000002, 0, 0, 0, 0)
Start-Sleep -Milliseconds 120
[W.U]::mouse_event(0x00000004, 0, 0, 0, 0)
Start-Sleep -Milliseconds 250
[W.U]::mouse_event(0x00000002, 0, 0, 0, 0)
Start-Sleep -Milliseconds 120
[W.U]::mouse_event(0x00000004, 0, 0, 0, 0)
''', timeout=40)


def screenshot(region):
    if region and len(region) == 4:
        x, y, w, h = [int(v) for v in region]
        script = f'''
Add-Type -AssemblyName System.Drawing
$b = New-Object System.Drawing.Bitmap({w}, {h})
$g = [System.Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen({x}, {y}, 0, 0, $b.Size)
$b.Save("{SHOT_PATH}")
Write-Output "区域 {w}x{h}"
'''
    else:
        script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$s = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$b = New-Object System.Drawing.Bitmap($s.Width, $s.Height)
$g = [System.Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen($s.Location, [System.Drawing.Point]::Empty, $s.Size)
$b.Save("{SHOT_PATH}")
Write-Output "全屏"
'''
    print("[截图]", run_ps(script, timeout=60))


def ensure_wegame(exe, wait):
    if "wegame.exe" in run_cmd("tasklist").lower():
        print("[WeGame] 已在运行")
        return True
    if not os.path.exists(exe):
        print("[错误] 找不到:", exe)
        return False
    print("[WeGame] 启动中...")
    subprocess.Popen([exe], shell=False)
    for i in range(wait):
        time.sleep(1)
        if "wegame.exe" in run_cmd("tasklist").lower():
            print(f"[WeGame] 已启动（{i+1}秒）")
            time.sleep(12)
            return True
    return True


def pick_digits(items):
    cands = []
    for text, x, y, w, h in items:
        t = text.strip()
        m = re.search(r"\d{4}(?!\d)", t)
        if m:
            cands.append((x, y, m.group(1)))
        elif re.fullmatch(r"\d{3}", t):
            cands.append((x, y, "0" + t))
    return cands


def cluster_row(cands, tol=25):
    if not cands:
        return []
    groups = []
    for x, y, c in sorted(cands, key=lambda t: t[1]):
        for g in groups:
            if abs(y - g[0]) <= tol:
                g[1].append((x, c)); break
        else:
            groups.append([y, [(x, c)]])
    groups.sort(key=lambda g: (-len(g[1]), g[0]))
    best = groups[0][1]
    best.sort(key=lambda t: t[0])
    return [c for _, c in best]


def manual_input(missing):
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk(); root.withdraw()
        for m in missing:
            v = simpledialog.askstring("补录密码", f"{m} 的4位密码：", parent=root)
            if v and re.fullmatch(r"\s*\d{1,4}\s*", v):
                yield m, v.strip().zfill(4)
        root.destroy()
    except Exception as e:
        print("[补录] 不可用:", e)


def main():
    cfg = load_config()
    print("=" * 58)
    print("[1/4] 打开 WeGame 并截图")
    ensure_wegame(cfg["wegame_exe"], int(cfg["wait_startup"]))
    activate_wegame(); time.sleep(2)
    if cfg.get("game_icon"):
        click(*cfg["game_icon"]); time.sleep(int(cfg["wait_click"]))
    activate_wegame(); time.sleep(1)
    if cfg.get("code_entry"):
        click(*cfg["code_entry"])
        time.sleep(int(cfg["wait_click"]) + int(cfg["wait_popup"]))
    screenshot(cfg.get("shot_region"))
    if not os.path.exists(SHOT_PATH):
        print("[失败] 无截图"); sys.exit(1)
    print("      已保存:", SHOT_PATH, os.path.getsize(SHOT_PATH), "字节")

    print("\n[2/4] OCR 识别（.NET 直调）")
    items = ocr_with_pos(SHOT_PATH)
    print("  词数:", len(items))
    for t in items[:20]:
        print(f"    {t[0]!r} @ x={t[1]} y={t[2]}")

    cands = pick_digits(items)
    codes = cluster_row(cands)
    print(f"  候选: {cands}")
    print(f"  聚类: {codes}")

    results = dict(zip(MAPS, codes[:6])) if len(codes) >= 6 else {}

    print("\n[3/4] 校验")
    if len(results) < 6:
        missing = [m for m in MAPS if m not in results]
        print("  缺少:", missing, "-> 弹窗补录")
        for m, v in manual_input(missing):
            results[m] = v
    else:
        print("  六张齐全")

    errs = uc.validate(results)
    if errs:
        print("[拒绝上传]")
        for e in errs:
            print("   -", e)
        sys.exit(2)

    print("\n[4/4] 上传")
    for m in MAPS:
        print(f"   {m}: {results[m]}")
    ok = uc.upload(results, uc.bj_today())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()