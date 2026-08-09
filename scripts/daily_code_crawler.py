#!/usr/bin/env python3
"""
每日密码爬虫 - 智谱AI免费版（glm-4-7 + Web Search）
✅ 只用免费资源包覆盖的模型
✅ 只跑一次 Web Search，省额度
✅ Key 从环境变量读，不硬编码
"""

import os
import re
import signal
import requests
from datetime import date

# ============ 超时保护 ============
signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(120)

# ============ 配置（只从环境变量读）============
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ⚠️ 这就是你免费资源包支持的模型
MODEL = "glm-4-7"

HEADERS = {
    "Authorization": f"Bearer {ZHIPU_API_KEY}",
    "Content-Type": "application/json"
}

# ============ 六张地图 ============
MAPS = ["零号大坝", "长弓溪谷", "巴克什", "航天基地", "潮汐监狱", "AZ3核电站"]

# ============ 智谱 Web Search（最省，走 search_pro）============
def zhipu_web_search(query):
    if not ZHIPU_API_KEY:
        print("  ⚠️ ZHIPU_API_KEY 为空")
        return []

    url = "https://open.bigmodel.cn/api/paas/v4/web_search"
    data = {
        "search_engine": "search_pro",
        "search_query": query,
        "search_intent": "on",
        "count": 15
    }

    try:
        r = requests.post(url, headers=HEADERS, json=data, timeout=15)
        if r.status_code != 200:
            print(f"  ⚠️ Web Search HTTP {r.status_code}: {r.text[:200]}")
            return []
        resp = r.json()
        return resp.get("search_result", resp.get("data", []))
    except Exception as e:
        print(f"  ⚠️ Web Search 异常: {e}")
        return []

# ============ 提取密码 ============
def extract_codes_from_text(text):
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

def extract_from_search_results(results):
    text = ""
    for item in results:
        if isinstance(item, dict):
            text += item.get("content", "") + "\n"
            text += item.get("snippet", "") + "\n"
            text += item.get("title", "") + "\n"
    return extract_codes_from_text(text)

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
        "source": "zhipu-glm4-7"
    }]

    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code in (200, 201, 204):
            print("✅ 写入 Supabase 成功")
            return True
        print(f"⚠️ Supabase {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"⚠️ 写库异常: {e}")
        return False

# ============ 主流程 ============
def crawl():
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    mmdd = today.strftime("%m%d")

    print(f"🗓️ 采集 {today_str} 每日密码（智谱 {MODEL} 免费版）")
    print(f"🔑 Key: {'✅ 已加载' if ZHIPU_API_KEY else '❌ 缺失'}")
    print("─" * 50)

    # 只跑一次 Web Search，省额度
    query = f"三角洲行动 {mmdd} 今日密码 零号大坝 长弓溪谷 巴克什 航天基地 潮汐监狱 AZ3核电站"
    print(f"\n📡 Web Search: {query}")
    results_raw = zhipu_web_search(query)

    results = {}
    if results_raw:
        print(f"  📄 {len(results_raw)} 条结果")
        results = extract_from_search_results(results_raw)
        print(f"  ✅ 提取 {len(results)}/6")
        for k, v in results.items():
            print(f"     {k}: {v}")
    else:
        print("  ⚠️ 无结果")

    # 写库
    print("\n" + "─" * 50)
    if len(results) >= 4:
        ok = write_to_supabase(results, today_str)
        print(f"🎉 {today_str} 完成 ({len(results)}/6)" if ok else "⚠️ 爬到但写库失败")
    else:
        print(f"❌ 仅 {len(results)}/6，请在 Supabase 手动添加")

    signal.alarm(0)

if __name__ == "__main__":
    crawl()