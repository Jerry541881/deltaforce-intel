#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 终极修复：
  1) GetAwaiter().GetResult() 替代 Wait(-1)，吐出真实错误
  2) powershell -MTA 多线程公寓运行（WinRT 异步必需）
  3) InMemoryRandomAccessStream + DataWriter 替代有 bug 的 MemoryStream
  4) 自动尝试 zh-Hans-CN / en-US / 用户首选语言
"""
import os
import sys
import tempfile
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHOT = os.path.join(BASE_DIR, "last_code_shot.png")

PS = r'''
param([string]$path)
$ErrorActionPreference = "Continue"
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]

if ($null -eq $asTaskGeneric) { Write-Output "FATAL|no AsTask method"; exit }

Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    return $netTask.GetAwaiter().GetResult()
}

try {
    [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
    [Windows.Storage.Streams.InMemoryRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
    [Windows.Storage.Streams.DataWriter,Windows.Storage.Streams,ContentType=WindowsRuntime] | Out-Null
    [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging.BitmapDecoder,ContentType=WindowsRuntime] | Out-Null
    [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
    [Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime] | Out-Null
    Write-Output "T1|types loaded OK"

    $bytes = [System.IO.File]::ReadAllBytes($path)
    Write-Output ("T2|bytes=" + $bytes.Length)

    $stream = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $writer = New-Object Windows.Storage.Streams.DataWriter($stream)
    $writer.WriteBytes($bytes)
    $null = Await ($writer.StoreAsync()) ([uint32])
    Write-Output "T3|bytes -> stream OK"
    $null = $writer.DetachStream()
    $null = $stream.Seek(0)

    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    Write-Output "T4|decoder OK"
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    Write-Output ("T5|bitmap " + $bitmap.PixelWidth + "x" + $bitmap.PixelHeight)

    $engine = $null
    foreach ($tag in @("zh-Hans-CN","en-US")) {
        try { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new($tag)) } catch {}
        if ($null -ne $engine) { break }
    }
    if ($null -eq $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
    if ($null -eq $engine) { Write-Output "FATAL|no OCR engine"; exit }
    Write-Output ("T6|engine=" + $engine.RecognizerLanguage.LanguageTag)

    $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
    Write-Output ("T7|lines=" + $result.Lines.Count)
    foreach ($line in $result.Lines) {
        foreach ($w in $line.Words) {
            $b = $w.BoundingRect
            Write-Output ("W|" + $w.Text + "|" + [int]$b.X + "|" + [int]$b.Y + "|" + [int]$b.Width + "|" + [int]$b.Height)
        }
    }
    Write-Output "OCR_OK"
} catch {
    Write-Output ("EX|" + $_.Exception.GetType().FullName)
    Write-Output ("MSG|" + $_.Exception.Message)
    if ($_.Exception.InnerException) { Write-Output ("INNER|" + $_.Exception.InnerException.Message) }
}
'''


def dec(raw):
    if not raw:
        return ""
    try:
        s = raw.decode("utf-8", errors="ignore")
    except Exception:
        s = ""
    if "\ufffd" in s:
        try:
            s = raw.decode("gbk", errors="ignore")
        except Exception:
            pass
    return s


def run(extra_flags, tag):
    ps_path = os.path.join(tempfile.gettempdir(), "ocrfix.ps1")
    with open(ps_path, "w", encoding="utf-8-sig") as f:
        f.write(PS)
    cmd = ["powershell.exe"] + extra_flags + [
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path, "-path", SHOT
    ]
    print("=" * 60)
    print(f"[{tag}] powershell.exe {' '.join(extra_flags)}")
    print("=" * 60)
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=180)
        out = dec(r.stdout) + ("\n[stderr]\n" + dec(r.stderr) if r.stderr else "")
        print(out.strip() or "(无输出)")
    except Exception as e:
        print("执行异常:", e)
    print()


def main():
    if not os.path.exists(SHOT):
        print("截图不存在:", SHOT)
        sys.exit(1)
    print("目标:", SHOT, os.path.getsize(SHOT), "字节\n")
    run(["-MTA"], "MTA")
    run([], "默认(STA)")


if __name__ == "__main__":
    main()