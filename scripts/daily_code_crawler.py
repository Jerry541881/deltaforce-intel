#!/usr/bin/env python3
"""
每日密码爬虫 - 防超时版
策略：UP 主当日优先 → 3DM 兜底 → 管理员手动兜底
"""

import os
import re
import json
import signal
import requests
from datetime import date
from urllib.parse import quote

# ============ 超时保护（2.5 分钟强制退出）============
def timeout_handler(signum, frame):
    print("⏰ 爬虫超时，强制退出")
    os._exit(0)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(150)  # 150 秒

# ============ 配置 ============
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com"
}

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

CODE_RE = re.compile(r'\b\d{4}\b')

# 单个请求 8 秒超时
def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"⚠️ 请求失败: {url[:50]} -> {e}")
        return ""

# ============ B站：今日密码 ============
def crawl_bilibili_today(today_str):
    keyword = quote("三角洲行动今日密码")
    html = fetch(f"https://search.bilibili.com/all?keyword={keyword}")
    if not html:
        return None

    # 找 "今天/今日" 附近的 4 位数字
    pattern = rf'(今天|今日).{{0,15}}?(\d{{4}})'
    m = re.search(pattern, html)
    if m:
        code = m.group(2)
        print(f"[B站] ✅ 找到今日密码: {code}")
        return {
            "code_date": today_str,
            "code_value": code,
            "verified": True,
            "source": "bilibili"
        }
    return None

# ============ 3DM 兜底 ============
def crawl_3dm(today_str):
    # ★ 你后面确认一个长期有效的 URL 替换这里
    url = "https://www.3dmgame.com/gl/3824721.html"
    html = fetch(url)
    if not html:
        return None

    if today_str not in html:
        print("[3DM] ⚠️ 页面不含今日日期")
        return None

    codes = CODE_RE.findall(html)
    if codes:
        code = codes[0]
        print(f"[3DM] ✅ 找到今日密码: {code}")
        return {
            "code_date": today_str,
            "code_value": code,
            "verified": True,
            "source": "3dm"
        }
    return None

# ============ 写 Supabase ============
def write_to_supabase(data):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase 环境变量未配置，跳过写库")
        print(f"   数据: {json.dumps(data, ensure_ascii=False)}")
        return False

    url = f"{SUPABASE_URL}/rest/v1/daily_codes"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    try:
        r = requests.post(url, headers=headers, json=[data], timeout=10)
        if r.status_code in (200, 201, 204):
            print(f"✅ 写入 Supabase 成功: {data['code_value']}")
            return True
        else:
            print(f"⚠️ Supabase 返回: {r.status_code} {r.text[:100]}")
            return False
    except Exception as e:
        print(f"⚠️ 写库失败: {e}")
        return False

# ============ 主流程 ============
def crawl():
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    print(f"🗓️ 采集 {today_str} 每日密码")
    print("─" * 40)

    # Step 1: B站
    result = crawl_bilibili_today(today_str)

    # Step 2: 3DM 兜底
    if not result:
        print("[Step 2] B站未找到，尝试 3DM...")
        result = crawl_3dm(today_str)

    # Step 3: 写库 或 留空
    if result:
        write_to_supabase(result)
        print("\n🎉 今日密码已更新")
    else:
        print("\n❌ 今日密码未找到")
        print("👉 等待管理员手动添加")

    print("─" * 40)
    signal.alarm(0)  # 取消超时

if __name__ == "__main__":
    crawl()