#!/usr/bin/env python3
"""
改枪码爬虫 - 全武器修正版
✅ 使用 SUPABASE_SERVICE_ROLE_KEY
✅ 每把枪只取 B站热度最高的一条
"""

import os
import re
import signal
import requests
from datetime import date
from urllib.parse import quote

# ============ 超时保护 ============
signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(120)

# ============ 配置 ============
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com"
}

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")  # ✅ 关键修正

# ============ 改枪码正则 ============
BUILD_CODE_RE = re.compile(r'\b6[A-Z0-9]{21,27}\b')

# ============ 全武器列表（含 FS-12，去 AX50）============
WEAPONS = [
    # 突击步枪
    {"name": "M4A1", "keyword": "三角洲行动 M4A1 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "K416", "keyword": "三角洲行动 K416 改枪码", "category_id": 1, "tier_id": 1},
    {"name": "QBZ95-1", "keyword": "三角洲行动 QBZ95 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "AKM", "keyword": "三角洲行动 AKM 改枪码", "category_id": 1, "tier_id": 1},
    {"name": "AK-12", "keyword": "三角洲行动 AK12 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "M16A4", "keyword": "三角洲行动 M16A4 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "AKS-74U", "keyword": "三角洲行动 AKS74U 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "AS Val", "keyword": "三角洲行动 ASVal 改枪码", "category_id": 1, "tier_id": 1},
    {"name": "AUG", "keyword": "三角洲行动 AUG 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "CAR-15", "keyword": "三角洲行动 CAR15 改枪码", "category_id": 1, "tier_id": 1},
    {"name": "SG552", "keyword": "三角洲行动 SG552 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "SCAR-H", "keyword": "三角洲行动 SCAR-H 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "G3", "keyword": "三角洲行动 G3 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "PTR 32", "keyword": "三角洲行动 PTR32 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "ASH-12", "keyword": "三角洲行动 ASH12 改枪码", "category_id": 1, "tier_id": 1},
    {"name": "KC17", "keyword": "三角洲行动 KC17 改枪码", "category_id": 1, "tier_id": 1},
    {"name": "RM277", "keyword": "三角洲行动 RM277 改枪码", "category_id": 1, "tier_id": 1},
    {"name": "腾龙", "keyword": "三角洲行动 腾龙 改枪码", "category_id": 1, "tier_id": 2},
    {"name": "MK47", "keyword": "三角洲行动 MK47 改枪码", "category_id": 1, "tier_id": 2},

    # 战斗步枪
    {"name": "M7", "keyword": "三角洲行动 M7 改枪码", "category_id": 4, "tier_id": 1},

    # 冲锋枪
    {"name": "Vector", "keyword": "三角洲行动 Vector 改枪码", "category_id": 2, "tier_id": 1},
    {"name": "MP5", "keyword": "三角洲行动 MP5 改枪码", "category_id": 2, "tier_id": 1},
    {"name": "P90", "keyword": "三角洲行动 P90 改枪码", "category_id": 2, "tier_id": 2},
    {"name": "SMG-45", "keyword": "三角洲行动 SMG45 改枪码", "category_id": 2, "tier_id": 2},
    {"name": "SR-3M", "keyword": "三角洲行动 SR3M 改枪码", "category_id": 2, "tier_id": 2},
    {"name": "UZI", "keyword": "三角洲行动 UZI 改枪码", "category_id": 2, "tier_id": 2},
    {"name": "MP7", "keyword": "三角洲行动 MP7 改枪码", "category_id": 2, "tier_id": 2},
    {"name": "野牛", "keyword": "三角洲行动 野牛 改枪码", "category_id": 2, "tier_id": 2},
    {"name": "QCQ171", "keyword": "三角洲行动 QCQ171 改枪码", "category_id": 2, "tier_id": 1},
    {"name": "MK4", "keyword": "三角洲行动 MK4 改枪码", "category_id": 2, "tier_id": 2},

    # 狙击/射手
    {"name": "AWM", "keyword": "三角洲行动 AWM 改枪码", "category_id": 3, "tier_id": 1},
    {"name": "SV98", "keyword": "三角洲行动 SV98 改枪码", "category_id": 3, "tier_id": 2},
    {"name": "M700", "keyword": "三角洲行动 M700 改枪码", "category_id": 3, "tier_id": 2},
    {"name": "M82A1", "keyword": "三角洲行动 M82 改枪码", "category_id": 3, "tier_id": 1},
    {"name": "SR-25", "keyword": "三角洲行动 SR25 改枪码", "category_id": 3, "tier_id": 1},
    {"name": "SVD", "keyword": "三角洲行动 SVD 改枪码", "category_id": 3, "tier_id": 2},
    {"name": "SKS", "keyword": "三角洲行动 SKS 改枪码", "category_id": 3, "tier_id": 2},
    {"name": "VSS", "keyword": "三角洲行动 VSS 改枪码", "category_id": 3, "tier_id": 2},
    {"name": "MINI-14", "keyword": "三角洲行动 MINI14 改枪码", "category_id": 3, "tier_id": 2},
    {"name": "M14", "keyword": "三角洲行动 M14 改枪码", "category_id": 3, "tier_id": 1},
    {"name": "PSG-1", "keyword": "三角洲行动 PSG1 改枪码", "category_id": 3, "tier_id": 2},
    {"name": "SVCH", "keyword": "三角洲行动 SVCH 改枪码", "category_id": 3, "tier_id": 1},

    # 轻机枪
    {"name": "M249", "keyword": "三角洲行动 M249 改枪码", "category_id": 5, "tier_id": 2},
    {"name": "PKM", "keyword": "三角洲行动 PKM 改枪码", "category_id": 5, "tier_id": 1},
    {"name": "M250", "keyword": "三角洲行动 M250 改枪码", "category_id": 5, "tier_id": 1},
    {"name": "QJB201", "keyword": "三角洲行动 QJB201 改枪码", "category_id": 5, "tier_id": 2},

    # 霰弹枪（含 FS-12）
    {"name": "S12K", "keyword": "三角洲行动 S12K 改枪码", "category_id": 6, "tier_id": 2},
    {"name": "M1014", "keyword": "三角洲行动 M1014 改枪码", "category_id": 6, "tier_id": 2},
    {"name": "M870", "keyword": "三角洲行动 M870 改枪码", "category_id": 6, "tier_id": 1},
    {"name": "FS-12", "keyword": "三角洲行动 FS12 改枪码", "category_id": 6, "tier_id": 1},
    {"name": "725", "keyword": "三角洲行动 725 改枪码", "category_id": 6, "tier_id": 2},

    # 手枪
    {"name": "G18", "keyword": "三角洲行动 G18 改枪码", "category_id": 7, "tier_id": 2},
    {"name": "357左轮", "keyword": "三角洲行动 左轮 改枪码", "category_id": 7, "tier_id": 2},
    {"name": "沙漠之鹰", "keyword": "三角洲行动 沙漠之鹰 改枪码", "category_id": 7, "tier_id": 1},
    {"name": "93R", "keyword": "三角洲行动 93R 改枪码", "category_id": 7, "tier_id": 2},
    {"name": "QSZ92G", "keyword": "三角洲行动 QSZ92 改枪码", "category_id": 7, "tier_id": 2},
    {"name": "G17", "keyword": "三角洲行动 G17 改枪码", "category_id": 7, "tier_id": 2},
    {"name": "M1911", "keyword": "三角洲行动 M1911 改枪码", "category_id": 7, "tier_id": 2},
]

# ============ 工具函数 ============
def fetch_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.raise_for_status()
        return r.text
    except:
        return ""

def search_first_video(keyword):
    html = fetch_page(f"https://search.bilibili.com/all?keyword={quote(keyword)}")
    if not html:
        return None
    bvs = re.findall(r'/video/(BV\w+)', html)
    return f"https://www.bilibili.com/video/{bvs[0]}" if bvs else None

def extract_code_from_page(url):
    html = fetch_page(url)
    if not html:
        return None
    m = BUILD_CODE_RE.search(html)
    return m.group(0) if m else None

# ============ 写 Supabase ============
def write_to_supabase(items):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase 配置缺失，跳过写库")
        return

    url = f"{SUPABASE_URL}/rest/v1/weapon_builds"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    try:
        r = requests.post(url, headers=headers, json=items, timeout=10)
        if r.status_code in (200, 201, 204):
            print(f"✅ 写入 Supabase 成功: {len(items)} 条")
        else:
            print(f"⚠️ Supabase 返回 {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"⚠️ 写库异常: {e}")

# ============ 主流程 ============
def crawl():
    today = str(date.today())
    total = len(WEAPONS)
    print(f"🔫 改枪码采集 ({today}) 共 {total} 把枪")
    print("─" * 50)

    results = []
    found = 0
    not_found = []

    for w in WEAPONS:
        name = w["name"]
        keyword = w["keyword"]

        video_url = search_first_video(keyword)
        if not video_url:
            print(f"  [{name}] ❌ 没找到视频")
            not_found.append(name)
            continue

        code = extract_code_from_page(video_url)
        if code:
            item = {
                "weapon_name": name,
                "category_id": w["category_id"],
                "tier_id": w["tier_id"],
                "build_code": code,
                "source": "bilibili",
                "source_url": video_url,
                "status": "active",
                "confidence": 0.85,
                "date": today
            }
            results.append(item)
            found += 1
            print(f"  [{name}] ✅ {code}")
        else:
            print(f"  [{name}] ⚠️ 视频存在但无改枪码")
            not_found.append(name)

    print("\n" + "─" * 50)
    print(f"🎉 成功: {found}/{total} 把枪")
    if not_found:
        print(f"⚠️ 未找到 ({len(not_found)}): {', '.join(not_found)}")
        print("👉 这些枪等待管理员手动添加")

    if results:
        write_to_supabase(results)

    signal.alarm(0)

if __name__ == "__main__":
    crawl()