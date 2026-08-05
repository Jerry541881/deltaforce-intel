"""
干员分析采集 —— 每3个月运行一次
采集 + AI 汇总 + 写入 Supabase
"""
import os
import sys
import json
import time
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.ai_extractor import extract_operators

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}

OPERATORS = [
    "蜂鸟", "特克", "索菲亚", "乌尔班", "雷恩",
    "泰瑞", "金卢娜", "凯尔", "诺亚", "星夜"
]

def search_bilibili_operator(name: str) -> list[dict]:
    """搜索某个干员的攻略视频"""
    results = []
    keywords = [f"三角洲行动{name}干员", f"三角洲行动{name}攻略"]
    for kw in keywords:
        url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={kw}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            data = resp.json()
            for item in data.get("data", {}).get("result", []):
                if item.get("result_type") == "video":
                    for v in item.get("data", []):
                        desc = v.get("description", "")
                        title = v.get("title", "")
                        full = f"{title} {desc}"
                        results.append({
                            "text": full,
                            "url": f"https://www.bilibili.com/video/{v.get('bvid','')}",
                            "author": v.get("author", ""),
                        })
            time.sleep(1)
        except Exception as e:
            print(f"  [WARN] {kw} 失败: {e}")
    return results

def main():
    print("=" * 50)
    print("🎮 干员分析采集器（季度更新）")
    print(f"⏰ {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 50)

    all_operators = []

    for name in OPERATORS:
        print(f"\n🔍 采集干员: {name}")
        items = search_bilibili_operator(name)

        combined_text = ""
        urls = []
        for item in items[:10]:
            combined_text += item["text"] + "\n"
            urls.append(item["url"])

        if combined_text:
            ops = extract_operators(combined_text[:5000])
            for o in ops:
                o["source_url"] = urls[0] if urls else ""
                o["source_urls"] = urls[:5]
                o["operator_name"] = o.get("operator_name") or name
                all_operators.append(o)
            print(f"  ✅ 提取到 {len(ops)} 条分析")
        else:
            print(f"  ⏭️ 无数据")

        time.sleep(2)

    # 写入 Supabase
    from supabase import create_client
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if url and key:
        supabase = create_client(url, key)
        for o in all_operators:
            record = {
                "operator_name": o.get("operator_name", ""),
                "role": o.get("role", ""),
                "overall_rating": o.get("overall_rating", 5.0),
                "strengths": o.get("strengths", []),
                "weaknesses": o.get("weaknesses", []),
                "best_maps": o.get("best_maps", []),
                "best_weapons": o.get("best_weapons", []),
                "playstyle": o.get("playstyle", ""),
                "tips": o.get("tips", ""),
                "analysis_text": o.get("analysis_text", ""),
                "version": "S10",
                "source_urls": o.get("source_urls", []),
                "confidence_score": o.get("confidence", 0.6),
                "status": "published",
            }
            try:
                supabase.table("operator_analysis").upsert(record, on_conflict="operator_name").execute()
            except Exception as e:
                print(f"  [WARN] {o.get('operator_name')} 写入失败: {e}")
        print(f"\n🎉 共写入 {len(all_operators)} 条干员分析")

    # 本地备份
    backup_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(backup_dir, exist_ok=True)
    fname = f"operators_{datetime.now():%Y%m%d}.json"
    with open(os.path.join(backup_dir, fname), "w", encoding="utf-8") as f:
        json.dump(all_operators, f, ensure_ascii=False, indent=2)
    print(f"💾 备份: {fname}")

if __name__ == "__main__":
    main()
