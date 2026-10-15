#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三角洲每日密码 · 全自动无人值守（重试加固版）
启动/激活 WeGame -> 点击 -> 截图 -> OCR -> 校验 -> 直接入库
冷启动慢、界面未就绪时自动重试最多 3 次
不足 6 组绝不上传
"""
import os
import re
import sys
import json
import time
import tempfile
import subprocess
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHOT_PATH = os.path.join(BASE_DIR, "last_code_shot.png")
CONFIG_PATH = os.path.join(BASE_DIR, "supabase_config.json")
LOG_PATH = os.path.join(BASE_DIR, "auto_daily.log")
MAPS = ["零号大坝", "长弓溪谷", "巴克什", "航天基地", "潮汐监狱", "AZ3"]
MAX_TRY = 3

DEFAULT = {
    "wegame_exe": r"D:\Program Files (x86)\WeGame\wegame.exe",
    "game_icon": None, "code_entry": None, "shot_region": None,
    "wait_startup": 90, "wait_click": 6, "wait_popup": 3,
}

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
} catch { Write-Output ("EX|" + $_.Exception.Message) }
'''


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


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
    ps_path = os.path.join(tempfile.gettempdir(), "ad_%d.ps1" % os.getpid())
    with open(ps_path, "w", encoding="utf-8-sig") as f:
        f.write(script)
    cmd = ["powershell.exe", "-MTA", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path]
    if args:
        cmd += args
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return dec(r.stdout) + dec(r.stderr)
    except Exception as e:
        log(f"PowerShell 失败: {e}")
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


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                default.update(d)
        except Exception:
            pass
    return default


def bj_today():
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d")


def wg_running():
    return "wegame.exe" in run_cmd("tasklist").lower()


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
    ok = "activated" in out
    log(f"  窗口激活: {out.strip() or '(无输出)'}")
    return ok


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
'''
    run_ps(script, timeout=60)


def ensure_wegame(exe, wait):
    if wg_running():
        log("WeGame 已在运行")
        return True
    if not os.path.exists(exe):
        log(f"找不到 WeGame: {exe}")
        return False
    log(f"启动 WeGame，最多等 {wait} 秒...")
    subprocess.Popen([exe], shell=False)
    for i in range(wait):
        time.sleep(1)
        if wg_running():
            log(f"WeGame 进程已起（{i+1}秒），再等 15 秒让界面就绪")
            time.sleep(15)
            return True
    log("启动等待超时，继续尝试点击")
    return True


def ocr_words(path):
    out = run_ps(PS_OCR, ["-path", path], timeout=180)
    words = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("W|"):
            p = line.split("|")
            if len(p) >= 6:
                try:
                    words.append({"t": p[1], "x": int(p[2]), "y": int(p[3]),
                                  "w": int(p[4]), "h": int(p[5])})
                except ValueError:
                    pass
        elif line.startswith("EX|") or line.startswith("FATAL|"):
            log(f"  OCR 错误: {line}")
    return words


def clean_num(t):
    return re.sub(r"\D", "", t)


def extract_codes(words):
    nums = []
    for w in words:
        d = clean_num(w["t"])
        if not d:
            continue
        if re.search(r"[A-Za-z]", w["t"]) and len(d) <= 1:
            continue
        nums.append({"d": d, "x": w["x"], "y": w["y"],
                     "w": w["w"], "h": w["h"]})
    if not nums:
        return []

    groups = []
    for n in sorted(nums, key=lambda v: v["y"]):
        for g in groups:
            if abs(n["y"] - g[0]) <= max(n["h"], 20) * 0.6:
                g[1].append(n)
                break
        else:
            groups.append([n["y"], [n]])
    groups.sort(key=lambda g: (-len(g[1]), g[0]))
    row = sorted(groups[0][1], key=lambda v: v["x"])

    parts = []
    for n in row:
        if parts:
            prev = parts[-1]
            gap = n["x"] - (prev["x"] + prev["w"])
            if gap <= prev["w"] * 0.8 and len(prev["d"]) + len(n["d"]) <= 4:
                prev["d"] += n["d"]
                prev["w"] = (n["x"] + n["w"]) - prev["x"]
                continue
        parts.append(dict(n))
    return [p["d"].zfill(4) for p in parts if 1 <= len(p["d"]) <= 4]


def upload(results, date_str):
    import requests
    cfg = load_json(CONFIG_PATH, {})
    url = (cfg.get("url") or "").rstrip("/")
    key = cfg.get("key") or ""
    if not url or not key:
        log("未配置 supabase_config.json")
        return False
    code_str = "|".join(f"{m}:{results[m]}" for m in MAPS)
    api = f"{url}/rest/v1/daily_codes"
    payload = [{
        "code_date": date_str,
        "code_value": code_str,
        "verified": True,
        "source": "wegame-ocr-auto",
    }]
    h_upsert = {
        "apikey": key, "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,on_conflict=code_date,return=minimal",
    }
    try:
        r = requests.post(api, headers=h_upsert, json=payload, timeout=25)
        if r.status_code in (200, 201, 204):
            log(f"上传成功: {code_str}")
            return True
        log(f"POST HTTP {r.status_code}，改用 PATCH 更新")
        r2 = requests.patch(f"{api}?code_date=eq.{date_str}",
                            headers={"apikey": key, "Authorization": f"Bearer {key}",
                                     "Content-Type": "application/json",
                                     "Prefer": "return=minimal"},
                            json=payload[0], timeout=25)
        if r2.status_code in (200, 201, 204):
            log(f"更新成功: {code_str}")
            return True
        log(f"PATCH HTTP {r2.status_code}: {r2.text[:200]}")
    except Exception as e:
        log(f"上传异常: {type(e).__name__}: {e}")
    return False


def one_attempt(cfg):
    """完整走一遍：激活 -> 点击 -> 截图 -> OCR，返回 codes"""
    activate_wegame()
    time.sleep(2)
    if cfg.get("game_icon"):
        click(*cfg["game_icon"])
        time.sleep(int(cfg["wait_click"]))
    activate_wegame()
    time.sleep(1)
    if cfg.get("code_entry"):
        click(*cfg["code_entry"])
        time.sleep(int(cfg["wait_click"]) + int(cfg["wait_popup"]))
    screenshot(cfg.get("shot_region"))
    if not os.path.exists(SHOT_PATH):
        log("  无截图")
        return []
    words = ocr_words(SHOT_PATH)
    codes = extract_codes(words)
    log(f"  OCR 词数 {len(words)}，提取 {len(codes)}/6: {codes}")
    return codes


def main():
    log("=" * 50)
    cfg = load_json(os.path.join(BASE_DIR, "wegame_config.json"), dict(DEFAULT))
    date_str = bj_today()

    if not cfg.get("game_icon") or not cfg.get("code_entry"):
        log("坐标未校准，请先跑: python wegame_capture.py calibrate")
        sys.exit(2)

    ensure_wegame(cfg["wegame_exe"], int(cfg["wait_startup"]))

    codes = []
    for attempt in range(1, MAX_TRY + 1):
        log(f"第 {attempt}/{MAX_TRY} 次尝试")
        codes = one_attempt(cfg)
        if len(codes) >= 6:
            break
        if attempt < MAX_TRY:
            wait = 10 * attempt
            log(f"  不足 6 组，{wait} 秒后重试...")
            time.sleep(wait)

    if len(codes) < 6:
        log(f"三次尝试后仍只识别到 {len(codes)} 组，放弃上传（避免脏数据）")
        sys.exit(3)

    results = dict(zip(MAPS, codes[:6]))
    ok = upload(results, date_str)
    log("完成" if ok else "上传失败")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
