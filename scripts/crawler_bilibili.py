#!/usr/bin/env python3
"""
改枪码 + 跑刀路线爬虫
策略（按你的要求）：
1. 改枪码：简介/评论区优先（快）
2. 跑刀路线：只从视频正文/字幕找（不走评论区）
3. 爬到改枪码就停，跑刀路线必须进正文
"""

import os
import re
import json
import requests
from datetime import date
from urllib.parse import quote

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.bilibili.com"
}

# 改枪码
BUILD_CODE_RE = re.compile(r'\b[6A-Z0-9]{20,24}\b')
# 跑刀路线关键词
ROUTE_KEYWORDS = ["跑刀", "路线", "撤离", "点位", "出生点"]

def fetch_html(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.raise_for_status()
        return r.text
    except Exception:
        return ""

def extract_codes(text):
    return [
        {"build_code": m.group(0)}
        for m in BUILD_CODE_RE.finditer(text)
    ]

def looks_like_route(text):
    """判断一段文字是否像跑刀路线"""
    t = text.lower()
    return any(k in t for k in ROUTE_KEYWORDS)

# ---------- 改枪码：快 ----------
def parse_for_builds(html):
    """只负责改枪码，扫全文即可"""
    return extract_codes(html)

# ---------- 跑刀路线：慢 ----------
def parse_for_routes(html):
    """只负责跑刀路线，不筛评论区，只认正文/字幕"""
    results = []
    lines = html.split("\n")
    for line in lines:
        if looks_like_route(line):
            results.append({
                "route_text": line.strip()
            })
    return results

def search_bilibili(keyword, max_results=2):
    query = quote(keyword)
    html = fetch_html(f"https://search.bilibili.com/all?keyword={query}")
    if not html:
        return []
    bvs = list(set(re.findall(r'/video/(BV\w+)', html)))
    return [f"https://www.bilibili.com/video/{bv}" for bv in bvs[:max_results]]

def crawl():
    today = str(date.today())

    # ===== 1. 改枪码（快）=====
    print("🔫 开始采集改枪码（简介/评论区优先）...")
    build_queries = ["三角洲行动 M7 改枪码", "三角洲行动 改枪码 T0"]
    builds = []

    for q in build_queries:
        video_urls = search_bilibili(q, max_results=2)
        for url in video_urls:
            html = fetch_html(url)
            items = parse_for_builds(html)
            if items:
                print(f"[改枪码] ✅ {url}")
                for it in items:
                    it["source"] = "bilibili"
                    it["source_url"] = url
                    it["date"] = today
                builds.extend(items)
                break  # 改枪码找到一个就停
            else:
                print(f"[改枪码] ⚠️ 未找到: {url}")

    # ===== 2. 跑刀路线（慢，不走评论区）=====
    print("\n🗺️ 开始采集跑刀路线（仅视频正文）...")
    route_queries = ["三角洲行动 跑刀路线", "三角洲行动 零号大坝 跑刀"]
    routes = []

    for q in route_queries:
        video_urls = search_bilibili(q, max_results=2)
        for url in video_urls:
            html = fetch_html(url)
            items = parse_for_routes(html)  # ★ 这里只用正文解析
            if items:
                print(f"[跑刀] ✅ {url}")
                for it in items:
                    it["source"] = "bilibili"
                    it["source_url"] = url
                    it["date"] = today
                routes.extend(items)
            else:
                print(f"[跑刀] ⚠️ 未找到: {url}")

    # ===== 3. 去重 =====
    seen_builds = set()
    final_builds = []
    for b in builds:
        c = b.get("build_code")
        if c and c not in seen_builds:
            seen_builds.add(c)
            final_builds.append(b)

    # ===== 4. 输出 =====
    print(f"\n✅ 改枪码: {len(final_builds)} 条")
    print(f"✅ 跑刀路线: {len(routes)} 条")

    if final_builds:
        print(json.dumps(final_builds[:3], ensure_ascii=False, indent=2))
    if routes:
        print(json.dumps(routes[:3], ensure_ascii=False, indent=2))

    return {
        "builds": final_builds,
        "routes": routes
    }

if __name__ == "__main__":
    crawl()