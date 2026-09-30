#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日密码爬虫 - 最终修正版
修复3个致命bug:
  1. AZ3核电站 -> AZ3   （网站只写 AZ3，旧名永远匹配不上）
  2. 正则间距6 -> 分段提取（真实文本"密码门密码:0533"隔9字符，旧正则全漏）
  3. UTC -> 北京时区    （GitHub Actions 默认UTC，北京0-8点会拿到昨天）
日期完全随当天变化：所有 query / mmdd / 存储日期均由 bj_today() 推导
"""

import os
import re
import signal
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(150)

ZHIPU_API_KEY = "a00b1314dd0a44c2bc522ac456bd6a22.GeFEMhnVCNQNJoju"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

ZH = {"Authorization": f"Bearer {ZHIPU_API_KEY}", "Content-Type": "application/json"}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}

# 修正：用网站真实写法 AZ3，不是 AZ3核电站
MAPS = ["零号大坝", "长弓溪谷", "巴克什", "航天基地", "潮汐监狱", "AZ3"]


def bj_today():
    """强制北京时间(UTC+8)，避免 GitHub Actions UTC 拿到昨天"""
    return datetime.now(timezone(timedelta(hours=8)))


def build_date_fields(dt):
    """所有日期字段均由当天推导"""
    return {
        "today_str": dt.strftime("%Y-%m-%d"),   # 2026-09-30  存库用
        "m_d": f"{int(dt.strftime('%m'))}月{int(dt.strftime('%d'))}日",  # 9月30日 搜索用
        "mmdd": dt.strftime("%m%d"),            # 0930 备用
    }


def build_query(fields):
    """搜索词随当天变化"""
    return f"三角洲行动 {fields['m_d']} 今日密码 零号大坝 长弓溪谷 巴克什 航天基地 潮汐监狱 AZ3"


def extract(text):
    """分段提取：按地图名切段，每段取第一个4位数字"""
    if not text:
        return {}
    marks = []
    for m in MAPS:
        for mt in re.finditer(re.escape(m), text):
            marks.append((mt.start(), m))
    if not marks:
        return {}
    marks.sort()
    res = {}
    for i, (pos, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        seg = text[pos:end]
        mm = re.search(r'(\d{4})', seg)
        if mm and name not in res:
            res[name] = mm.group(1)
    return res


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


def results_to_text(items):
    out = []
    for it in items:
        if isinstance(it, dict):
            for k in ("title", "content", "snippet", "summary"):
                v = it.get(k)
                if v:
                    out.append(str(v))
    return "\n".join(out)


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
    data = [{"code_date": today_str, "code_value": code_str, "verified": True, "source": "auto"}]
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
    now = bj_today()
    fields = build_date_fields(now)
    today_str = fields["today_str"]
    q = build_query(fields)

    print(f"🗓️ 北京时间今天: {today_str} ({fields['m_d']})")
    print(f"🔍 搜索词随当天变化: {q}")
    print("─" * 55)

    results = {}

    print("\n📡 策略1: 智谱 Web Search")
    items = zhipu_search(q)
    if items:
        raw = results_to_text(items)
        print(f"  📄 原文前300字:\n{raw[:300]}")
        results = extract(raw)
        print(f"  ✅ 智谱提取 {len(results)}/6")

    if len(results) < 4:
        print(f"\n📡 策略2: 免Key直抓兜底")
        html = crawl_18183()
        if html:
            got = extract(html)
            new = {k: v for k, v in got.items() if k not in results}
            results.update(new)
            print(f"  18183: 新增 {len(new)} 条 (共{len(results)}/6)")
        else:
            print("  18183: 无响应")

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