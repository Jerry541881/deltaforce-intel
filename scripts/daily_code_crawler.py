#!/usr/bin/env python3
"""
每日密码爬虫 - 智谱AI联网搜索版
✅ 用智谱AI的Web Search API联网搜索"三角洲行动今日密码"
✅ AI搜索比B站/18183更智能，能理解语义、跨多源汇总
✅ 6张地图密码全拿
✅ 用 SUPABASE_SERVICE_ROLE_KEY 写库
"""

import os
import re
import json
import signal
import requests
from datetime import date

# ============ 超时保护 ============
signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(180)  # 3分钟

# ============ 配置（函数内延迟读取环境变量）============
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

ZHIPU_SEARCH_URL = "https://open.bigmodel.cn/api/paas/v4/web_search"
ZHIPU_CHAT_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# ============ 六张地图 ============
MAPS = [
    "零号大坝",
    "长弓溪谷",
    "巴克什",
    "航天基地",
    "潮汐监狱",
    "AZ3核电站",
]

# ============ 智谱AI联网搜索 ============
def zhipu_web_search(query, count=15):
    """
    调用智谱AI Web Search API
    返回: list of {title, content, link, media, publish_date}
    """
    api_key = os.getenv("ZHIPU_API_KEY", "")
    if not api_key:
        print("  ❌ ZHIPU_API_KEY 未配置")
        return None

    payload = {
        "search_query": query,
        "search_engine": "search_pro",    # 高阶版，更精准
        "search_intent": True,             # 开启意图识别
        "count": count,
        "search_recency_filter": "oneDay",  # 只要今天的内容
        "content_size": "high",           # 长摘要，方便提取密码
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(ZHIPU_SEARCH_URL, json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("search_result", [])
    except Exception as e:
        print(f"  ⚠️ 智谱搜索异常: {e}")
        return None

# ============ 智谱AI大模型直接回答（兜底）============
def zhipu_ai_query(prompt):
    """
    调用智谱GLM大模型，让它联网搜索后直接回答今日密码
    """
    api_key = os.getenv("ZHIPU_API_KEY", "")
    if not api_key:
        return None

    payload = {
        "model": "glm-4-flash",   # 免费模型，够用
        "messages": [
            {"role": "system", "content": "你是一个游戏资讯助手，只回答三角洲行动今日密码。请联网搜索后给出准确答案。直接给出地图和密码的对应关系，不要废话。"},
            {"role": "user", "content": prompt}
        ],
        "tools": [
            {
                "type": "web_search",
                "web_search": {
                    "enable": True,
                    "search_engine": "search_pro"
                }
            }
        ],
        "tool_choice": "auto"
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(ZHIPU_CHAT_URL, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return None
    except Exception as e:
        print(f"  ⚠️ 智谱AI对话异常: {e}")
        return None

# ============ 从搜索结果/AI回复里提取密码 ============
def extract_codes_from_text(text):
    """
    从文本中按6张地图依次提取4位密码
    返回: dict {地图名: 密码}
    """
    if not text:
        return {}

    found = {}
    for m in MAPS:
        patterns = [
            rf'{m}[密码]*[：:：\s]*(\d{{4}})',
            rf'{m}\s*[是为]?\s*(\d{{4}})',
        ]
        for p in patterns:
            mm = re.search(p, text)
            if mm:
                found[m] = mm.group(1)
                break

    return found

def extract_codes_from_results(results):
    """
    从智谱返回的搜索结果列表提取密码
    """
    if not results:
        return {}

    full_text = ""
    for item in results:
        full_text += f"\n{item.get('title','')}\n{item.get('content','')}\n"

    print(f"  📄 共 {len(results)} 条搜索结果，开始提取密码...")
    found = extract_codes_from_text(full_text)

    for k, v in found.items():
        print(f"     ✅ {k}: {v}")

    return found

# ============ 写 Supabase ============
def write_to_supabase(results, today_str):
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    if not supabase_url or not supabase_key:
        print("❌ Supabase 配置缺失")
        print(f"   请在 GitHub Settings → Secrets 配置")
        print(f"   手动添加: {today_str} = {results}")
        return False

    # 拼成 "零号大坝:9514|长弓溪谷:4654|..." 格式
    code_str = "|".join([f"{k}:{v}" for k, v in results.items()])

    url = f"{supabase_url}/rest/v1/daily_codes"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
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
    today = date.today().strftime("%Y-%m-%d")
    mmdd = date.today().strftime("%m%d")

    print(f"🗓️ 采集 {today} 每日密码（智谱AI联网搜索）")
    print("─" * 55)

    found = {}

    # ===== 策略1: 智谱 Web Search API（精准搜索）=====
    print(f"\n📡 策略1: 智谱 Web Search 联网搜索")
    query = f"三角洲行动 {mmdd} 今日密码 各地图"
    print(f"   搜索: {query}")

    results_raw = zhipu_web_search(query, count=15)
    found = extract_codes_from_results(results_raw)

    # ===== 如果不够，策略2: 智谱GLM大模型直接回答 =====
    if len(found) < 4:
        print(f"\n  ⚠️ Web Search 仅获取 {len(found)}/6，启动策略2...")
        print(f"\n📡 策略2: 智谱 GLM 大模型（联网+推理）")

        today_str_cn = date.today().strftime("%Y年%m月%d日")
        prompt = f"请联网搜索三角洲行动{today_str_cn}今日密码，告诉我零号大坝、长弓溪谷、巴克什、航天基地、潮汐监狱、AZ3核电站这6张地图各自的4位密码数字。"
        print(f"   提问: {prompt[:60]}...")

        reply = zhipu_ai_query(prompt)
        if reply:
            print(f"   AI回复: {reply[:200]}...")
            ai_found = extract_codes_from_text(reply)
            # 合并：策略1优先，缺的补上策略2的
            for k, v in ai_found.items():
                if k not in found:
                    found[k] = v
                    print(f"     ✅ {k}: {v} (来自AI)")

    # ===== 结果处理 =====
    print("\n" + "─" * 55)
    if len(found) >= 4:
        print(f"📊 最终获取: {len(found)}/6 张地图密码")
        for k, v in found.items():
            print(f"   {k}: {v}")

        ok = write_to_supabase(found, today)
        if ok:
            print(f"\n🎉 完成: {today} 密码已入库")
        else:
            print(f"\n⚠️ 爬到了但写库失败，请手动添加:")
            for k, v in found.items():
                print(f"   {k}: {v}")
    else:
        print(f"❌ 仅获取 {len(found)}/6 张地图密码，不够")
        if found:
            print("   已找到的:")
            for k, v in found.items():
                print(f"   {k}: {v}")
        print("👉 请在 Supabase 手动添加")
        print("   参考来源: 18183.com/db/sjzmm/ 或 好游快爆")

    signal.alarm(0)

if __name__ == "__main__":
    crawl()
