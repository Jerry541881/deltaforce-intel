#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
截图 -> Windows OCR(带坐标) -> Y聚类取密码行 -> 按X排序 -> 校验 -> 补录 -> 上传
抗干扰：即使截图区域包含说明文字/图片，也能自动锁定密码那一行
"""
import os
import re
import sys
import tempfile
import subprocess
import upload_codes as uc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHOT_PATH = os.path.join(BASE_DIR, "last_code_shot.png")
MAPS = ["零号大坝", "长弓溪谷", "巴克什", "航天基地", "潮汐监狱", "AZ3"]

PS_OCR = r'''
param([string]$path)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging.BitmapDecoder,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new("en-US"))
if ($null -eq $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
foreach ($line in $result.Lines) {
    foreach ($w in $line.Words) {
        $b = $w.BoundingRect
        Write-Output ($w.Text + "|" + [int]$b.X + "|" + [int]$b.Y + "|" + [int]$b.Width + "|" + [int]$b.Height)
    }
}
'''


def run_ps(script, args=None, timeout=120):
    ps_path = os.path.join(tempfile.gettempdir(), "ocr_%d.ps1" % os.getpid())
    with open(ps_path, "w", encoding="utf-8-sig") as f:
        f.write(script)
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path]
    if args:
        cmd += args
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        raw = r.stdout or b""
        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return raw.decode("gbk", errors="ignore")
    except Exception as e:
        print(f"[PowerShell] 失败: {e}")
        return ""


def ocr_with_pos(path):
    """返回 [(text, x, y, w, h), ...]"""
    out = run_ps(PS_OCR, ["-path", path], timeout=120)
    items = []
    for line in out.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        p = line.split("|")
        if len(p) < 5:
            continue
        try:
            items.append((p[0], int(p[1]), int(p[2]), int(p[3]), int(p[4])))
        except ValueError:
            continue
    return items


def pick_digits(items):
    """从 OCR 结果里挑出候选数字：(x, y, code)
    规则：4位直接取；3位补前导零；1-2位忽略（避免 AZ3 的 '3' 被误当密码）
    """
    cands = []
    for text, x, y, w, h in items:
        t = text.strip()
        # 4 位连续数字（最高优先）
        for m in re.finditer(r"\d{4}(?!\d)", t):
            cands.append((x, y, m.group(1)))
            break
        else:
            # 纯数字 3 位 -> 补前导零（如 794 -> 0794）
            if re.fullmatch(r"\d{3}", t):
                cands.append((x, y, "0" + t))
            # 忽略 1-2 位（AZ3 的 3、年份碎片等）
    return cands


def cluster_by_row(cands, tol=25):
    """按 Y 坐标聚类，返回数字最多的一簇（容差 tol 像素）"""
    if not cands:
        return []
    groups = []
    for x, y, code in sorted(cands, key=lambda t: t[1]):
        placed = False
        for g in groups:
            if abs(y - g[0]) <= tol:
                g[1].append((x, code))
                placed = True
                break
        if not placed:
            groups.append([y, [(x, code)]])
    # 取成员最多的簇；并列时取 Y 最小（密码栏在最上方）
    groups.sort(key=lambda g: (-len(g[1]), g[0]))
    best = groups[0][1]
    best.sort(key=lambda t: t[0])  # 按 X 从左到右
    return [c for _, c in best]


def fallback_by_name(items):
    """兜底：用中文地图名匹配（需中文 OCR 包）"""
    full = " ".join(t[0] for t in items)
    marks = []
    for m in MAPS:
        idx = full.find(m)
        marks.append((idx if idx >= 0 else 10 ** 6, m))
    marks.sort()
    res = {}
    for i, (pos, name) in enumerate(marks):
        if pos >= 10 ** 6:
            continue
        end = marks[i + 1][0] if i + 1 < len(marks) and marks[i + 1][0] < 10 ** 6 else len(full)
        seg = full[pos:end]
        mm = re.search(r"(\d{4})(?!\d)", seg) or re.search(r"\b(\d{3})\b", seg)
        if mm:
            res[name] = mm.group(1).zfill(4)
    return res


def manual_input(missing):
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        for m in missing:
            v = simpledialog.askstring("补录密码", f"{m} 的4位密码：", parent=root)
            if v and re.fullmatch(r"\s*\d{1,4}\s*", v):
                yield m, v.strip().zfill(4)
        root.destroy()
    except Exception as e:
        print(f"[补录] 弹窗不可用: {e}")


def main():
    print("=" * 58)
    print("[1/4] 打开 WeGame 并截图")
    r = subprocess.run([sys.executable, os.path.join(BASE_DIR, "wegame_capture.py"), "capture"],
                       cwd=BASE_DIR, capture_output=True, timeout=300)
    try:
        print((r.stdout or b"").decode("utf-8", errors="ignore").strip())
    except Exception:
        pass
    if not os.path.exists(SHOT_PATH):
        print("[失败] 未生成截图")
        sys.exit(1)

    print("\n[2/4] OCR 识别（带坐标）")
    items = ocr_with_pos(SHOT_PATH)
    full = " ".join(t[0] for t in items)
    print("  ---- OCR 原文（前400字）----")
    print("  " + (full[:400] or "(空)"))
    print("  ---- 候选词+坐标（前25个）----")
    for t in items[:25]:
        print(f"    {t[0]!r} @ x={t[1]} y={t[2]}")
    print("  ------------------")

    cands = pick_digits(items)
    print(f"  候选数字: {[(c, y) for _, y, c in cands]}")
    codes = cluster_by_row(cands)
    print(f"  Y聚类后: {codes}")

    results = {}
    if len(codes) >= 6:
        results = dict(zip(MAPS, codes[:6]))
        print("  ✅ 按位置匹配成功")
    else:
        results = fallback_by_name(items)
        print(f"  中文名兜底: {len(results)}/6")

    print("\n[3/4] 补录缺失项")
    if len(results) < 6:
        missing = [m for m in MAPS if m not in results]
        print(f"  缺少: {missing}")
        for m, v in manual_input(missing):
            results[m] = v
    else:
        print("  六张齐全")

    print("\n[4/4] 校验并上传")
    errs = uc.validate(results)
    if errs:
        print("[拒绝上传] 数据不完整：")
        for e in errs:
            print(f"   - {e}")
        sys.exit(2)
    for m in MAPS:
        print(f"   {m}: {results[m]}")
    ok = uc.upload(results, uc.bj_today())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()