"""
同步脚本 —— 把采集到的 JSON 数据写入 Supabase
"""
import os
import sys
import json
import glob
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

CATEGORY_MAP = {
    "突击步枪": 1, "冲锋枪": 2, "狙击枪": 3,
    "战斗步枪": 4, "轻机枪": 5, "霰弹枪": 6, "手枪": 7,
}
TIER_MAP = {"T0": 1, "T1": 2, "T2": 3}
MAP_MAP = {"零号大坝": 1, "航天基地": 2, "巴克什": 3, "终极战场": 4}

def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase 环境变量未设置！请检查 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def load_latest_json(prefix: str) -> dict | None:
    """加载最新的某个前缀的 JSON 文件"""
    pattern = os.path.join(DATA_DIR, f"{prefix}_*.json")
    files = glob.glob(pattern)
    if not files:
        print(f"  [WARN] 没有找到 {prefix}_*.json 文件")
        return None
    latest = max(files, key=os.path.getmtime)
    print(f"  📂 加载: {os.path.basename(latest)}")
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)

def sync_builds(supabase, data: dict):
    """同步改枪码"""
    builds = data.get("builds", [])
    if not builds:
        print("  ⏭️ 无改枪码数据")
        return

    inserted = 0
    for b in builds:
        weapon_name = b.get("weapon_name", "")
        cat_name = b.get("category", "")
        tier_name = b.get("tier", "T1")

        record = {
            "weapon_name": weapon_name,
            "category_id": CATEGORY_MAP.get(cat_name, 4),  # 默认战斗步枪
            "tier_id": TIER_MAP.get(tier_name, 2),
            "build_code": b.get("build_code", ""),
            "title": b.get("title", ""),
            "description": b.get("description", ""),
            "source_url": b.get("source_url", ""),
            "source_platform": b.get("source_platform", ""),
            "author": b.get("author", ""),
            "tags": b.get("tags", []),
            "confidence_score": b.get("confidence", 0.5),
            "status": "published" if b.get("confidence", 0.5) >= 0.6 else "pending",
        }

        try:
            supabase.table("weapon_builds").upsert(record, on_conflict="build_code").execute()
            inserted += 1
        except Exception as e:
            print(f"    [WARN] 插入失败 {weapon_name}: {e}")

    print(f"  ✅ 改枪码入库: {inserted}/{len(builds)}")

def sync_routes(supabase, data: dict):
    """同步跑刀路线"""
    routes = data.get("routes", [])
    if not routes:
        print("  ⏭️ 无路线数据")
        return

    inserted = 0
    for r in routes:
        map_name = r.get("map_name", "")
        record = {
            "map_id": MAP_MAP.get(map_name, 1),
            "title": r.get("title", ""),
            "difficulty": r.get("difficulty", "medium"),
            "expected_loot": r.get("expected_loot", ""),
            "risk_level": r.get("risk_level", "medium"),
            "steps": r.get("steps", []),
            "video_url": r.get("source_url", ""),
            "author": r.get("author", ""),
            "source_url": r.get("source_url", ""),
            "confidence_score": r.get("confidence", 0.5),
            "status": "published" if r.get("confidence", 0.5) >= 0.6 else "pending",
        }
        try:
            supabase.table("route_guides").upsert(record, on_conflict="title").execute()
            inserted += 1
        except Exception as e:
            print(f"    [WARN] 插入失败: {e}")

    print(f"  ✅ 路线入库: {inserted}/{len(routes)}")

def sync_operators(supabase, data: dict):
    """同步干员分析"""
    operators = data.get("operators", [])
    if not operators:
        print("  ⏭️ 无干员数据")
        return

    inserted = 0
    for o in operators:
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
            "analysis_text": o.get("analysis", ""),
            "version": o.get("version", "current"),
            "source_urls": [o.get("source_url", "")],
            "confidence_score": o.get("confidence", 0.5),
            "status": "published" if o.get("confidence", 0.5) >= 0.6 else "draft",
        }
        try:
            supabase.table("operator_analysis").upsert(record, on_conflict="operator_name").execute()
            inserted += 1
        except Exception as e:
            print(f"    [WARN] 插入失败: {e}")

    print(f"  ✅ 干员入库: {inserted}/{len(operators)}")

def main():
    print("=" * 50)
    print("📤 数据同步 → Supabase")
    print(f"⏰ {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 50)

    try:
        supabase = get_supabase()
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # 加载 B站数据
    print("\n📦 处理 B站数据...")
    bili_data = load_latest_json("bilibili")
    if bili_data:
        sync_builds(supabase, bili_data)
        sync_routes(supabase, bili_data)
        sync_operators(supabase, bili_data)

    # 加载短视频数据
    print("\n📦 处理短视频数据...")
    sv_data = load_latest_json("shortvideo")
    if sv_data:
        sync_builds(supabase, sv_data)
        sync_routes(supabase, sv_data)
        sync_operators(supabase, sv_data)

    print("\n🎉 同步完成！")

if __name__ == "__main__":
    main()
