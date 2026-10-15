#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三种模式:
  calibrate  校准坐标（只框密码栏）
  auto       自动点击打开密码弹窗并截图（会先激活窗口）
  manual     手动点开密码弹窗，倒计时自动截图（最稳）
"""
import os
import sys
import json
import time
import tempfile
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "wegame_config.json")
SHOT_PATH = os.path.join(BASE_DIR, "last_code_shot.png")

DEFAULT_CONFIG = {
    "wegame_exe": r"D:\Program Files (x86)\WeGame\wegame.exe",
    "game_icon": None,
    "code_entry": None,
    "shot_region": None,
    "wait_startup": 40,
    "wait_click": 6
}


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, shell=True, timeout=timeout)
        out = b""
        for raw in (r.stdout, r.stderr):
            if raw:
                out += raw
        try:
            return out.decode("utf-8")
        except UnicodeDecodeError:
            return out.decode("gbk", errors="ignore")
    except Exception:
        return ""


def run_ps(script, timeout=120):
    ps_path = os.path.join(tempfile.gettempdir(), "wg_%d.ps1" % os.getpid())
    with open(ps_path, "w", encoding="utf-8-sig") as f:
        f.write(script)
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path],
            capture_output=True, timeout=timeout
        )
        raw = r.stdout or b""
        try:
            return raw.decode("utf-8", errors="ignore").strip()
        except Exception:
            return raw.decode("gbk", errors="ignore").strip()
    except Exception as e:
        print(f"[PowerShell] 失败: {e}")
        return ""


def activate_wegame():
    """把 WeGame 窗口拉到前台并激活"""
    script = r'''
Add-Type -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr hWnd);
[DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr hWnd, int nCmdShow);
[DllImport("user32.dll")] public static extern bool IsIconic(System.IntPtr hWnd);
'@ -Name W -Namespace Native

$procs = Get-Process -Name wegame -ErrorAction SilentlyContinue
if (-not $procs) { Write-Output "notfound"; exit }
$h = 0
foreach ($p in $procs) {
    if ($p.MainWindowHandle -ne 0) { $h = $p.MainWindowHandle; break }
}
if ($h -eq 0) { Write-Output "nohwnd"; exit }
if ([Native.W]::IsIconic($h)) { [Native.W]::ShowWindow($h, 9) | Out-Null }
Start-Sleep -Milliseconds 500
[Native.W]::ShowWindow($h, 9) | Out-Null
Start-Sleep -Milliseconds 300
$ok = [Native.W]::SetForegroundWindow($h)
if ($ok) { Write-Output "activated" } else { Write-Output "failed" }
'''
    out = run_ps(script, timeout=40)
    print(f"[窗口] 激活结果: {out or '(无输出)'}")
    return "activated" in out


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"[配置] 已保存到 {CONFIG_PATH}")


def click(x, y):
    run_ps(f'''
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({int(x)}, {int(y)})
Add-Type -MemberDefinition '[DllImport("user32.dll")] public static extern void mouse_event(int flags, int dx, int dy, int cButtons, int extraInfo);' -Name U -Namespace W
Start-Sleep -Milliseconds 300
[W.U]::mouse_event(0x00000002, 0, 0, 0, 0)
Start-Sleep -Milliseconds 120
[W.U]::mouse_event(0x00000004, 0, 0, 0, 0)
Start-Sleep -Milliseconds 200
[W.U]::mouse_event(0x00000002, 0, 0, 0, 0)
Start-Sleep -Milliseconds 120
[W.U]::mouse_event(0x00000004, 0, 0, 0, 0)
''', timeout=40)


def get_mouse_pos():
    out = run_ps('''
Add-Type -AssemblyName System.Windows.Forms
$p = [System.Windows.Forms.Cursor]::Position
Write-Output "$($p.X),$($p.Y)"
''', timeout=30)
    try:
        a, b = out.split(",")[0], out.split(",")[1]
        return [int(a.strip()), int(b.strip())]
    except Exception:
        print(f"[警告] 读坐标失败: {out!r}")
        return None


def screenshot(save_path, region=None):
    if region and len(region) == 4:
        x, y, w, h = [int(v) for v in region]
        script = f'''
Add-Type -AssemblyName System.Drawing
$b = New-Object System.Drawing.Bitmap({w}, {h})
$g = [System.Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen({x}, {y}, 0, 0, $b.Size)
$b.Save("{save_path}")
Write-Output "region {w}x{h}"
'''
    else:
        script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$s = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$b = New-Object System.Drawing.Bitmap($s.Width, $s.Height)
$g = [System.Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen($s.Location, [System.Drawing.Point]::Empty, $s.Size)
$b.Save("{save_path}")
Write-Output "fullscreen"
'''
    print(f"[截图] {run_ps(script, timeout=60)}")
    return save_path


def ensure_wegame(exe, wait):
    out = run_cmd("tasklist")
    if "wegame.exe" in out.lower():
        print("[WeGame] 已在运行")
        return True
    if not os.path.exists(exe):
        print(f"[错误] 找不到: {exe}")
        return False
    print(f"[WeGame] 启动中...")
    subprocess.Popen([exe], shell=False)
    for i in range(wait):
        time.sleep(1)
        if "wegame.exe" in run_cmd("tasklist").lower():
            print(f"[WeGame] 已启动（{i+1}秒）")
            time.sleep(12)
            return True
    print("[警告] 启动超时")
    return True


def ask_pos(tip, seconds=7):
    print(f"\n>>> {tip}")
    for s in range(seconds, 0, -1):
        print(f"    {s} 秒后记录，移动鼠标到目标...   ", end="\r")
        time.sleep(1)
    pos = get_mouse_pos()
    print(f"\n    已记录: {pos}")
    return pos


def calibrate():
    cfg = load_config()
    print("=" * 58)
    print("校准：鼠标移到指定位置，倒计时自动记录")
    print("=" * 58)
    ensure_wegame(cfg["wegame_exe"], cfg["wait_startup"])
    activate_wegame()
    time.sleep(2)

    cfg["game_icon"] = ask_pos("1/3 移到【我的游戏 → 三角洲行动】图标")
    if cfg["game_icon"]:
        click(*cfg["game_icon"])
        time.sleep(cfg["wait_click"])
    activate_wegame()

    cfg["code_entry"] = ask_pos("2/3 移到【右侧栏 → 每日密码】入口")
    if cfg["code_entry"]:
        click(*cfg["code_entry"])
        time.sleep(cfg["wait_click"])
    activate_wegame()

    print("\n3/3 密码弹窗应该已打开")
    print("     框选【顶部密码栏】—— 只框六个地图名+数字那一行！")
    lt = ask_pos("     密码栏 左上角")
    rb = ask_pos("     密码栏 右下角")
    if lt and rb:
        cfg["shot_region"] = [lt[0], lt[1], max(rb[0]-lt[0], 100), max(rb[1]-lt[1], 40)]
        print(f"     区域: {cfg['shot_region']}  (宽{cfg['shot_region'][2]} 高{cfg['shot_region'][3]})")
    save_config(cfg)
    screenshot(SHOT_PATH, cfg.get("shot_region"))
    print(f"\n[完成] {SHOT_PATH} —— 打开确认只看到六个密码")


def capture_auto():
    cfg = load_config()
    if not cfg.get("game_icon") or not cfg.get("code_entry"):
        print("[错误] 未校准，先跑: python wegame_capture.py calibrate")
        sys.exit(2)
    ensure_wegame(cfg["wegame_exe"], cfg["wait_startup"])
    activate_wegame()
    time.sleep(2)
    click(*cfg["game_icon"])
    time.sleep(cfg["wait_click"])
    activate_wegame()
    click(*cfg["code_entry"])
    time.sleep(cfg["wait_click"] + 2)
    screenshot(SHOT_PATH, cfg.get("shot_region"))
    print(f"[截图] {SHOT_PATH}")


def capture_manual(wait=15):
    """手动模式：用户自己点开弹窗，倒计时截图"""
    cfg = load_config()
    print("=" * 58)
    print("请【手动】打开 WeGame → 三角洲行动 → 每日密码弹窗")
    print(f"然后把手移开鼠标，{wait} 秒后自动截图")
    print("=" * 58)
    for s in range(wait, 0, -1):
        print(f"    {s} 秒后截图...   ", end="\r")
        time.sleep(1)
    print()
    screenshot(SHOT_PATH, cfg.get("shot_region"))
    print(f"[截图] {SHOT_PATH}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "auto"
    if mode == "calibrate":
        calibrate()
    elif mode == "manual":
        w = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        capture_manual(w)
    else:
        capture_auto()