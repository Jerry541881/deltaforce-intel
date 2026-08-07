"""
三角洲行动 - 全武器数据
唯一数据源，crawler_bilibili.py 从这里读取
共 58 把枪，7 大分类

category_id 映射:
  1 = 突击步枪
  2 = 冲锋枪
  3 = 狙击/射手步枪
  4 = 战斗步枪
  5 = 轻机枪
  6 = 霰弹枪
  7 = 手枪

tier_id 映射:
  1 = T0/T1 主流
  2 = T2/T3 可选
"""

WEAPONS = [
    # ============ 突击步枪 (19把) ============
    {"name": "M4A1",    "keyword": "三角洲行动 M4A1 改枪码",    "category_id": 1, "tier_id": 2},
    {"name": "K416",    "keyword": "三角洲行动 K416 改枪码",    "category_id": 1, "tier_id": 1},
    {"name": "QBZ95-1", "keyword": "三角洲行动 QBZ95 改枪码",   "category_id": 1, "tier_id": 2},
    {"name": "AKM",     "keyword": "三角洲行动 AKM 改枪码",     "category_id": 1, "tier_id": 1},
    {"name": "AK-12",   "keyword": "三角洲行动 AK12 改枪码",    "category_id": 1, "tier_id": 2},
    {"name": "M16A4",   "keyword": "三角洲行动 M16A4 改枪码",   "category_id": 1, "tier_id": 2},
    {"name": "AKS-74U", "keyword": "三角洲行动 AKS74U 改枪码",  "category_id": 1, "tier_id": 2},
    {"name": "AS Val",  "keyword": "三角洲行动 ASVal 改枪码",   "category_id": 1, "tier_id": 1},
    {"name": "AUG",     "keyword": "三角洲行动 AUG 改枪码",     "category_id": 1, "tier_id": 2},
    {"name": "CAR-15",  "keyword": "三角洲行动 CAR15 改枪码",   "category_id": 1, "tier_id": 1},
    {"name": "SG552",   "keyword": "三角洲行动 SG552 改枪码",    "category_id": 1, "tier_id": 2},
    {"name": "SCAR-H",  "keyword": "三角洲行动 SCAR-H 改枪码",  "category_id": 1, "tier_id": 2},
    {"name": "G3",      "keyword": "三角洲行动 G3 改枪码",      "category_id": 1, "tier_id": 2},
    {"name": "PTR 32",  "keyword": "三角洲行动 PTR32 改枪码",   "category_id": 1, "tier_id": 2},
    {"name": "ASH-12",  "keyword": "三角洲行动 ASH12 改枪码",   "category_id": 1, "tier_id": 1},
    {"name": "KC17",    "keyword": "三角洲行动 KC17 改枪码",    "category_id": 1, "tier_id": 1},
    {"name": "RM277",   "keyword": "三角洲行动 RM277 改枪码",   "category_id": 1, "tier_id": 1},
    {"name": "腾龙",     "keyword": "三角洲行动 腾龙 改枪码",     "category_id": 1, "tier_id": 2},
    {"name": "MK47",    "keyword": "三角洲行动 MK47 改枪码",    "category_id": 1, "tier_id": 2},

    # ============ 战斗步枪 (1把) ============
    {"name": "M7",      "keyword": "三角洲行动 M7 改枪码",      "category_id": 4, "tier_id": 1},

    # ============ 冲锋枪 (10把) ============
    {"name": "Vector",  "keyword": "三角洲行动 Vector 改枪码",   "category_id": 2, "tier_id": 1},
    {"name": "MP5",     "keyword": "三角洲行动 MP5 改枪码",     "category_id": 2, "tier_id": 1},
    {"name": "P90",     "keyword": "三角洲行动 P90 改枪码",     "category_id": 2, "tier_id": 2},
    {"name": "SMG-45",  "keyword": "三角洲行动 SMG45 改枪码",   "category_id": 2, "tier_id": 2},
    {"name": "SR-3M",   "keyword": "三角洲行动 SR3M 改枪码",    "category_id": 2, "tier_id": 2},
    {"name": "UZI",     "keyword": "三角洲行动 UZI 改枪码",     "category_id": 2, "tier_id": 2},
    {"name": "MP7",     "keyword": "三角洲行动 MP7 改枪码",     "category_id": 2, "tier_id": 2},
    {"name": "野牛",     "keyword": "三角洲行动 野牛 改枪码",     "category_id": 2, "tier_id": 2},
    {"name": "QCQ171",  "keyword": "三角洲行动 QCQ171 改枪码",  "category_id": 2, "tier_id": 1},
    {"name": "MK4",     "keyword": "三角洲行动 MK4 改枪码",     "category_id": 2, "tier_id": 2},

    # ============ 狙击步枪 (4把) ============
    {"name": "AWM",     "keyword": "三角洲行动 AWM 改枪码",     "category_id": 3, "tier_id": 1},
    {"name": "SV98",    "keyword": "三角洲行动 SV98 改枪码",    "category_id": 3, "tier_id": 2},
    {"name": "M700",    "keyword": "三角洲行动 M700 改枪码",    "category_id": 3, "tier_id": 2},
    {"name": "M82A1",   "keyword": "三角洲行动 M82 改枪码",     "category_id": 3, "tier_id": 1},

    # ============ 射手步枪 (8把) ============
    {"name": "SR-25",   "keyword": "三角洲行动 SR25 改枪码",   "category_id": 3, "tier_id": 1},
    {"name": "SVD",     "keyword": "三角洲行动 SVD 改枪码",     "category_id": 3, "tier_id": 2},
    {"name": "SKS",     "keyword": "三角洲行动 SKS 改枪码",     "category_id": 3, "tier_id": 2},
    {"name": "VSS",     "keyword": "三角洲行动 VSS 改枪码",     "category_id": 3, "tier_id": 2},
    {"name": "MINI-14", "keyword": "三角洲行动 MINI14 改枪码",  "category_id": 3, "tier_id": 2},
    {"name": "M14",     "keyword": "三角洲行动 M14 改枪码",     "category_id": 3, "tier_id": 1},
    {"name": "PSG-1",   "keyword": "三角洲行动 PSG1 改枪码",    "category_id": 3, "tier_id": 2},
    {"name": "SVCH",    "keyword": "三角洲行动 SVCH 改枪码",    "category_id": 3, "tier_id": 1},

    # ============ 轻机枪 (4把) ============
    {"name": "M249",    "keyword": "三角洲行动 M249 改枪码",    "category_id": 5, "tier_id": 2},
    {"name": "PKM",     "keyword": "三角洲行动 PKM 改枪码",     "category_id": 5, "tier_id": 1},
    {"name": "M250",    "keyword": "三角洲行动 M250 改枪码",    "category_id": 5, "tier_id": 1},
    {"name": "QJB201",  "keyword": "三角洲行动 QJB201 改枪码",  "category_id": 5, "tier_id": 2},

    # ============ 霰弹枪 (5把) ============
    {"name": "S12K",    "keyword": "三角洲行动 S12K 改枪码",    "category_id": 6, "tier_id": 2},
    {"name": "M1014",   "keyword": "三角洲行动 M1014 改枪码",   "category_id": 6, "tier_id": 2},
    {"name": "M870",    "keyword": "三角洲行动 M870 改枪码",    "category_id": 6, "tier_id": 1},
    {"name": "FS-12",   "keyword": "三角洲行动 FS12 改枪码",    "category_id": 6, "tier_id": 1},
    {"name": "725",     "keyword": "三角洲行动 725 改枪码",     "category_id": 6, "tier_id": 2},

    # ============ 手枪 (7把) ============
    {"name": "G18",        "keyword": "三角洲行动 G18 改枪码",        "category_id": 7, "tier_id": 2},
    {"name": "357左轮",    "keyword": "三角洲行动 左轮 改枪码",      "category_id": 7, "tier_id": 2},
    {"name": "沙漠之鹰",   "keyword": "三角洲行动 沙漠之鹰 改枪码",  "category_id": 7, "tier_id": 1},
    {"name": "93R",        "keyword": "三角洲行动 93R 改枪码",        "category_id": 7, "tier_id": 2},
    {"name": "QSZ92G",     "keyword": "三角洲行动 QSZ92 改枪码",     "category_id": 7, "tier_id": 2},
    {"name": "G17",        "keyword": "三角洲行动 G17 改枪码",        "category_id": 7, "tier_id": 2},
    {"name": "M1911",      "keyword": "三角洲行动 M1911 改枪码",     "category_id": 7, "tier_id": 2},
]
