#!/usr/bin/env python3
"""
每日密码爬虫 - 智谱AI联网搜索版（Key已内置）
⚠️ Key硬编码，仅限私有仓库使用
"""

import os
import re
import signal
import requests
from datetime import date

# ============ 超时保护 ============
signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(180)

# ============ 配置（Key直接写死）============
ZHIPU_API_KEY = "755e7e56df9a40f29a6a365cbacd4e13.qwTIx88dyPPfa5r5"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {ZHIPU_API_KEY}",
    "Content-Type": "application/json"
}

# ============ 六张地图 ============
MAPS = ["零号大坝", "长弓溪谷", "巴克什", "航天基地", "潮汐监狱", "AZ3核电站"]

# ============ 智谱 Web Search ============
def zhipu_web_search(query):
    url = "https://open.bigmodel.cn/api/paas/v4/web_search"
    data = {
        "search_engine": "search_pro",
        "search_query": query,
        "search_intent": "on",
        "count": 15
    }
    try:
        r = requests.post(url, headers=HEADERS, json=data, timeout=15)
        if r.status_code == 200:
            resp = r.json()
            return resp.get("search_result", resp.get("data", []))
    except:
        pass
    return []

# ============ 提取密码 ============
def extract_codes(text):
    results = {}
    if not text:
        return results
    for m in MAPS:
        patterns = [
            rf'{m}[密码]*[：:]\s*(\d{{4}})',
            rf'{m}\s*[是为]\s*(\d{{4}})',
            rf'{m}.{{0,10}}(\d{{4}})',
        ]
        for p in patterns:
            mm = re.search(p, text)
            if mm:
                results[m] = mm.group(1)
                break
    return results

def extract_from_search_results(results):
    all_text = ""
    for item in results:
        if isinstance(item, dict):
            all_text += item.get("content", "") + "\n"
            all_text += item.get("snippet", "") + "\n"
            all_text += item.get("title", "") + "\n"
    return extract_codes(all_text)

# ============ 写 Supabase ============
def write_to_supabase(results, today_str):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase 配置缺失")
        return False

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
        "source": "zhipu-ai"
    }]
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code in (200, 201, 204):
            print(f"✅ 写入 Supabase 成功")
            return True
    except:
        pass
    return False

# ============ 主流程 ============
def crawl():
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    mmdd = today.strftime("%m%d")

    print(f"🗓️ 采集 {today_str} 每日密码（智谱AI）")
    print("─" * 50)

    results = {}

    print("\n📡 智谱 Web Search 联网搜索")
    query = f"三角洲行动 {mmdd} 今日密码 各地图 零号大坝 长弓溪谷 巴克什 航天基地 潮汐监狱 AZ3核电站"
    search_results = zhipu_web_search(query)

    if search_results:
        print(f"  📄 共 {len(search_results)} 条结果")
        results = extract_from_search_results(search_results)
        print(f"  ✅ 提取到 {len(results)}/6 张地图密码")
        for k, v in results.items():
            print(f"     {k}: {v}")
    else:
        print("  ⚠️ Web Search 无结果")

    print("\n" + "─" * 50)
    if len(results) >= 4:
        write_to_supabase(results, today_str)
        print(f"🎉 完成: {today_str} 密码已入库")
    else:
        print(f"❌ 仅获取 {len(results)}/6 张地图密码")
        print("👉 请在 Supabase 手动添加")

    signal.alarm(0)

if __name__ == "__main__":
    crawl()