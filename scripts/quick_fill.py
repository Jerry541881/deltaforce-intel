#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
半自动填码：截图 -> 打开截图 -> 六格一次填完 -> 上传
OCR 不可用时的兜底方案，每天约 20 秒
"""
import os
import re
import sys
import subprocess
import upload_codes as uc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHOT_PATH = os.path.join(BASE_DIR, "last_code_shot.png")
MAPS = ["零号大坝", "长弓溪谷", "巴克什", "航天基地", "潮汐监狱", "AZ3"]


def grab_shot():
    """调 wegame_capture 截图（auto 模式，弹窗已能自动打开）"""
    print("[1/3] 打开 WeGame 密码弹窗并截图...")
    r = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "wegame_capture.py"), "auto"],
        cwd=BASE_DIR, capture_output=True, timeout=300
    )
    try:
        print((r.stdout or b"").decode("utf-8", errors="ignore").strip())
    except Exception:
        pass
    return os.path.exists(SHOT_PATH)


def show_shot():
    """用系统默认看图工具打开截图"""
    if os.path.exists(SHOT_PATH):
        try:
            os.startfile(SHOT_PATH)
            print("[2/3] 已打开截图，请照着图填下面六格")
        except Exception:
            print(f"[2/3] 请手动打开: {SHOT_PATH}")
    else:
        print("[2/3] 截图不存在，请直接看游戏界面填")


def ask_gui():
    """一个窗口六格输入，回车即提交"""
    import tkinter as tk
    from tkinter import messagebox

    result = {}
    root = tk.Tk()
    root.title("今日密码录入")
    root.geometry("380x340")
    root.attributes("-topmost", True)

    tk.Label(root, text="照着截图填六组4位密码，然后点【上传】",
             font=("Microsoft YaHei", 10)).pack(pady=10)

    frame = tk.Frame(root)
    frame.pack(padx=20)

    entries = {}
    for i, m in enumerate(MAPS):
        tk.Label(frame, text=m, font=("Microsoft YaHei", 10), width=10, anchor="w").grid(row=i, column=0, pady=4)
        e = tk.Entry(frame, font=("Consolas", 14), width=8, justify="center")
        e.grid(row=i, column=1, pady=4)
        entries[m] = e
        if i == 0:
            e.focus()

    def on_submit(event=None):
        ok = True
        for m in MAPS:
            v = entries[m].get().strip()
            if not re.fullmatch(r"\d{1,4}", v):
                entries[m].config(bg="#ffcccc")
                ok = False
            else:
                entries[m].config(bg="white")
                result[m] = v.zfill(4)
        if not ok:
            messagebox.showwarning("格式错误", "每组必须是 1-4 位数字")
            return
        root.quit()

    def on_cancel():
        root.destroy()
        sys.exit(1)

    entries[MAPS[-1]].bind("<Return>", on_submit)

    btn = tk.Frame(root)
    btn.pack(pady=12)
    tk.Button(btn, text="上传", command=on_submit, width=10,
              bg="#4CAF50", fg="white", font=("Microsoft YaHei", 10)).pack(side="left", padx=8)
    tk.Button(btn, text="取消", command=on_cancel, width=10,
              font=("Microsoft YaHei", 10)).pack(side="left", padx=8)

    root.mainloop()
    try:
        root.destroy()
    except Exception:
        pass
    return result


def main():
    print("=" * 55)
    grab_shot()
    show_shot()
    codes = ask_gui()

    print("\n[3/3] 校验并上传")
    errs = uc.validate(codes)
    if errs:
        print("[拒绝] 数据不完整：")
        for e in errs:
            print("   -", e)
        sys.exit(2)

    for m in MAPS:
        print(f"   {m}: {codes[m]}")
    ok = uc.upload(codes, uc.bj_today())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()