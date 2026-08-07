#!/usr/bin/env python3
"""
每日密码爬虫 - 最终版
✅ 用日期锁定当天视频（最精准）
✅ 多关键词兜底
✅ 用 SUPABASE_SERVICE_ROLE_KEY
"""

import os
import re
import signal
import requests
from datetime import date
from urllib.parse import quote

# ============ 超时保护 ============
signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(180)  # 3分钟够用

# ============ 配置 ============
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com"
}

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ============ HTTP 请求 ============
def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ⚠️ 请求失败: {e}")
        return ""

# ============ 搜索视频 ============
def search_videos(keyword, max_results=5):
    """搜索B站，返回多个视频URL（按热度排序）"""
    html = fetch(f"https://search.bilibili.com/all?keyword={quote(keyword)}")
    if not html:
        return []
    bvs = re.findall(r'/video/(BV\w+)', html)
    # 去重保序
    seen = set()
    unique = []
    for bv in bvs:
        if bv not in seen:
            seen.add(bv)
            unique.append(bv)
    return [f"https://www.bilibili.com/video/{bv}" for bv in unique[:max_results]]

# ============ 从视频页面提取密码 ============
def extract_password_from_page(html, today_str):
    """
    多种策略提取4位密码：
    1. 找 "密码: 1234" / "密码是1234" / "今日密码1234"
    2. 找 "今天/今日 ... 1234"
    """
    # 策略1: 显式标注
    patterns = [
        r'密码[是为:：\s]*(\d{4})',
        r'今日密码[是为:：\s]*(\d{4})',
        r'今天密码[是为:：\s]*(\d{4})',
        r'每日密码[是为:：\s]*(\d{4})',
    ]
    for p in patterns:
        m = re.search(p, html)
        if m:
            return m.group(1)

    # 策略2: "今天/今日"附近找4位数字
    m = re.search(r'(今天|今日).{0,30}?(\d{4})', html)
    if m:
        return m.group(2)

    return None

# ============ 写 Supabase ============
def write_to_supabase(code, today_str):
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL 未配置")
        return False
    if not SUPABASE_KEY:
        print("❌ SUPABASE_SERVICE_ROLE_KEY 未配置")
        return False

    url = f"{SUPABASE_URL}/rest/v1/daily_codes"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    data = [{
        "code_date": today_str,
        "code_value": code,
        "verified": True,
        "source": "bilibili"
    }]

    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code in (200, 201, 204):
            print(f"✅ 写入 Supabase 成功: {code}")
            return True
        else:
            print(f"⚠️ Supabase 返回 {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"⚠️ 写库异常: {e}")
        return False

# ============ 主流程 ============
def crawl():
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    mmdd = today.strftime("%m%d")

    print(f"🗓️ 采集 {today_str} 每日密码")
    print("─" * 50)

    # 多关键词兜底
    keywords = [
        f"三角洲行动{mmdd}密码",
        "三角洲行动 今日密码",
        "三角洲行动 每日密码",
    ]

    found_code = None

    for kw in keywords:
        print(f"\n🔍 搜索: {kw}")
        videos = search_videos(kw, max_results=5)

        if not videos:
            print("  ❌ 无搜索结果")
            continue

        print(f"  📹 找到 {len(videos)} 个视频")

        for i, url in enumerate(videos, 1):
            print(f"  [{i}] 检查: {url}")
            html = fetch(url)
            if not html:
                continue

            code = extract_password_from_page(html, today_str)
            if code:
                print(f"  ✅ 找到密码: {code}")
                found_code = code
                break  # 找到了就停

        if found_code:
            break  # 关键词也停

    # 结果处理
    print("\n" + "─" * 50)
    if found_code:
        ok = write_to_supabase(found_code, today_str)
        if ok:
            print(f"🎉 完成: 密码 {found_code} 已入库")
        else:
            print(f"⚠️ 爬到了但写库失败: {found_code}")
            print(f"👉 请在 Supabase 手动添加: {today_str} = {found_code}")
    else:
        print("❌ 所有关键词都没找到今日密码")
        print("👉 请在 Supabase 手动添加")

    signal.alarm(0)

if __name__ == "__main__":
    crawl()