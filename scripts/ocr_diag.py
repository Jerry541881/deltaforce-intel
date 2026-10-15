#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR 诊断：把 PowerShell 的 stdout + stderr 全部打印出来"""
import os, sys, tempfile, subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHOT = os.path.join(BASE_DIR, "last_code_shot.png")


def run_ps(script, timeout=120):
    ps_path = os.path.join(tempfile.gettempdir(), "diag.ps1")
    with open(ps_path, "w", encoding="utf-8-sig") as f:
        f.write(script)
    r = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path],
        capture_output=True, timeout=timeout
    )
    def dec(b):
        try:
            return b.decode("utf-8", errors="ignore")
        except Exception:
            return b.decode("gbk", errors="ignore")
    return dec(r.stdout or b""), dec(r.stderr or b""), r.returncode


print("=" * 60)
print("[1] 检查截图文件")
if os.path.exists(SHOT):
    size = os.path.getsize(SHOT)
    print(f"    存在: {SHOT}")
    print(f"    大小: {size} 字节  {'⚠️ 太小，可能没截到东西' if size < 5000 else ''}")
else:
    print(f"    ❌ 不存在: {SHOT}")

print("\n[2] 测试 OCR 引擎能否创建")
s1 = r'''
$ErrorActionPreference = "Continue"
try {
    [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
    Write-Output "OK: OcrEngine 类型加载成功"
    $langs = [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages
    Write-Output ("可用语言: " + (($langs | ForEach-Object { $_.LanguageTag }) -join ", "))
    $eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new("en-US"))
    if ($null -eq $eng) {
        Write-Output "WARN: en-US 引擎创建失败，尝试用户首选语言"
        $eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    }
    if ($null -eq $eng) { Write-Output "FAIL: 引擎创建失败" } else { Write-Output ("OK: 引擎就绪 -> " + $eng.RecognizerLanguage.LanguageTag) }
} catch {
    Write-Output ("EXCEPTION: " + $_.Exception.Message)
}
'''
out, err, rc = run_ps(s1)
print("  ---- stdout ----")
print(out.strip() or "  (空)")
print("  ---- stderr ----")
print(err.strip() or "  (空)")
print(f"  ---- exit code: {rc} ----")

print("\n[3] 实际识别测试")
s2 = '''
$ErrorActionPreference = "Continue"
$path = "%s"
try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
    if ($null -eq $asTaskGeneric) { Write-Output "FAIL: 找不到 AsTask 泛型方法"; exit }
    Function Await($WinRtTask, $ResultType) {
        $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
        $netTask = $asTask.Invoke($null, @($WinRtTask))
        $netTask.Wait(-1) | Out-Null
        $netTask.Result
    }
    [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
    [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging.BitmapDecoder,ContentType=WindowsRuntime] | Out-Null
    [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null

    Write-Output "step1: 打开文件"
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
    Write-Output "step2: 打开流"
    $stream = Await ($file.OpenAsync([Windows.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    Write-Output "step3: 创建解码器"
    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    Write-Output "step4: 取位图"
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    Write-Output ("step5: 位图 " + $bitmap.PixelWidth + "x" + $bitmap.PixelHeight)
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new("en-US"))
    if ($null -eq $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
    Write-Output "step6: 开始识别"
    $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
    Write-Output ("step7: 识别完成，行数=" + $result.Lines.Count)
    foreach ($line in $result.Lines) { Write-Output ("  LINE: " + $line.Text) }
} catch {
    Write-Output ("EXCEPTION: " + $_.Exception.Message)
    Write-Output ("STACK: " + $_.ScriptStackTrace)
}
''' % SHOT.replace("\\", "\\\\")
out, err, rc = run_ps(s2, timeout=150)
print("  ---- stdout ----")
print(out.strip() or "  (空)")
print("  ---- stderr ----")
print(err.strip() or "  (空)")
print(f"  ---- exit code: {rc} ----")
print("\n" + "=" * 60)