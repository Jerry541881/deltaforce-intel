#!/usr/bin/env python3
"""
改枪码爬虫 —— 全武器版（无超时限制）
============================================
规则：
1. 只爬改枪码，不爬密码/跑刀/干员
2. 每把枪只取 B站热度最高的 1 条
3. 优先搜索结果 → 再打开视频页面
4. 字段完全匹配 Supabase weapon_builds 表
5. 不设置超时，所有枪全部爬完为止

改枪码格式（三角洲行动 S10赛季）：
  格式A（22位）: 6EIAUAK02U9HU6AC38CQJ
  格式B（带前缀）: M4A1突击步枪-全面战场-6H8PDBG05RVK0UR1L9GPJ
  格式C（分段）:  3S2E-7F9K-4D8G-1B6N

使用方法：
  python crawler_bilibili.py

环境变量：
  SUPABASE_URL               - Supabase 项目 URL
  SUPABASE_SERVICE_ROLE_KEY   - service_role API Key
"""

import os
import re
import json
import time
import requests
from datetime import date
from urllib.parse import quote

# ============ 配置 ============
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://search.bilibili.com",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ============ 改枪码正则（三种格式）============
# 格式A: 6开头，20-24位字母数字（核心格式）
RE_FORMAT_A = re.compile(r'\b6[A-Z0-9]{19,23}\b')
# 格式B: 带武器名前缀的 "xxx-全面战场-6XXXX" 或 "xxx-烽火地带-6XXXX"
RE_FORMAT_B = re.compile(r'[一-龥\w]+[-‑][一-龥\w]+[-‑](6[A-Z0-9]{19,23})')
# 格式C: 分段格式 XXXX-XXXX-XXXX-XXXX（4段，每段4字符）
RE_FORMAT_C = re.compile(r'\b([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})\b')

def extract_build_code(text):
    """从文本中提取改枪码，三种格式都试，返回第一个匹配"""
    if not text:
        return None
    # 格式C优先（分段的最明确）
    m = RE_FORMAT_C.search(text)
    if m:
        return m.group(1)
    # 格式B（带前缀）
    m = RE_FORMAT_B.search(text)
    if m:
        return m.group(1)
    # 格式A（纯码）
    m = RE_FORMAT_A.search(text)
    if m:
        return m.group(0)
    return None

# 从 weapons.py 读取武器列表
try:
    from weapons import WEAPONS
except ImportError:
    # 兜底列表（最少覆盖）
    WEAPONS = [
        {"name": "M4A1", "keyword": "三角洲行动 M4A1 改枪码", "category_id": 1, "tier_id": 2},
        {"name": "K416", "keyword": "三角洲行动 K416 改枪码", "category_id": 1, "tier_id": 1},
        {"name": "AKM", "keyword": "三角洲行动 AKM 改枪码", "category_id": 1, "tier_id": 1},
        {"name": "M7", "keyword": "三角洲行动 M7 改枪码", "category_id": 4, "tier_id": 1},
        {"name": "Vector", "keyword": "三角洲行动 Vector 改枪码", "category_id": 2, "tier_id": 1},
        {"name": "MP5", "keyword": "三角洲行动 MP5 改枪码", "category_id": 2, "tier_id": 1},
        {"name": "AWM", "keyword": "三角洲行动 AWM 改枪码", "category_id": 3, "tier_id": 1},
        {"name": "M82A1", "keyword": "三角洲行动 M82 改枪码", "category_id": 3, "tier_id": 1},
    ]

# ============ HTTP 请求（带重试）============
def fetch_page(url, timeout=15, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"    ⚠️ 请求失败(第{attempt+1}次): {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return ""

# ============ B站搜索API ============
def search_bilibili_videos(keyword, max_results=3):
    encoded = quote(keyword)
    url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={encoded}&page=1"
    headers_api = {**HEADERS, "Origin": "https://search.bilibili.com"}

    try:
        r = requests.get(url, headers=headers_api, timeout=15)
        data = r.json()
    except Exception as e:
        print(f"    ⚠️ B站API请求失败: {e}")
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

    videos.sort(key=lambda x: x.get("play", 0), reverse=True)
    return videos

# ============ 从视频页面提取文本 ============
def get_video_page_text(bvid):
    url = f"https://www.bilibili.com/video/{bvid}"
    html = fetch_page(url, timeout=15)
    if not html:
        return ""

    text_parts = []

    title_m = re.search(r'<title>([^<]+)</title>', html)
    if title_m:
        text_parts.append(title_m.group(1))

    desc_m = re.search(r'og:description"\s+content="([^"]+)"', html)
    if desc_m:
        text_parts.append(desc_m.group(1))

    meta_m = re.search(r'name="description"\s+content="([^"]+)"', html)
    if meta_m:
        text_parts.append(meta_m.group(1))

    init_m = re.search(r'__INITIAL_STATE__=(.+?)</script>', html)
    if init_m:
        text_parts.append(init_m.group(1)[:3000])

    return " ".join(text_parts)

# ============ 写 Supabase ============
def write_to_supabase(items):
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL 未配置")
        return False
    if not SUPABASE_KEY:
        print("❌ SUPABASE_SERVICE_ROLE_KEY 未配置")
        print("   请在 GitHub Settings → Secrets 中配置")
        return False

    url = f"{SUPABASE_URL}/rest/v1/weapon_builds"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }

    try:
        r = requests.post(url, headers=headers, json=items, timeout=30)
        print(f"📤 Supabase 返回: {r.status_code}")
        if r.status_code in (200, 201, 204):
            print(f"✅ 写入 Supabase 成功: {len(items)} 条")
            return True
        else:
            print(f"⚠️ Supabase 错误: {r.text[:300]}")
            return False
    except Exception as e:
        print(f"⚠️ 写库异常: {e}")
        return False

# ============ 保存本地备份 ============
def save_local_backup(items, today_str):
    backup_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, f"builds_{today_str.replace('-','')}.json")
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"💾 本地备份: {backup_file}")

# ============ 主流程 ============
def crawl():
    today = str(date.today())
    total = len(WEAPONS)

    print("=" * 60)
    print(f"🔫 改枪码全武器采集器")
    print(f"📅 {today} | 共 {total} 把枪 | 无超时限制")
    print("=" * 60)

    results = []
    found_list = []
    not_found_list = []

    for i, w in enumerate(WEAPONS, 1):
        name = w["name"]
        keyword = w["keyword"]

        print(f"\n[{i}/{total}] {name}")
        print(f"  🔍 搜索: {keyword}")

        videos = search_bilibili_videos(keyword, max_results=3)
        if not videos:
            print(f"  ❌ 没找到相关视频")
            not_found_list.append(name)
            continue

        print(f"  📹 找到 {len(videos)} 个视频")

        code_found = None
        source_url = ""
        author = ""
        view_count = 0

        for v in videos:
            bvid = v.get("bvid", "")
            if not bvid:
                continue

            title = v.get("title", "")
            play = v.get("play", 0)
            print(f"  👁 {title[:40]}... (播放:{play})")

            # 先试搜索结果的标题+描述
            search_text = f"{title} {v.get('desc', '')}"
            code = extract_build_code(search_text)

            if not code:
                # 再打开视频页面
                text = get_video_page_text(bvid)
                code = extract_build_code(text)

            if code:
                code_found = code
                source_url = f"https://www.bilibili.com/video/{bvid}"
                author = v.get("author", "")
                view_count = play
                print(f"  ✅ 改枪码: {code}")
                break

            time.sleep(1)

        if code_found:
            item = {
                "weapon_name": name,
                "category_id": w["category_id"],
                "tier_id": w["tier_id"],
                "build_code": code_found,
                "title": f"{name} 改枪码",
                "description": "",
                "source_url": source_url,
                "source_platform": "bilibili",
                "author": author,
                "tags": [],
                "view_count": view_count,
                "like_count": 0,
                "confidence_score": 0.85,
                "status": "active",
            }
            results.append(item)
            found_list.append(name)
        else:
            print(f"  ⚠️ 所有视频均未找到改枪码")
            not_found_list.append(name)

        time.sleep(2)

    # ============ 总结 ============
    print("\n" + "=" * 60)
    print(f"🎉 采集完成: 成功 {len(found_list)}/{total} 把枪")

    if found_list:
        print(f"\n✅ 已采集 ({len(found_list)}):")
        for n in found_list:
            print(f"   • {n}")

    if not_found_list:
        print(f"\n⚠️ 未找到 ({len(not_found_list)}):")
        for n in not_found_list:
            print(f"   • {n}")
        print(f"\n👉 这些枪等待管理员手动添加")

    if results:
        print(f"\n📤 正在写入 Supabase...")
        write_to_supabase(results)
        save_local_backup(results, today)
    else:
        print(f"\n⚠️ 没有可写入的数据")

    print("=" * 60)
    print("🏁 全部完成")


if __name__ == "__main__":
    crawl()
