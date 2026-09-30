#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日密码爬虫 - 年份修正版
修复"抓到2024年旧文章"致命问题：
  1. 搜索词加年份（三角洲行动 2026年9月30日 今日密码）
  2. 日期锚定支持年份，优先匹配"2026年9月30日"
  3. 往年(2024/2025)区块直接跳过，绝不把旧密码当今天的
保留修复：AZ3改名、分段提取、北京时区、写库3次重试
"""
import os, re, signal, time, requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(150)

ZHIPU_API_KEY = "a00b1314dd0a44c2bc522ac456bd6a22.GeFEMhnVCNQNJoju"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

ZH = {"Authorization": f"Bearer {ZHIPU_API_KEY}", "Content-Type": "application/json"}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}

MAPS = ["零号大坝", "长弓溪谷", "巴克什", "航天基地", "潮汐监狱", "AZ3"]


def bj_today():
    return datetime.now(timezone(timedelta(hours=8)))


def date_fields(dt):
    y, m, d = dt.year, dt.month, dt.day
    return {
        "today_str": f"{y}-{m:02d}-{d:02d}",
        "full_cn": f"{y}年{m}月{d}日",
        "iso": f"{y}-{m:02d}-{d:02d}",
        "slash": f"{y}/{m}/{d}",
        "cn_dash": f"{y}-{m}-{d}",
        "m_d": f"{m}月{d}日",
        "mmdd": f"{m:02d}{d:02d}",
        "year": y,
    }


def build_query(f):
    return f"三角洲行动 {f['full_cn']} 今日密码 零号大坝 长弓溪谷 巴克什 航天基地 潮汐监狱 AZ3"


def _seg(window):
    marks = []
    for m in MAPS:
        for mt in re.finditer(re.escape(m), window):
            marks.append((mt.start(), m))
    if not marks:
        return {}
    marks.sort()
    res = {}
    for i, (pos, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(window)
        mm = re.search(r'(\d{4})', window[pos:end])
        if mm and name not in res:
            res[name] = mm.group(1)
    return res


def extract(text, dt):
    """年份锚定：优先匹配含年份的今天日期，跳过往年区块"""
    if not text:
        return {}
    y, m, d = dt.year, dt.month, dt.day
    full = f"{y}年{m}月{d}日"
    iso = f"{y}-{m:02d}-{d:02d}"
    slash = f"{y}/{m}/{d}"
    cn_dash = f"{y}-{m}-{d}"
    m_d = f"{m}月{d}日"

    # 1) 含年份的"今天"锚点（最高优先级）
    primary = []
    for pat in (full, iso, slash, cn_dash):
        for mt in re.finditer(re.escape(pat), text):
            primary.append(mt.start())

    # 2) 月日锚点：校验前方最近年份不是往年
    secondary = []
    for mt in re.finditer(re.escape(m_d), text):
        pos = mt.start()
        if any(0 <= pos - p <= 8 for p in primary):
            continue
        prefix = text[max(0, pos - 150):pos]
        years = re.findall(r'(20\d{2})年', prefix)
        if years and int(years[-1]) != y:
            continue
        secondary.append(pos)

    anchors = sorted(set(primary + secondary))

    # 3) 其他日期标记（用于切断区块边界）
    others = []
    for mt in re.finditer(r'(20\d{2})年\d{1,2}月\d{1,2}日|(20\d{2})-\d{1,2}-\d{1,2}|\d{1,2}月\d{1,2}日', text):
        seg, pos = mt.group(0), mt.start()
        is_today = (seg == full or seg == iso or seg == cn_dash or
                    (seg == m_d and pos in secondary) or
                    any(0 <= pos - p <= 8 for p in primary))
        if not is_today:
            others.append(pos)

    res = {}
    for ap in anchors:
        later = [p for p in others if p > ap]
        end = min(later) if later else len(text)
        for k, v in _seg(text[ap:end]).items():
            if k not in res:
                res[k] = v
        if len(res) >= 6:
            break
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


def results_text(items):
    out = []
    for it in items:
        if isinstance(it, dict):
            for k in ("title", "content", "snippet", "summary"):
                if it.get(k):
                    out.append(str(it[k]))
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


def write_supabase(results, today_str, retries=3):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("  [Supabase] 配置缺失，跳过写库")
        return False
    code_str = "|".join(f"{k}:{v}" for k, v in results.items())
    url = f"{SUPABASE_URL}/rest/v1/daily_codes"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
               "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}
    data = [{"code_date": today_str, "code_value": code_str, "verified": True, "source": "auto"}]
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, headers=headers, json=data, timeout=20)
            if r.status_code in (200, 201, 204):
                print(f"  ✅ 写入成功 (第{attempt}次)")
                return True
            print(f"  ⚠️ HTTP {r.status_code}: {r.text[:150]}")
        except Exception as e:
            print(f"  ⚠️ 第{attempt}次失败: {type(e).__name__}，重试中...")
            time.sleep(2)
    print("  ❌ 写库最终失败，请手动添加")
    return False


def crawl():
    now = bj_today()
    f = date_fields(now)
    today_str = f["today_str"]
    q = build_query(f)
    print(f"🗓️ 北京时间今天: {today_str} ({f['full_cn']})")
    print(f"🔍 搜索词(含年份): {q}")
    print("─" * 55)

    results = {}
    print("\n📡 策略1: 智谱 Web Search")
    items = zhipu_search(q)
    if items:
        raw = results_text(items)
        print(f"  📄 原文前300字:\n{raw[:300]}")
        results = extract(raw, now)
        print(f"  ✅ 提取 {len(results)}/6")

    if len(results) < 6:
        print(f"\n📡 策略2: 18183兜底")
        html = fetch("https://db.18183.com/sjzmm/")
        if html:
            got = extract(html, now)
            new = {k: v for k, v in got.items() if k not in results}
            results.update(new)
            print(f"  18183: 新增{len(new)}条 (共{len(results)}/6)")
        else:
            print("  18183: 无响应")

    print("\n" + "─" * 55)
    if len(results) >= 4:
        print(f"📊 最终 {len(results)}/6")
        for k, v in results.items():
            print(f"   {k}: {v}")
        write_supabase(results, today_str)
        print(f"🎉 {today_str} 完成")
    else:
        print(f"❌ 仅 {len(results)}/6，请手动添加")
    signal.alarm(0)


if __name__ == "__main__":
    crawl()