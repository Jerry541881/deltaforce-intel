#!/usr/bin/env python3
"""
每日密码爬虫 —— 最终版
===========================
功能：从 B站搜索"三角洲行动今日密码"，提取4位密码

字段完全匹配 Supabase daily_codes 表：
  code_date    DATE      - 日期
  code_value   TEXT      - 4位密码
  source_count INT       - 来源数量
  sources      JSONB     - 来源列表
  confidence   DECIMAL   - 置信度
  verified     BOOLEAN   - 是否验证
  notes        TEXT      - 备注

使用方法：
  python daily_code_crawler.py

环境变量：
  SUPABASE_URL               - Supabase 项目 URL
  SUPABASE_SERVICE_ROLE_KEY   - service_role API Key
"""

import os
import re
import time
import requests
from datetime import date
from urllib.parse import quote

# ============ 配置 ============
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# 4位数字密码正则（前后不能是数字）
CODE_4DIGIT = re.compile(r'(?<!\d)(\d{4})(?!\d)')

# ============ HTTP 请求（带重试）============
def fetch(url, timeout=15, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"  ⚠️ 请求失败(第{attempt+1}次): {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return ""

# ============ B站搜索API ============
def search_bilibili_videos(keyword, max_results=5):
    """调用 B站搜索API 找视频"""
    encoded = quote(keyword)
    url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={encoded}&page=1"
    headers_api = {**HEADERS, "Origin": "https://search.bilibili.com"}

    try:
        r = requests.get(url, headers=headers_api, timeout=15)
        data = r.json()
    except Exception as e:
        print(f"  ⚠️ B站API请求失败: {e}")
        return []

    videos = []
    for item in data.get("data", {}).get("result", []):
        if item.get("result_type") == "video":
            for v in item.get("data", []):
                videos.append({
                    "bvid": v.get("bvid", ""),
                    "title": v.get("title", "").replace("&#39;", "'"),
                    "desc": v.get("description", ""),
                    "play": v.get("play", 0),
                    "author": v.get("author", ""),
                    "pubdate": v.get("pubdate", 0),
                })
                if len(videos) >= max_results:
                    break
        if len(videos) >= max_results:
            break

    return videos

# ============ 从视频页面提取密码 ============
def extract_code_from_page(bvid):
    """打开视频页面，从描述/标题/正文中找4位密码"""
    url = f"https://www.bilibili.com/video/{bvid}"
    html = fetch(url, timeout=15)
    if not html:
        return None

    # 方法1：og:description（最常用，UP主通常写在简介）
    desc_m = re.search(r'og:description"\s+content="([^"]+)"', html)
    if desc_m:
        text = desc_m.group(1)
        # 找"今日密码xxx"或"今天密码xxx"附近的4位数字
        m = re.search(r'(?:今天|今日|今日密码|今天的密码).{0,30}?(\d{4})', text)
        if m:
            return m.group(1)

    # 方法2：全局搜索"今日密码"附近数字
    m = re.search(r'(今日密码|今天密码|今日.{0,5}密码).{0,50}?(\d{4})', html)
    if m:
        return m.group(2)

    # 方法3：所有含"密码/开门/安全箱"的description
    all_descs = re.findall(r'content="([^"]*(?:密码|开门|安全箱)[^"]*)"', html)
    for d in all_descs:
        m = CODE_4DIGIT.search(d)
        if m:
            return m.group(1)

    # 方法4：标题里直接有4位数字
    title_m = re.search(r'<title>([^<]+)</title>', html)
    if title_m:
        m = CODE_4DIGIT.search(title_m.group(1))
        if m:
            return m.group(1)

    return None

# ============ 从搜索结果提取 ============
def extract_code_from_search(videos):
    """从搜索结果的标题/描述里直接找密码"""
    for v in videos:
        full = f"{v.get('title','')} {v.get('desc','')}"
        if re.search(r'今天|今日', full):
            m = re.search(r'(?:今天|今日).{0,30}?(\d{4})', full)
            if m:
                return m.group(1), v.get("bvid", "")
    return None, ""

# ============ 写 Supabase ============
def write_to_supabase(code, source_url="", source_name="bilibili"):
    """写入 daily_codes 表"""
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL 未配置")
        return False
    if not SUPABASE_KEY:
        print("❌ SUPABASE_SERVICE_ROLE_KEY 未配置")
        print("   请在 GitHub Settings → Secrets 中配置")
        return False

    today = date.today().isoformat()
    url = f"{SUPABASE_URL}/rest/v1/daily_codes"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    data = [{
        "code_date": today,
        "code_value": code,
        "source_count": 1,
        "sources": [source_name],
        "confidence": 0.85,
        "verified": True,
        "notes": f"来源: {source_url}" if source_url else "",
    }]

    try:
        r = requests.post(url, headers=headers, json=data, timeout=15)
        print(f"📤 Supabase 返回: {r.status_code}")
        if r.status_code in (200, 201, 204):
            print(f"✅ 写入 Supabase 成功: {code} (日期: {today})")
            return True
        else:
            print(f"⚠️ Supabase 错误: {r.text[:300]}")
            return False
    except Exception as e:
        print(f"⚠️ 写库异常: {e}")
        return False

# ============ 主流程 ============
def crawl():
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    print("=" * 55)
    print(f"🔑 每日密码采集器")
    print(f"📅 {today_str}")
    print("=" * 55)

    # 多个搜索关键词，提高命中率
    keywords = [
        "三角洲行动今日密码",
        "三角洲行动 今日密码",
        "三角洲行动密码门今日",
        "三角洲行动 安全箱密码 今天",
    ]

    found_code = None
    found_url = ""

    for kw in keywords:
        print(f"\n🔍 搜索: {kw}")
        videos = search_bilibili_videos(kw, max_results=5)
        print(f"   找到 {len(videos)} 个视频")

        if not videos:
            continue

        # 先从搜索结果里找
        code, bvid = extract_code_from_search(videos)
        if code:
            found_code = code
            found_url = f"https://www.bilibili.com/video/{bvid}" if bvid else ""
            print(f"   ✅ 从搜索结果找到: {code}")
            break

        # 逐个打开视频页面
        for v in videos[:3]:
            bvid = v.get("bvid", "")
            if not bvid:
                continue
            title = v.get("title", "")[:35]
            print(f"   📹 检查: {title}...")

            code = extract_code_from_page(bvid)
            if code:
                found_code = code
                found_url = f"https://www.bilibili.com/video/{bvid}"
                print(f"   ✅ 从视频页面找到: {code}")
                break

            time.sleep(1)

        if found_code:
            break

    # ============ 总结 ============
    print("\n" + "─" * 55)
    if found_code:
        print(f"🎉 今日密码: {found_code}")
        write_to_supabase(found_code, found_url)
    else:
        print("❌ 今日密码未找到")
        print("👉 请在 Supabase 手动添加")
        print(f"   表: daily_codes")
        print(f"   字段: code_date={today_str}, code_value=<4位>, verified=true")
    print("─" * 55)


if __name__ == "__main__":
    crawl()
