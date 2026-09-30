#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日密码爬虫 - 最终版
1) 智谱 Web Search（Key 内置）
2) 打印原始结果前300字，便于排查
3) 智谱不足4条 -> 免Key直抓 18183 / 必应 兜底
"""

import os
import re
import signal
import requests
from datetime import date
from urllib.parse import quote

signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(150)

ZHIPU_API_KEY = "a00b1314dd0a44c2bc522ac456bd6a22.GeFEMhnVCNQNJoju"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

ZH = {"Authorization": f"Bearer {ZHIPU_API_KEY}", "Content-Type": "application/json"}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}

MAPS = ["零号大坝", "长弓溪谷", "巴克什", "航天基地", "潮汐监狱", "AZ3核电站"]


def zhipu_search(q):
    url = "https://open.bigmodel.cn/api/paas/v4/web_search"
    combos = [
        {"search_engine": "search-pro", "search_query": q, "search_intent": True, "count": 15},
        {"search_engine": "search_pro", "search_query": q, "search_intent": True, "count": 15},
        {"search_engine": "search-pro", "search_query": q, "count": 15},
        {"search_query": q, "count": 15},
    ]
    for i, p in enumerate(combos, 1):
        try:
            r = requests.post(url, headers=ZH, json=p, timeout=15)
            if r.status_code == 200:
                j = r.json()
                items = j.get("search_result", j.get("data", []))
                if items:
                    print(f"  [组合{i}] OK -> {len(items)}条")
                    return items
                print(f"  [组合{i}] 200但空")
            else:
                print(f"  [组合{i}] HTTP {r.status_code}")
        except Exception as e:
            print(f"  [组合{i}] 异常 {type(e).__name__}")
    return []


def fetch(url, timeout=10):
    try:
        r = requests.get(url, headers=UA, timeout=timeout)
        if r.status_code == 200:
            r.encoding = r.apparent_encoding or "utf-8"
            return r.text
    except Exception:
        pass
    return ""


def crawl_18183():
    return fetch("https://db.18183.com/sjzmm/")

def crawl_bing(mmdd):
    return fetch(f"https://cn.bing.com/search?q={quote(f'三角洲行动{mmdd}今日密码')}")

def crawl_sogou(mmdd):
    return fetch(f"https://www.sogou.com/web?query={quote(f'三角洲行动{mmdd}今日密码')}")


def extract_codes(text):
    """从任意文本提取6张地图的4位密码"""
    results = {}
    if not text:
        return results
    for m in MAPS:
        pats = [
            rf'{m}[^\d]{{0,6}}(\d{{4}})',
            rf'{m}\D{{0,4}}(\d{{4}})',
        ]
        for p in pats:
            mm = re.search(p, text)
            if mm:
                results[m] = mm.group(1)
                break
    return results


def results_to_text(items):
    """把智谱搜索结果列表拼成文本"""
    out = []
    for it in items:
        if isinstance(it, dict):
            for k in ("title", "content", "snippet", "summary"):
                v = it.get(k)
                if v:
                    out.append(str(v))
    return "\n".join(out)


def write_to_supabase(results, today_str):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("  [Supabase] 配置缺失，跳过写库")
        return False
    code_str = "|".join(f"{k}:{v}" for k, v in results.items())
    url = f"{SUPABASE_URL}/rest/v1/daily_codes"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }
    data = [{
        "code_date": today_str,
        "code_value": code_str,
        "verified": True,
        "source": "auto",
    }]
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code in (200, 201, 204):
            print("  ✅ 写入 Supabase 成功")
            return True
        print(f"  ⚠️ Supabase HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"  ⚠️ 写库异常 {type(e).__name__}")
    return False


def crawl():
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    mmdd = today.strftime("%m%d")

    print(f"🗓️ 采集 {today_str} 每日密码")
    print("─" * 55)

    results = {}

    # 策略1: 智谱
    print("\n📡 策略1: 智谱 Web Search")
    q = f"三角洲行动 {mmdd} 今日密码 零号大坝 长弓溪谷 巴克什 航天基地 潮汐监狱 AZ3核电站"
    items = zhipu_search(q)
    if items:
        raw = results_to_text(items)
        print(f"  📄 原文前300字:\n{raw[:300]}")
        results = extract_codes(raw)
        print(f"  ✅ 智谱提取 {len(results)}/6")

    # 策略2: 免Key兜底
    if len(results) < 4:
        print(f"\n📡 策略2: 免Key直抓兜底")
        for name, fn in [("18183", crawl_18183), ("必应", lambda: crawl_bing(mmdd)), ("搜狗", lambda: crawl_sogou(mmdd))]:
            try:
                html = fn()
            except Exception:
                html = ""
            if not html:
                print(f"  {name}: 无响应")
                continue
            got = extract_codes(html)
            new = {k: v for k, v in got.items() if k not in results}
            results.update(new)
            print(f"  {name}: 新增 {len(new)} 条 (共{len(results)}/6)")
            if len(results) >= 4:
                break

    # 结果
    print("\n" + "─" * 55)
    if len(results) >= 4:
        print(f"📊 最终 {len(results)}/6")
        for k, v in results.items():
            print(f"   {k}: {v}")
        write_to_supabase(results, today_str)
        print(f"🎉 {today_str} 完成")
    else:
        print(f"❌ 仅 {len(results)}/6，请在 Supabase 手动添加")

    signal.alarm(0)


if __name__ == "__main__":
    crawl()