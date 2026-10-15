#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三角洲每日密码 · 全自动
启动WeGame → 点击游戏 → 打开每日密码 → 截图 → OCR识别 → 校验 → 补录 → 上传
OCR 方案：PowerShell -MTA + InMemoryRandomAccessStream + GetAwaiter（已验证可用）
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

# 已验证可用的 OCR 脚本：MTA + InMemoryRandomAccessStream + GetAwaiter
PS_OCR = r'''
param([string]$path)
$ErrorActionPreference = "Continue"
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
if ($null -eq $asTaskGeneric) { Write-Output "FATAL|no AsTask"; exit }
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    return $asTask.Invoke($null, @($WinRtTask)).GetAwaiter().GetResult()
}
try {
    [Windows.Storage.Streams.InMemoryRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
    [Windows.Storage.Streams.DataWriter,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
    [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging.BitmapDecoder,ContentType=WindowsRuntime] | Out-Null
    [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
    [Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime] | Out-Null

    $bytes = [System.IO.File]::ReadAllBytes($path)
    $stream = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $writer = New-Object Windows.Storage.Streams.DataWriter($stream)
    $writer.WriteBytes($bytes)
    $null = Await ($writer.StoreAsync()) ([uint32])
    $null = $writer.DetachStream()
    $null = $stream.Seek(0)

    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

    $engine = $null
    foreach ($tag in @("zh-Hans-CN","en-US")) {
        try { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new($tag)) } catch {}
        if ($null -ne $engine) { break }
    }
    if ($null -eq $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
    if ($null -eq $engine) { Write-Output "FATAL|no engine"; exit }

    $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
    foreach ($line in $result.Lines) {
        foreach ($w in $line.Words) {
            $b = $w.BoundingRect
            Write-Output ("W|" + $w.Text + "|" + [int]$b.X + "|" + [int]$b.Y + "|" + [int]$b.Width + "|" + [int]$b.Height)
        }
    }
    Write-Output "OCR_OK"
} catch {
    Write-Output ("EX|" + $_.Exception.Message)
}
'''


def dec(raw):
    if not raw:
        return ""
    try:
        s = raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""
    if "\ufffd" in s:
        try:
            s = raw.decode("gbk", errors="ignore")
        except Exception:
            pass
    return s


def run_ps(script, args=None, timeout=180):
    ps_path = os.path.join(tempfile.gettempdir(), "af_%d.ps1" % os.getpid())
    with open(ps_path, "w", encoding="utf-8-sig") as f:
        f.write(script)
    # 关键：必须 -MTA
    cmd = ["powershell.exe", "-MTA", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path]
    if args:
        cmd += args
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return dec(r.stdout) + dec(r.stderr)
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
    print("[窗口]", out.strip() or "(无输出)")
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
    print("[截图]", run_ps(script, timeout=60).strip())


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


def ocr_with_pos(path):
    out = run_ps(PS_OCR, ["-path", path], timeout=180)
    items = []
    ok = False
    for line in out.splitlines():
        line = line.strip()
        if line == "OCR_OK":
            ok = True
        elif line.startswith("W|"):
            p = line.split("|")
            if len(p) >= 6:
                try:
                    items.append((p[1], int(p[2]), int(p[3]), int(p[4]), int(p[5])))
                except ValueError:
                    pass
        elif line.startswith("EX|") or line.startswith("FATAL|"):
            print("[OCR错误]", line)
    return items, ok


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
    print("=" * 60)
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
    print("      ", SHOT_PATH, os.path.getsize(SHOT_PATH), "字节")

    print("\n[2/4] OCR 识别")
    items, ok = ocr_with_pos(SHOT_PATH)
    print("      词数:", len(items), "| 状态:", "OK" if ok else "FAILED")
    if items:
        print("      识别原文:", " ".join(t[0] for t in items)[:200])
    cands = pick_digits(items)
    codes = cluster_row(cands)
    print("      聚类结果:", codes)

    results = dict(zip(MAPS, codes[:6])) if len(codes) >= 6 else {}

    print("\n[3/4] 校验")
    if len(results) < 6:
        missing = [m for m in MAPS if m not in results]
        print("      缺少:", missing, "-> 弹窗补录")
        for m, v in manual_input(missing):
            results[m] = v
    else:
        print("      六张齐全 ✅")

    errs = uc.validate(results)
    if errs:
        print("[拒绝上传]")
        for e in errs:
            print("       -", e)
        sys.exit(2)

    print("\n[4/4] 上传")
    for m in MAPS:
        print(f"      {m}: {results[m]}")
    ok = uc.upload(results, uc.bj_today())
    print("\n[完成]" if ok else "\n[失败]")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()