#!/usr/bin/env python3
"""
每日密码爬虫 - 智谱AI（Key内置 + 多参数容错）
"""

import os
import re
import signal
import requests
from datetime import date

signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(150)

ZHIPU_API_KEY = "a00b1314dd0a44c2bc522ac456bd6a22.GeFEMhnVCNQNJoju"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {ZHIPU_API_KEY}",
    "Content-Type": "application/json"
}

MAPS = ["零号大坝", "长弓溪谷", "巴克什", "航天基地", "潮汐监狱", "AZ3核电站"]


def zhipu_web_search(query):
    url = "https://open.bigmodel.cn/api/paas/v4/web_search"

    combos = [
        ("search-pro + intent=true", {"search_engine": "search-pro", "search_query": query, "search_intent": True, "count": 15}),
        ("search_pro + intent=true", {"search_engine": "search_pro", "search_query": query, "search_intent": True, "count": 15}),
        ("search-pro 无intent",     {"search_engine": "search-pro", "search_query": query, "count": 15}),
        ("search-std 无intent",     {"search_engine": "search-std", "search_query": query, "count": 15}),
        ("最简只带query",            {"search_query": query, "count": 15}),
        ("极简无count",             {"search_query": query}),
    ]

    for name, payload in combos:
        try:
            r = requests.post(url, headers=HEADERS, json=payload, timeout=15)
            if r.status_code == 200:
                resp = r.json()
                items = resp.get("search_result", resp.get("data", []))
                if items:
                    print(f"  OK combo: {name} -> {len(items)} items")
                    return items
                print(f"  WARN {name}: 200 but empty")
            else:
                print(f"  FAIL {name}: HTTP {r.status_code} {r.text[:100]}")
        except Exception as e:
            print(f"  FAIL {name}: exception {e}")
    return []


def extract_codes(text):
    results = {}
    if not text:
        return results
    for m in MAPS:
        for p in [
            rf'{m}[密码]*[：:]\s*(\d{{4}})',
            rf'{m}\s*[是为]\s*(\d{{4}})',
            rf'{m}.{{0,10}}(\d{{4}})',
        ]:
            mm = re.search(p, text)
            if mm:
                results[m] = mm.group(1)
                break
    return results


def extract_from_results(results):
    text = ""
    for item in results:
        if isinstance(item, dict):
            text += item.get("content", "") + "\n"
            text += item.get("snippet", "") + "\n"
            text += item.get("title", "") + "\n"
    return extract_codes(text)


def write_to_supabase(results, today_str):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Supabase config missing")
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
        "source": "zhipu"
    }]
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code in (200, 201, 204):
            print("Supabase write OK")
            return True
        print(f"Supabase {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"Supabase exception: {e}")
        return False


def crawl():
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    mmdd = today.strftime("%m%d")

    print(f"Date: {today_str}")
    print(f"Key: built-in")
    print("-" * 55)

    query = f"三角洲行动 {mmdd} 今日密码 零号大坝 长弓溪谷 巴克什 航天基地 潮汐监狱 AZ3核电站"
    print(f"Trying combos...")
    raw = zhipu_web_search(query)

    results = {}
    if raw:
        results = extract_from_results(raw)
        print(f"Extracted {len(results)}/6")
        for k, v in results.items():
            print(f"   {k}: {v}")
    else:
        print("All combos failed")

    print("-" * 55)
    if len(results) >= 4:
        write_to_supabase(results, today_str)
    else:
        print(f"Only {len(results)}/6")

    signal.alarm(0)


if __name__ == "__main__":
    crawl()
