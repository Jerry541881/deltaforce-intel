#!/usr/bin/env python3
"""
每日密码爬虫 - 必应/18183版（最稳）
✅ 直接抓 18183 三角洲每日密码工具页
✅ 多源兜底：18183 → 3DM → 必应搜索
✅ 用 SUPABASE_SERVICE_ROLE_KEY
"""

import os
import re
import json
import signal
import requests
from datetime import date
from urllib.parse import quote

# ============ 超时保护 ============
signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(180)

# ============ 配置 ============
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.18183.com/"
}

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ============ 六张地图 ============
MAPS = [
    "零号大坝",
    "长弓溪谷",
    "巴克什",
    "航天基地",
    "潮汐监狱",
    "AZ3核电站",
]

# ============ HTTP 请求 ============
def fetch(url, encoding="utf-8"):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        r.encoding = encoding
        return r.text
    except Exception as e:
        print(f"  ⚠️ 请求失败: {e}")
        return ""

# ============ 来源1: 18183 工具页 ============
def crawl_18183():
    """从 18183 三角洲每日密码工具页提取"""
    html = fetch("https://db.18183.com/sjzmm/")
    if not html:
        return None

    results = {}
    # 18183 通常格式: "零号大坝密码:9514" 或 "零号大坝：9514"
    for m in MAPS:
        # 多种写法兼容
        patterns = [
            rf'{m}[密码]*[：:]\s*(\d{{4}})',
            rf'{m}\s*[密码]*\s*[是为]\s*(\d{{4}})',
        ]
        for p in patterns:
            mm = re.search(p, html)
            if mm:
                results[m] = mm.group(1)
                break

    return results if len(results) >= 4 else None

# ============ 来源2: 3DM ============
def crawl_3dm(today_str):
    """从 3DM 攻略站提取"""
    y, m, d = today_str.split("-")
    url = f"https://m.3dmgame.com/ol/gl/{y}{m}{d}.html"
    html = fetch(url)
    if not html:
        return None

    results = {}
    for mp in MAPS:
        p = rf'{mp}.*?[密码]*[：:]\s*(\d{{4}})'
        mm = re.search(p, html)
        if mm:
            results[mp] = mm.group(1)
    return results if results else None

# ============ 来源3: 必应搜索兜底 ============
def crawl_bing(today_str):
    """必应搜索，找今日密码文章"""
    mmdd = today_str.replace("-", "")[4:]  # 0807
    kw = f"三角洲行动{mmdd}密码"
    search_url = f"https://cn.bing.com/search?q={quote(kw)}"
    html = fetch(search_url)
    if not html:
        return None

    # 在搜索结果摘要里找 "零号大坝:9514" 模式
    results = {}
    for mp in MAPS:
        p = rf'{mp}.*?(\d{{4}})'
        mm = re.search(p, html)
        if mm:
            results[mp] = mm.group(1)
    return results if results else None

# ============ 写 Supabase ============
def write_to_supabase(results, today_str):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase 配置缺失")
        print(f"   请在 GitHub Settings → Secrets 配置")
        print(f"   或在 Supabase 手动添加: {today_str} = {results}")
        return False

    # 把 6 张地图密码拼成一个字符串存 daily_codes
    # 格式: "零号大坝:9514|长弓溪谷:4654|..."
    code_str = "|".join([f"{k}:{v}" for k, v in results.items()])

    url = f"{SUPABASE_URL}/rest/v1/daily_codes"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    data = [{
        "code_date": today_str,
        "code_value": code_str,
        "verified": True,
        "source": "18183"
    }]

    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code in (200, 201, 204):
            print(f"✅ 写入 Supabase 成功")
            return True
        else:
            print(f"⚠️ Supabase 返回 {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"⚠️ 写库异常: {e}")
        return False

# ============ 主流程 ============
def crawl():
    today = date.today().strftime("%Y-%m-%d")
    print(f"🗓️ 采集 {today} 每日密码（多源爬虫）")
    print("─" * 55)

    results = None
    sources = [
        ("18183工具页", crawl_18183),
        ("3DM攻略站",  lambda: crawl_3dm(today)),
        ("必应搜索",   lambda: crawl_bing(today)),
    ]

    for name, func in sources:
        print(f"\n📡 尝试: {name}")
        try:
            results = func()
        except Exception as e:
            print(f"  ⚠️ 异常: {e}")
            results = None

        if results and len(results) >= 4:
            print(f"  ✅ 成功获取 {len(results)}/6 张地图密码")
            for k, v in results.items():
                print(f"     {k}: {v}")
            break
        else:
            got = len(results) if results else 0
            print(f"  ⚠️ 仅获取 {got}/6，换下一个源")

    # 结果处理
    print("\n" + "─" * 55)
    if results and len(results) >= 4:
        ok = write_to_supabase(results, today)
        if ok:
            print(f"🎉 完成: {today} 密码已入库")
        else:
            print(f"⚠️ 爬到了但写库失败，请手动添加:")
            for k, v in results.items():
                print(f"   {k}: {v}")
    else:
        print("❌ 所有来源都没找到今日密码")
        print("👉 请在 Supabase 手动添加")
        print("   参考: 零号大坝:9514 长弓溪谷:4654 ...")

    signal.alarm(0)

if __name__ == "__main__":
    crawl()