"""
B站 爬虫 —— 采集三角洲行动改枪码 / 跑刀路线 / 干员攻略
使用 bilibili-api 库（免费、无需登录）
"""
import os
import sys
import json
import time
import asyncio
import hashlib
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.ai_extractor import (
    extract_weapon_builds, extract_routes,
    extract_daily_code, extract_operators
)

# ---------- 搜索关键词 ----------
SEARCH_KEYWORDS = {
    "build": [
        "三角洲行动改枪码",
        "三角洲行动配枪码",
        "三角洲行动M7改枪码",
        "三角洲行动K416改枪码",
        "三角洲行动最强改枪码",
    ],
    "route": [
        "三角洲行动跑刀路线",
        "三角洲行动零号大坝跑刀",
        "三角洲行动航天基地跑刀路线",
        "三角洲行动巴克什跑刀",
    ],
    "operator": [
        "三角洲行动干员分析",
        "三角洲行动干员推荐",
        "三角洲行动哪个干员最强",
    ],
    "code": [
        "三角洲行动每日密码",
        "三角洲行动今日密码",
        "三角洲行动密码门",
    ],
}

def search_bilibili(keyword: str, page: int = 1) -> list[dict]:
    """搜索B站视频，返回视频列表"""
    try:
        from bilibili_api import search, sync
    except ImportError:
        print("[INFO] bilibili-api 未安装，使用 requests 备选方案")
        return _search_bilibili_fallback(keyword, page)

    try:
        results = sync(search.search(keyword, page=page))
        videos = []
        for item in results.get("result", []):
            if item.get("result_type") == "video":
                for v in item.get("data", []):
                    videos.append({
                        "bvid": v.get("bvid", ""),
                        "title": v.get("title", "").replace("&#39;", "'"),
                        "author": v.get("author", ""),
                        "url": f"https://www.bilibili.com/video/{v.get('bvid','')}",
                        "desc": v.get("description", ""),
                        "play": v.get("play", 0),
                        "pubdate": v.get("pubdate", 0),
                    })
        return videos
    except Exception as e:
        print(f"[WARN] B站搜索失败: {e}")
        return []

def _search_bilibili_fallback(keyword: str, page: int = 1) -> list[dict]:
    """不依赖 bilibili-api 的纯 requests 方案"""
    import requests
    import urllib.parse

    url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={urllib.parse.quote(keyword)}&page={page}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://search.bilibili.com",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        videos = []
        for item in data.get("data", {}).get("result", []):
            if item.get("result_type") == "video":
                for v in item.get("data", []):
                    videos.append({
                        "bvid": v.get("bvid", ""),
                        "title": v.get("title", ""),
                        "author": v.get("author", ""),
                        "url": f"https://www.bilibili.com/video/{v.get('bvid','')}",
                        "desc": v.get("description", ""),
                        "play": v.get("play", 0),
                    })
        return videos
    except Exception as e:
        print(f"[WARN] 备选搜索也失败: {e}")
        return []

def get_video_subtitle(bvid: str) -> str:
    """获取视频字幕/简介文本"""
    import requests

    # 1. 先拿视频详情页
    url = f"https://www.bilibili.com/video/{bvid}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        text = resp.text
        # 提取 og:description
        import re
        desc_match = re.search(r'og:description"\s+content="([^"]+)"', text)
        desc = desc_match.group(1) if desc_match else ""
        return desc
    except Exception as e:
        print(f"[WARN] 获取 {bvid} 内容失败: {e}")
        return ""

def crawl_category(category: str, keywords: list[str]) -> list[dict]:
    """采集某一类内容"""
    all_items = []
    for kw in keywords:
        print(f"  🔍 搜索: {kw}")
        videos = search_bilibili(kw, page=1)
        for v in videos[:5]:  # 每关键词取前5
            # 获取详细内容
            content = get_video_subtitle(v["bvid"])
            full_text = f"{v['title']} {v.get('desc','')} {content}"
            v["full_text"] = full_text
            v["keyword"] = kw
            all_items.append(v)
            time.sleep(1)  # 礼貌延迟
    return all_items

def main():
    print("=" * 50)
    print("🎯 三角洲情报站 —— B站采集器")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    results = {"builds": [], "routes": [], "operators": [], "codes": []}

    # 1. 采集改枪码
    print("\n📦 采集改枪码...")
    videos = crawl_category("build", SEARCH_KEYWORDS["build"])
    for v in videos:
        builds = extract_weapon_builds(v["full_text"])
        for b in builds:
            b["source_url"] = v["url"]
            b["source_platform"] = "bilibili"
            b["author"] = v.get("author", "")
            results["builds"].append(b)
    print(f"  ✅ 提取到 {len(results['builds'])} 条改枪码")

    # 2. 采集跑刀路线
    print("\n🗺️ 采集跑刀路线...")
    videos = crawl_category("route", SEARCH_KEYWORDS["route"])
    for v in videos:
        routes = extract_routes(v["full_text"])
        for r in routes:
            r["source_url"] = v["url"]
            r["source_platform"] = "bilibili"
            results["routes"].append(r)
    print(f"  ✅ 提取到 {len(results['routes'])} 条路线")

    # 3. 采集干员
    print("\n🎮 采集干员分析...")
    videos = crawl_category("operator", SEARCH_KEYWORDS["operator"])
    for v in videos:
        operators = extract_operators(v["full_text"])
        for o in operators:
            o["source_url"] = v["url"]
            o["source_platform"] = "bilibili"
            results["operators"].append(o)
    print(f"  ✅ 提取到 {len(results['operators'])} 条干员分析")

    # 4. 采集每日密码
    print("\n🔑 采集每日密码...")
    videos = crawl_category("code", SEARCH_KEYWORDS["code"])
    for v in videos:
        code = extract_daily_code(v["full_text"])
        if code:
            code["source_url"] = v["url"]
            code["source_platform"] = "bilibili"
            results["codes"].append(code)
    print(f"  ✅ 提取到 {len(results['codes'])} 条密码")

    # 保存结果
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"bilibili_{datetime.now():%Y%m%d_%H%M%S}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 数据已保存: {output_file}")

if __name__ == "__main__":
    main()
