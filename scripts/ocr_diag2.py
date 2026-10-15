#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 诊断 v2
- 强制 PowerShell UTF-8 输出，解决中文报错乱码
- 打印异常类型 / HResult / Message（ASCII 优先，不再乱码）
- 测试两条加载路径：A=StorageFile  B=MemoryStream.AsRandomAccessStream（备用）
"""
import os, sys, tempfile, subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHOT = os.path.join(BASE_DIR, "last_code_shot.png")

PRELUDE = r'''
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
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
[Windows.Storage.Streams.RandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
'''


def run_ps(body, timeout=180):
    script = PRELUDE + "\n" + body
    ps_path = os.path.join(tempfile.gettempdir(), "diag2.ps1")
    with open(ps_path, "w", encoding="utf-8-sig") as f:
        f.write(script)
    r = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path],
        capture_output=True, timeout=timeout
    )
    out = (r.stdout or b"").decode("utf-8", errors="ignore")
    err = (r.stderr or b"").decode("utf-8", errors="ignore")
    return out, err, r.returncode


def show(tag, out, err, rc):
    print(f"  ---- {tag} stdout ----")
    print(out.strip() or "  (空)")
    if err.strip():
        print(f"  ---- {tag} stderr ----")
        print(err.strip())
    print(f"  ---- exit code: {rc} ----")


print("=" * 62)
print("[1] 截图文件")
if os.path.exists(SHOT):
    print(f"    存在 {os.path.getsize(SHOT)} 字节 -> {SHOT}")
else:
    print(f"    X 不存在 -> {SHOT}")

path_esc = SHOT.replace("\\", "\\\\")

print("\n[2] 路径 A：StorageFile.GetFileFromPathAsync")
body_a = f'''
try {{
    Write-Output "A-step1 打开文件"
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync("{path_esc}")) ([Windows.Storage.StorageFile])
    Write-Output "A-step2 打开流"
    $stream = Await ($file.OpenAsync([Windows.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    Write-Output "A-step3 解码"
    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    Write-Output "A-step4 位图"
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    Write-Output ("A-OK 位图 " + $bitmap.PixelWidth + "x" + $bitmap.PixelHeight)
}} catch {{
    Write-Output ("A-FAIL 类型=" + $_.Exception.GetType().FullName)
    Write-Output ("A-FAIL HResult=" + $_.Exception.HResult)
    Write-Output ("A-FAIL Message=" + $_.Exception.Message)
    if ($_.Exception.InnerException) {{
        Write-Output ("A-FAIL Inner=" + $_.Exception.InnerException.Message)
    }}
}}
'''
out, err, rc = run_ps(body_a)
show("A", out, err, rc)

print("\n[3] 路径 B：MemoryStream.AsRandomAccessStream（备用）")
body_b = f'''
try {{
    Write-Output "B-step1 读字节"
    $bytes = [System.IO.File]::ReadAllBytes("{path_esc}")
    Write-Output ("B-step2 字节数=" + $bytes.Length)
    $ms = New-Object System.IO.MemoryStream
    $ms.Write($bytes, 0, $bytes.Length)
    $ms.Position = 0
    $stream = $ms.AsRandomAccessStream()
    Write-Output "B-step3 解码"
    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    Write-Output ("B-OK 位图 " + $bitmap.PixelWidth + "x" + $bitmap.PixelHeight)
    Write-Output "B-step4 识别"
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new("en-US"))
    if ($null -eq $engine) {{ $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }}
    Write-Output ("B-引擎=" + $engine.RecognizerLanguage.LanguageTag)
    $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
    Write-Output ("B-识别完成 行数=" + $result.Lines.Count)
    foreach ($line in $result.Lines) {{
        foreach ($w in $line.Words) {{
            $b = $w.BoundingRect
            Write-Output ("  W " + $w.Text + "|" + [int]$b.X + "|" + [int]$b.Y)
        }}
    }}
}} catch {{
    Write-Output ("B-FAIL 类型=" + $_.Exception.GetType().FullName)
    Write-Output ("B-FAIL HResult=" + $_.Exception.HResult)
    Write-Output ("B-FAIL Message=" + $_.Exception.Message)
    if ($_.Exception.InnerException) {{
        Write-Output ("B-FAIL Inner=" + $_.Exception.InnerException.Message)
    }}
}}
'''
out, err, rc = run_ps(body_b, timeout=200)
show("B", out, err, rc)

print("\n" + "=" * 62)
print("把上面 A-FAIL / B-FAIL 的 Message 和 HResult 发我")
