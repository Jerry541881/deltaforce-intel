"""
短视频平台爬虫 —— 抖音/快手/虎牙
这些平台反爬严格，采用搜索结果页 + 字幕/标题提取策略
"""
import os
import sys
import json
import time
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.ai_extractor import (
    extract_weapon_builds, extract_routes,
    extract_daily_code, extract_operators
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# ============ 抖音（通过搜索接口） ============
def search_douyin(keyword: str) -> list[dict]:
    """
    抖音搜索 —— 使用 mobile 端接口
    注意：抖音反爬极强，GitHub Actions 环境 IP 可能被限制
    这里用公开搜索结果页做 best-effort
    """
    results = []
    # 方案：通过抖音网页版搜索
    search_url = f"https://www.douyin.com/search/{keyword}"
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=10, allow_redirects=True)
        # 抖音内容大多在 JS 渲染中，纯 requests 只能拿到骨架
        # 生产环境建议用 Playwright
        print(f"  [抖音] 搜索 '{keyword}' 状态码: {resp.status_code}")
        # 提取视频描述文本（尽力而为）
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        # 找所有包含关键词的文本片段
        texts = [t.get_text(strip=True) for t in soup.find_all(text=True)
                 if keyword.replace("三角洲行动", "") in t.get_text() if t.get_text(strip=True)]
        for t in texts[:10]:
            results.append({"platform": "douyin", "text": t[:500], "url": search_url})
    except Exception as e:
        print(f"  [抖音] 失败: {e}")
    return results

# ============ 快手 ============
def search_kuaishou(keyword: str) -> list[dict]:
    """快手搜索"""
    results = []
    # 快手有相对开放的搜索接口
    api_url = "https://www.kuaishou.com/graphql"
    try:
        resp = requests.get(
            f"https://www.kuaishou.com/search/video?searchKey={keyword}",
            headers=HEADERS, timeout=10
        )
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        # 提取视频标题/描述
        for tag in soup.find_all(["p", "span", "div"], limit=20):
            text = tag.get_text(strip=True)
            if len(text) > 10 and any(k in text for k in ["改枪", "跑刀", "密码", "干员"]):
                results.append({
                    "platform": "kuaishou",
                    "text": text[:500],
                    "url": f"https://www.kuaishou.com/search/video?searchKey={keyword}"
                })
        print(f"  [快手] 搜索 '{keyword}' 提取到 {len(results)} 条")
    except Exception as e:
        print(f"  [快手] 失败: {e}")
    return results

# ============ 虎牙 ============
def search_huya(keyword: str) -> list[dict]:
    """虎牙直播/视频搜索"""
    results = []
    try:
        resp = requests.get(
            f"https://www.huya.com/search?keyword={keyword}",
            headers=HEADERS, timeout=10
        )
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup.find_all(["p", "span", "div"], limit=20):
            text = tag.get_text(strip=True)
            if len(text) > 10:
                results.append({
                    "platform": "huya",
                    "text": text[:500],
                    "url": f"https://www.huya.com/search?keyword={keyword}"
                })
        print(f"  [虎牙] 搜索 '{keyword}' 提取到 {len(results)} 条")
    except Exception as e:
        print(f"  [虎牙] 失败: {e}")
    return results

# ============ 主流程 ============
def main():
    print("=" * 50)
    print("🎯 短视频平台采集器（抖音/快手/虎牙）")
    print(f"⏰ {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 50)

    keywords = [
        "三角洲行动改枪码",
        "三角洲行动跑刀路线",
        "三角洲行动每日密码",
        "三角洲行动干员推荐",
    ]

    all_data = {"builds": [], "routes": [], "codes": [], "operators": []}

    for kw in keywords:
        print(f"\n🔍 关键词: {kw}")

        # 快手
        items = search_kuaishou(kw)
        for item in items:
            text = item["text"]
            builds = extract_weapon_builds(text)
            routes = extract_routes(text)
            codes = extract_daily_code(text)
            ops = extract_operators(text)
            for b in builds:
                b["source_url"] = item["url"]
                b["source_platform"] = "kuaishou"
                all_data["builds"].append(b)
            for r in routes:
                r["source_url"] = item["url"]
                r["source_platform"] = "kuaishou"
                all_data["routes"].append(r)
            if codes:
                codes["source_url"] = item["url"]
                codes["source_platform"] = "kuaishou"
                all_data["codes"].append(codes)
            for o in ops:
                o["source_url"] = item["url"]
                o["source_platform"] = "kuaishou"
                all_data["operators"].append(o)
        time.sleep(2)

        # 虎牙
        items = search_huya(kw)
        for item in items:
            text = item["text"]
            builds = extract_weapon_builds(text)
            for b in builds:
                b["source_url"] = item["url"]
                b["source_platform"] = "huya"
                all_data["builds"].append(b)
        time.sleep(2)

        # 抖音（尽力）
        items = search_douyin(kw)
        for item in items:
            text = item["text"]
            builds = extract_weapon_builds(text)
            for b in builds:
                b["source_url"] = item["url"]
                b["source_platform"] = "douyin"
                all_data["builds"].append(b)
        time.sleep(3)

    # 保存
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    fname = f"shortvideo_{datetime.now():%Y%m%d_%H%M%S}.json"
    fpath = os.path.join(output_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！数据: {fpath}")
    print(f"  改枪码: {len(all_data['builds'])}")
    print(f"  路线: {len(all_data['routes'])}")
    print(f"  密码: {len(all_data['codes'])}")
    print(f"  干员: {len(all_data['operators'])}")

if __name__ == "__main__":
    main()
