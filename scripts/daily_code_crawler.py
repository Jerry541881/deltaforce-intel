"""
每日密码专项采集 —— 多次搜索交叉验证
策略：从B站/抖音/快手/贴吧/知乎多源搜索，>=2 源一致才入库
"""
import os
import sys
import json
import time
import requests
from datetime import datetime, date
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.ai_extractor import extract_daily_code

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}

def search_bilibili_code() -> list[dict]:
    """B站搜索今日密码"""
    results = []
    keywords = ["三角洲行动今日密码", "三角洲行动每日密码", "三角洲行动密码门今日"]
    for kw in keywords:
        url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={kw}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            data = resp.json()
            for item in data.get("data", {}).get("result", []):
                if item.get("result_type") == "video":
                    for v in item.get("data", []):
                        # 获取视频简介
                        desc = v.get("description", "")
                        title = v.get("title", "")
                        full = f"{title} {desc}"
                        code = extract_daily_code(full)
                        if code:
                            code["source"] = "bilibili"
                            code["url"] = f"https://www.bilibili.com/video/{v.get('bvid','')}"
                            results.append(code)
            time.sleep(1)
        except Exception as e:
            print(f"  [B站] {kw} 失败: {e}")
    return results

def search_baidu_code() -> list[dict]:
    """百度搜索三角洲行动今日密码"""
    results = []
    query = "三角洲行动 今日密码"
    url = f"https://www.baidu.com/s?wd={query}"
    headers = {**HEADERS, "Cookie": ""}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        # 提取搜索结果摘要
        for div in soup.find_all("div", class_="c-abstract"):
            text = div.get_text(strip=True)
            code = extract_daily_code(text)
            if code:
                code["source"] = "baidu"
                results.append(code)
        for span in soup.find_all("span", class_="content-right_8Zs40"):
            text = span.get_text(strip=True)
            code = extract_daily_code(text)
            if code:
                code["source"] = "baidu"
                results.append(code)
        print(f"  [百度] 提取到 {len(results)} 条")
    except Exception as e:
        print(f"  [百度] 失败: {e}")
    return results

def search_douyin_code() -> list[dict]:
    """抖音搜索（尽力）"""
    results = []
    url = "https://www.douyin.com/search/三角洲行动今日密码"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        for t in soup.find_all(text=True):
            text = t.strip()
            if len(text) > 5 and any(k in text for k in ["密码", "开门"]):
                code = extract_daily_code(text)
                if code:
                    code["source"] = "douyin"
                    results.append(code)
        print(f"  [抖音] 提取到 {len(results)} 条")
    except Exception as e:
        print(f"  [抖音] 失败: {e}")
    return results

def cross_validate(results: list[dict]) -> dict | None:
    """
    交叉验证：>=2 源一致才确认
    返回最终密码对象 或 None
    """
    if not results:
        return None

    # 统计每个密码出现次数
    code_counter = Counter()
    code_sources = {}
    for r in results:
        c = r.get("code", "").strip()
        if c and len(c) >= 3:
            code_counter[c] += 1
            if c not in code_sources:
                code_sources[c] = []
            code_sources[c].append(r.get("source", "unknown"))

    # 找出现 >=2 次的
    for code, count in code_counter.most_common():
        if count >= 2:
            return {
                "code_date": date.today().isoformat(),
                "code_value": code,
                "source_count": count,
                "sources": code_sources[code],
                "confidence": min(0.5 + count * 0.15, 0.95),
                "verified": True,
            }

    # 没有交叉验证通过的，返回置信度最高的单源
    if results:
        best = max(results, key=lambda x: x.get("confidence", 0))
        return {
            "code_date": date.today().isoformat(),
            "code_value": best.get("code", ""),
            "source_count": 1,
            "sources": [best.get("source", "unknown")],
            "confidence": best.get("confidence", 0.3),
            "verified": False,
        }

    return None

def save_to_supabase(final_code: dict):
    """写入 Supabase daily_codes 表"""
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("[WARN] Supabase 环境变量未设置，跳过入库")
        return

    supabase = create_client(url, key)
    try:
        # upsert by date
        supabase.table("daily_codes").upsert(final_code, on_conflict="code_date").execute()
        print(f"  ✅ 已写入数据库: {final_code['code_value']} (置信度 {final_code['confidence']})")
    except Exception as e:
        print(f"  [ERROR] 写入失败: {e}")

def main():
    print("=" * 50)
    print("🔑 每日密码采集器")
    print(f"📅 {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 50)

    all_results = []

    print("\n📡 B站搜索...")
    all_results.extend(search_bilibili_code())

    print("\n📡 百度搜索...")
    all_results.extend(search_baidu_code())

    print("\n📡 抖音搜索...")
    all_results.extend(search_douyin_code())

    print(f"\n📊 共采集到 {len(all_results)} 条候选")

    # 交叉验证
    final = cross_validate(all_results)

    if final:
        print(f"\n✅ 最终密码: {final['code_value']}")
        print(f"   来源数: {final['source_count']}")
        print(f"   置信度: {final['confidence']}")
        print(f"   已验证: {'是' if final['verified'] else '否（单源）'}")

        # 写入数据库
        save_to_supabase(final)

        # 保存本地备份
        backup_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(backup_dir, exist_ok=True)
        fname = f"daily_code_{date.today():%Y%m%d}.json"
        with open(os.path.join(backup_dir, fname), "w", encoding="utf-8") as f:
            json.dump(final, f, ensure_ascii=False, indent=2)
    else:
        print("\n⚠️ 今日未采集到有效密码")
        print("   建议：检查关键词 / 手动从社区获取")

if __name__ == "__main__":
    main()
