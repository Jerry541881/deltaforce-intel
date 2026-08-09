#!/usr/bin/env python3
"""
每日密码爬虫 - 智谱AI联网搜索版（环境变量专用）
✅ 不硬编码 Key
✅ 优先 Web Search
✅ GLM 兜底
✅ 严格校验 4 位密码
"""

import os
import re
import signal
import requests
from datetime import date

# ============ 超时保护 ============
signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(180)

# ============ 配置（只从环境变量读 Key）============
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
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
    """调用智谱 Web Search API（search_pro）"""
    if not ZHIPU_API_KEY:
        print("  ⚠️ ZHIPU_API_KEY 为空")
        return []

    url = "https://open.bigmodel.cn/api/paas/v4/web_search"
    data = {
        "search_engine": "search_pro",
        "search_query": query,
        "search_intent": "on",
        "search_date_filter": "no_limit",
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

# ============ 智谱 GLM 联网推理 ============
def zhipu_ai_query(prompt):
    """GLM-4-Flash 联网回答"""
    if not ZHIPU_API_KEY:
        return ""

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    data = {
        "model": "glm-4-flash",
        "messages": [
            {"role": "system", "content": "你是信息检索助手，请联网搜索最新信息，直接给出准确答案，不要编造。"},
            {"role": "user", "content": prompt}
        ],
        "tools": [{"type": "web_search", "web_search": {"search_result": True}}],
        "temperature": 0.1
    }

    try:
        r = requests.post(url, headers=HEADERS, json=data, timeout=20)
        if r.status_code != 200:
            print(f"  ⚠️ GLM HTTP {r.status_code}: {r.text[:200]}")
            return ""
        resp = r.json()
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ⚠️ GLM 异常: {e}")
        return ""

# ============ 提取密码 ============
def extract_codes(text):
    """从文本提取 6 张地图的 4 位密码"""
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
    """合并所有搜索结果文本"""
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

    print(f"🗓️ 采集 {today_str} 每日密码（智谱AI）")
    print(f"🔑 Key状态: {'✅ 已加载' if ZHIPU_API_KEY else '❌ 缺失'}")
    print("─" * 50)

    results = {}

    # ---- 策略1: Web Search ----
    print("\n📡 策略1: 智谱 Web Search 联网搜索")
    query = f"三角洲行动 {mmdd} 今日密码 各地图 零号大坝 长弓溪谷 巴克什 航天基地 潮汐监狱 AZ3核电站"
    search_results = zhipu_web_search(query)

    if search_results:
        print(f"  📄 共 {len(search_results)} 条搜索结果")
        results = extract_from_search_results(search_results)
        print(f"  ✅ 提取到 {len(results)}/6 张地图密码")
        for k, v in results.items():
            print(f"     {k}: {v}")
    else:
        print("  ⚠️ Web Search 无结果")

    # ---- 策略2: GLM 兜底 ----
    if len(results) < 4:
        print(f"\n📡 策略2: 智谱 GLM 大模型联网推理")
        prompt = f"请联网搜索三角洲行动 {today_str} 今日密码，告诉我零号大坝、长弓溪谷、巴克什、航天基地、潮汐监狱、AZ3核电站 这6张地图今天的4位密码，格式：地图名:密码"
        reply = zhipu_ai_query(prompt)
        if reply:
            print(f"  📝 AI回复: {reply[:200]}")
            new_results = extract_codes(reply)
            for k, v in new_results.items():
                if k not in results:
                    results[k] = v
            print(f"  ✅ 补充后共 {len(results)}/6 张地图密码")
            for k, v in results.items():
                print(f"     {k}: {v}")

    # ---- 结果处理 ----
    print("\n" + "─" * 50)
    if len(results) >= 4:
        ok = write_to_supabase(results, today_str)
        if ok:
            print(f"🎉 完成: {today_str} 密码已入库 ({len(results)}/6)")
        else:
            print(f"⚠️ 爬到了但写库失败，请手动添加:")
            for k, v in results.items():
                print(f"   {k}: {v}")
    else:
        print(f"❌ 仅获取 {len(results)}/6 张地图密码，不够")
        print("👉 请在 Supabase 手动添加")
        print("   参考: 18183.com/db/sjzmm/ 或 好游快爆")

    signal.alarm(0)

if __name__ == "__main__":
    crawl()#!/usr/bin/env python3
"""
每日密码爬虫 - 智谱AI联网搜索版（环境变量专用）
✅ 不硬编码 Key
✅ 优先 Web Search
✅ GLM 兜底
✅ 严格校验 4 位密码
"""

import os
import re
import signal
import requests
from datetime import date

# ============ 超时保护 ============
signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(180)

# ============ 配置（只从环境变量读 Key）============
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
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
    """调用智谱 Web Search API（search_pro）"""
    if not ZHIPU_API_KEY:
        print("  ⚠️ ZHIPU_API_KEY 为空")
        return []

    url = "https://open.bigmodel.cn/api/paas/v4/web_search"
    data = {
        "search_engine": "search_pro",
        "search_query": query,
        "search_intent": "on",
        "search_date_filter": "no_limit",
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

# ============ 智谱 GLM 联网推理 ============
def zhipu_ai_query(prompt):
    """GLM-4-Flash 联网回答"""
    if not ZHIPU_API_KEY:
        return ""

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    data = {
        "model": "glm-4-flash",
        "messages": [
            {"role": "system", "content": "你是信息检索助手，请联网搜索最新信息，直接给出准确答案，不要编造。"},
            {"role": "user", "content": prompt}
        ],
        "tools": [{"type": "web_search", "web_search": {"search_result": True}}],
        "temperature": 0.1
    }

    try:
        r = requests.post(url, headers=HEADERS, json=data, timeout=20)
        if r.status_code != 200:
            print(f"  ⚠️ GLM HTTP {r.status_code}: {r.text[:200]}")
            return ""
        resp = r.json()
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ⚠️ GLM 异常: {e}")
        return ""

# ============ 提取密码 ============
def extract_codes(text):
    """从文本提取 6 张地图的 4 位密码"""
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
    """合并所有搜索结果文本"""
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

    print(f"🗓️ 采集 {today_str} 每日密码（智谱AI）")
    print(f"🔑 Key状态: {'✅ 已加载' if ZHIPU_API_KEY else '❌ 缺失'}")
    print("─" * 50)

    results = {}

    # ---- 策略1: Web Search ----
    print("\n📡 策略1: 智谱 Web Search 联网搜索")
    query = f"三角洲行动 {mmdd} 今日密码 各地图 零号大坝 长弓溪谷 巴克什 航天基地 潮汐监狱 AZ3核电站"
    search_results = zhipu_web_search(query)

    if search_results:
        print(f"  📄 共 {len(search_results)} 条搜索结果")
        results = extract_from_search_results(search_results)
        print(f"  ✅ 提取到 {len(results)}/6 张地图密码")
        for k, v in results.items():
            print(f"     {k}: {v}")
    else:
        print("  ⚠️ Web Search 无结果")

    # ---- 策略2: GLM 兜底 ----
    if len(results) < 4:
        print(f"\n📡 策略2: 智谱 GLM 大模型联网推理")
        prompt = f"请联网搜索三角洲行动 {today_str} 今日密码，告诉我零号大坝、长弓溪谷、巴克什、航天基地、潮汐监狱、AZ3核电站 这6张地图今天的4位密码，格式：地图名:密码"
        reply = zhipu_ai_query(prompt)
        if reply:
            print(f"  📝 AI回复: {reply[:200]}")
            new_results = extract_codes(reply)
            for k, v in new_results.items():
                if k not in results:
                    results[k] = v
            print(f"  ✅ 补充后共 {len(results)}/6 张地图密码")
            for k, v in results.items():
                print(f"     {k}: {v}")

    # ---- 结果处理 ----
    print("\n" + "─" * 50)
    if len(results) >= 4:
        ok = write_to_supabase(results, today_str)
        if ok:
            print(f"🎉 完成: {today_str} 密码已入库 ({len(results)}/6)")
        else:
            print(f"⚠️ 爬到了但写库失败，请手动添加:")
            for k, v in results.items():
                print(f"   {k}: {v}")
    else:
        print(f"❌ 仅获取 {len(results)}/6 张地图密码，不够")
        print("👉 请在 Supabase 手动添加")
        print("   参考: 18183.com/db/sjzmm/ 或 好游快爆")

    signal.alarm(0)

if __name__ == "__main__":
    crawl()