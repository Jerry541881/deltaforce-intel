#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三角洲行动 改枪码入库脚本
数据来源：游侠网 / 18183 / 3DM / NGA / 看个号 / deltagamehub / 微信公众号攻略 / 百度百科
全部为公开分享码，模式统一为「烽火地带」（与全面战场不互通）
每把枪 >= 4 条
"""
import os
import json
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "supabase_config.json")

MODE = "烽火地带"
SEASON = "S11"

# (枪名, 类型, 流派/描述, 改枪码, 来源)
DATA = [
    # ==================== 突击步枪 ====================
    ("M4A1", "突击步枪", "全能均衡满改·3倍战术镜·全地图通用", "6I57UD4080ELE0AQVMCG8", "威龙改枪"),
    ("M4A1", "突击步枪", "红点近战猛攻·冲楼贴脸专属", "6KLHGFK0BIGQQKR21AT1J", "威龙改枪"),
    ("M4A1", "突击步枪", "远距架枪满改·4倍精密镜·52米射程", "6KMF8H00BIGQQKR21AT1J", "威龙改枪"),
    ("M4A1", "突击步枪", "消音潜伏偷袭·老六隐蔽打法", "6I57UJ0080ELE0AQVMCG8", "威龙改枪"),
    ("M4A1", "突击步枪", "满改均衡·50米稳压·S10主流", "6KV8VB40DVV2IQEKG70I3", "游侠网/公众号"),
    ("M4A1", "突击步枪", "17万性价比之王·平民版本答案", "6HIK6V407G8S9A1C445HN", "18183"),
    ("M4A1", "突击步枪", "40.8万侦查5倍镜·312ms开镜·27%后座", "6JR6CM001GVPEAUQV7U8V", "今日头条"),

    ("AKM", "突击步枪", "27万满腰射·40米稳压", "6GMT6IK0B1P7JU7QB8KMM", "电玩帮"),
    ("AKM", "突击步枪", "27万中距离·机密/绝密巴克什", "6GMT6O80B1P7JU7QB8KMM", "电玩帮"),
    ("AKM", "突击步枪", "37万绝密满改·三倍镜", "6GMT6SO0B1P7JU7QB8KMM", "电玩帮"),
    ("AKM", "突击步枪", "18万纯粹丐版", "6KOT7FO0EU90O684D8QL5", "18183"),
    ("AKM", "突击步枪", "30万满改沙暴锚点", "6KOT8T80EU90O684D8QL5", "18183"),
    ("AKM", "突击步枪", "满改·金枪客提交方案", "6HJ7L7K09CDRQA7OLUPBA", "3DM"),

    ("K416", "突击步枪", "26万高性价比中配·近乎满后座控制", "6KS6SUK07FI7MVPVB9B3H", "VGTopup"),
    ("K416", "突击步枪", "35万高配A·30发偏稳定", "6KS6V7S07FI7MVPVB9B3H", "VGTopup"),
    ("K416", "突击步枪", "满腰射·100腰射精度·50米腰射百分百命中", "6KLS8DO06JIA63S9GM6T5", "18183"),
    ("K416", "突击步枪", "开镜腰射双修·蛛网制退器", "6JJEOEK0BNSV43TFRAQ1K", "微信公众号"),
    ("K416", "突击步枪", "18万性价比·新手零门槛", "6HIT3EK0BCHV462S8UUDS", "流雪游戏网"),
    ("K416", "突击步枪", "28万激光枪·50米内稳压", "6LDL5GG09U56JTCR74D0P", "今日头条"),

    ("K437", "突击步枪", "34万长枪管性价比版", "6LAEM6802G22C8LLI3CIN", "游侠网"),
    ("K437", "突击步枪", "40万长枪管三倍镜版", "6L6U1CO087UT56LJS9S2U", "游侠网"),
    ("K437", "突击步枪", "55万满改三倍镜版", "6L8M948087UT56LJS9S2U", "游侠网"),
    ("K437", "突击步枪", "60万手电顶配版", "6LAEO4K02G22C8LLI3CIN", "游侠网"),
    ("K437", "突击步枪", "62万满改·45发弹匣带3S手电", "6L73JQS0A5GUHBBBKSMNC", "NGA"),

    ("MDR", "突击步枪", "基础版·射程内小M7", "6LA8USG058UBUV9RKBGRG", "游侠网"),
    ("MDR", "突击步枪", "FFC满改版", "6L8V9DO0BNSV43TFRAQ1K", "游侠网"),
    ("MDR", "突击步枪", "多口径满改版", "6L8V9JG0BNSV43TFRAQ1K", "游侠网"),
    ("MDR", "突击步枪", "S11满改", "6LBIQ4O0AO21USGQ8AC2S", "今日头条"),

    # ==================== 冲锋枪 ====================
    ("MK4", "冲锋枪", "32万只开镜·三连发不上跳·后座63", "6L73KE00A5GUHBBBKSMNC", "游侠网/NGA"),
    ("MK4", "冲锋枪", "52-56万绝密双修满改·对抗5-6套甲", "6LA8LPO058UBUV9RKBGRG", "游侠网"),
    ("MK4", "冲锋枪", "蛛网制退器·贴脸以小博大·腰射90+", "6JJED900BNSV43TFRAQ1K", "微信公众号"),
    ("MK4", "冲锋枪", "绝密猛攻·腰射超模", "6KSQ7CO03JVRTS8O8552R", "18183"),
    ("MK4", "冲锋枪", "S11满改", "6LBICJC0AO21USGQ8AC2S", "今日头条"),

    ("MP7", "冲锋枪", "30万月影性价比·腰射开镜流", "6J2L2IS0E5QUTQP36HK9K", "看个号"),
    ("MP7", "冲锋枪", "50万满改·能腰射能打中距离", "6J2L2JO0E5QUTQP36HK9K", "看个号"),
    ("MP7", "冲锋枪", "23万月影丐版", "6J2L2K80E5QUTQP36HK9K", "看个号"),
    ("MP7", "冲锋枪", "35万60发大弹鼓版", "6J2L2KS0E5QUTQP36HK9K", "看个号"),
    ("MP7", "冲锋枪", "21万室内之王·950射速", "6GTIP4COAO21USGQ8AC2S", "微信公众号"),
    ("MP7", "冲锋枪", "S11满改", "6LBIM4K0AO21USGQ8AC2S", "今日头条"),

    ("MP5", "冲锋枪", "9万腰射100·修脚夺舍", "6J9884S0E5QUTQP36HK9K", "看个号"),
    ("MP5", "冲锋枪", "16万带爆闪+腰射", "6J9885O0E5QUTQP36HK9K", "看个号"),
    ("MP5", "冲锋枪", "35万三爆闪", "6J9886G0E5QUTQP36HK9K", "看个号"),
    ("MP5", "冲锋枪", "9万修脚夺舍首选", "6GTJ1440AO21USGQ8AC2S", "微信公众号"),
    ("MP5", "冲锋枪", "100腰射·近距离", "6H8OK3S0CN2U58NL2UJC9", "deltagamehub"),

    ("Vector", "冲锋枪", "58万开镜流", "6J6V9V40E5QUTQP36HK9K", "看个号"),
    ("Vector", "冲锋枪", "45万腰射·绝密航天", "6J6V9VO0E5QUTQP36HK9K", "看个号"),
    ("Vector", "冲锋枪", "28万腰射·绝密巴克什", "6J6VA0C0E5QUTQP36HK9K", "看个号"),
    ("Vector", "冲锋枪", "46万稳定开镜流", "6J6VA140E5QUTQP36HK9K", "看个号"),
    ("Vector", "冲锋枪", "36万性价比开镜", "6J6VA1S0E5QUTQP36HK9K", "看个号"),
    ("Vector", "冲锋枪", "17万室内贴脸·1091射速", "6GTIVDOOAO21USGQ8AC2S", "微信公众号"),

    ("QCQ171", "冲锋枪", "49万满改", "6J6V9QO0E5QUTQP36HK9K", "看个号"),
    ("QCQ171", "冲锋枪", "35万", "6J6V9RC0E5QUTQP36HK9K", "看个号"),
    ("QCQ171", "冲锋枪", "10万丐版修脚", "6J6V9S40E5QUTQP36HK9K", "看个号"),
    ("QCQ171", "冲锋枪", "25万暗影流性价比", "6J6V9SO0E5QUTQP36HK9K", "看个号"),
    ("QCQ171", "冲锋枪", "13万高伤害高射速·30米稳压", "6GTIEFOOAO21USGQ8AC2S", "微信公众号"),

    ("P90", "冲锋枪", "28万性价比·无后座带腰射", "6J1CUH00E5QUTQP36HK9K", "看个号"),
    ("P90", "冲锋枪", "40万满改带爆闪", "6J3KBEK0E5QUTQP36HK9K", "看个号"),
    ("P90", "冲锋枪", "18万性价比带腰射", "6J3KBF40E5QUTQP36HK9K", "看个号"),
    ("P90", "冲锋枪", "38万带腰射满改·先进多口消音", "6J3KBFO0E5QUTQP36HK9K", "看个号"),
    ("P90", "冲锋枪", "20万能开镜能腰射·50米稳压", "6GS63SCOAO21USGQ8AC2S", "微信公众号"),
    ("P90", "冲锋枪", "24万近战持久·自带50发弹匣", "6LDL6IG09U56JTCR74D0P", "今日头条"),

    ("UZI", "冲锋枪", "11万满改", "6IVBASS0E5QUTQP36HK9K", "看个号"),
    ("UZI", "冲锋枪", "6万性价比·腰射小弹夹", "6IVBATG0E5QUTQP36HK9K", "看个号"),
    ("UZI", "冲锋枪", "6万跑刀神器·消音大弹夹", "6IVBAU40E5QUTQP36HK9K", "看个号"),
    ("UZI", "冲锋枪", "8万腰射跑打", "6GTIU380AO21USGQ8AC2S", "微信公众号"),
    ("UZI", "冲锋枪", "腰射流", "6K7NK2C0AO21USGQ8AC2S", "微信公众号"),

    ("SMG-45", "冲锋枪", "30万腰射满改", "6J78F740E5QUTQP36HK9K", "看个号"),
    ("SMG-45", "冲锋枪", "11万满腰射性价比", "6J78FA80E5QUTQP36HK9K", "看个号"),
    ("SMG-45", "冲锋枪", "23万满改激光枪", "6J78FB00E5QUTQP36HK9K", "看个号"),
    ("SMG-45", "冲锋枪", "14万双修流", "6J78FBK0E5QUTQP36HK9K", "看个号"),
    ("SMG-45", "冲锋枪", "6万丐版", "6J78FCG0E5QUTQP36HK9K", "看个号"),
    ("SMG-45", "冲锋枪", "8万低配·近可腰射远能50米稳压", "6LCVSTS0CFGHPDGIHVI67", "视频攻略"),

    ("SR-3M", "紧凑突击步枪", "47万半改·可开镜可腰射", "6J3LNFO0E5QUTQP36HK9K", "看个号"),
    ("SR-3M", "紧凑突击步枪", "69万满改轮椅", "6J3LNG80E5QUTQP36HK9K", "看个号"),
    ("SR-3M", "紧凑突击步枪", "100腰射", "6J3LNGS0E5QUTQP36HK9K", "看个号"),
    ("SR-3M", "紧凑突击步枪", "23万性价比", "6J3LNHO0E5QUTQP36HK9K", "看个号"),
    ("SR-3M", "紧凑突击步枪", "麦晓雯女鬼流", "6J3LNIC0E5QUTQP36HK9K", "看个号"),
    ("SR-3M", "紧凑突击步枪", "30万近战闪击·12米腰射35米开镜", "6LDL6E009U56JTCR74D0P", "今日头条"),

    ("勇士", "冲锋枪", "16万满腰射", "6IVBAG80E5QUTQP36HK9K", "看个号"),
    ("勇士", "冲锋枪", "19万开镜穿甲流", "6J3LO8C0E5QUTQP36HK9K", "看个号"),
    ("勇士", "冲锋枪", "16万丐版最稳开镜", "6J3LO900E5QUTQP36HK9K", "看个号"),
    ("勇士", "冲锋枪", "26万腰射版+爆闪", "6J3LO9O0E5QUTQP36HK9K", "看个号"),
    ("勇士", "冲锋枪", "45万红点版", "6J3LOA80E5QUTQP36HK9K", "看个号"),
    ("勇士", "冲锋枪", "9万·50米内稳定压枪", "6GTIR880AO21USGQ8AC2S", "微信公众号"),

    ("汤姆逊", "冲锋枪", "丐版腰射", "6L8V45S0BNSV43TFRAQ1K", "游侠网"),
    ("汤姆逊", "冲锋枪", "满改开镜", "6L8V47O0BNSV43TFRAQ1K", "游侠网"),
    ("汤姆逊", "冲锋枪", "满改腰射", "6L8V4AK0BNSV43TFRAQ1K", "游侠网"),
    ("汤姆逊", "冲锋枪", "腰射开镜双修流派", "6LA8JN0058UBUV9RKBGRG", "游侠网"),
    ("汤姆逊", "冲锋枪", "开镜无后座版本", "6LA8JI8058UBUV9RKBGRG", "游侠网"),
    ("汤姆逊", "冲锋枪", "S11满改·先进枪身", "6L9TK040AO21USGQ8AC2S", "今日头条"),

    # ==================== 狙击 / 射手 ====================
    ("AWM", "狙击步枪", "115万终极版·全距离", "6K1AI6C0AI4S65CVSS3J1", "deltagamehub"),
    ("AWM", "狙击步枪", "高射程版", "6IK54DK0E5QUTQP36HK9K", "看个号"),
    ("AWM", "狙击步枪", "低射程版", "6IHLEV00E5QUTQP36HK9K", "看个号"),
    ("AWM", "狙击步枪", "3/7倍镜·45万", "6G940L008OPOB8QKQ72I8", "moming.work"),
    ("AWM", "狙击步枪", "S11满改", "6L996N00AO21USGQ8AC2S", "今日头条"),

    ("M700", "狙击步枪", "49万满改", "6J22C1C0E5QUTQP36HK9K", "看个号"),
    ("M700", "狙击步枪", "23万半改", "6J22C940E5QUTQP36HK9K", "看个号"),
    ("M700", "狙击步枪", "45万瞬狙", "6GPEAGC0CQ9J5LUV083F9", "moming.work"),
    ("M700", "狙击步枪", "HVK旋风新套件·栓狙变全自动", "6L6F40G00HV7Q7HR7NNCH", "微信公众号"),
    ("M700", "狙击步枪", "3/7镜·45万", "6G940TG08OPOB8QKQ72I8", "moming.work"),

    ("R93", "狙击步枪", "28万满改", "6IK4S0O0E5QUTQP36HK9K", "看个号"),
    ("R93", "狙击步枪", "13万丐版", "6IK4S1G0E5QUTQP36HK9K", "看个号"),
    ("R93", "狙击步枪", "21万红狼滑铲狙专用", "6LHDDOS03OCPBNPLQ4T6P", "微信公众号"),
    ("R93", "狙击步枪", "16万6倍消音低配", "6LHDED803OCPBNPLQ4T6P", "微信公众号"),
    ("R93", "狙击步枪", "3/7镜·23万", "6G940RC08OPOB8QKQ72I8", "moming.work"),
    ("R93", "狙击步枪", "29万·长弓溪谷蹲守", "6KJG5MO0AO21USGQ8AC2S", "电玩帮"),

    ("SV-98", "狙击步枪", "29万满改", "6IK4S2G0E5QUTQP36HK9K", "看个号"),
    ("SV-98", "狙击步枪", "14万丐版", "6IK4S3S0E5QUTQP36HK9K", "看个号"),
    ("SV-98", "狙击步枪", "3/7倍镜·22万", "6G940IC08OPOB8QKQ72I8", "moming.work"),
    ("SV-98", "狙击步枪", "13万以小博大·跑狙专用", "6K0VHKG08B3NQ47C8F9H7", "微信公众号"),
    ("SV-98", "狙击步枪", "28万超远射程·远距离架枪", "6H0PFB80FIAS4OUQQ081T", "微信公众号"),
    ("SV-98", "狙击步枪", "17万·中距离peek对枪", "6KJG6RO0AO21USGQ8AC2S", "电玩帮"),

    ("SR-25", "射手步枪", "72万稳压版·射程130", "6K0O4EO0E8BGRBKVBDER1", "deltagamehub"),
    ("SR-25", "射手步枪", "65万稳定速射流", "6GT83BC03EINQ63AGU05N", "moming.work"),
    ("SR-25", "射手步枪", "60万37架点", "6GT83IO03EINQ63AGU05N", "moming.work"),
    ("SR-25", "射手步枪", "69万中距连狙", "6HR7FR80817N6Y7WZ29K", "微信公众号"),
    ("SR-25", "射手步枪", "S11满改", "6LBABKS0AO21USGQ8AC2S", "今日头条"),

    # ==================== 机枪 ====================
    ("PKM", "通用机枪", "满改长枪管", "6J2AKS00E5QUTQP36HK9K", "看个号"),
    ("PKM", "通用机枪", "满腰射+开镜无后座·短枪管满改", "6J2AKUS0E5QUTQP36HK9K", "看个号"),
    ("PKM", "通用机枪", "金枪客提交方案", "6HJ7LC009CDRQA7OLUPBA", "3DM"),
    ("PKM", "通用机枪", "实战推荐", "6HJ7LFS09CDRQA7OLUPBA", "3DM"),
    ("PKM", "通用机枪", "S11满改", "6LBIEFC0AO21USGQ8AC2S", "今日头条"),
]


def main():
    cfg_path = CONFIG_PATH
    if not os.path.exists(cfg_path):
        # 兼容：scripts 目录下
        alt = os.path.join(os.path.dirname(BASE_DIR), "scripts", "supabase_config.json")
        if os.path.exists(alt):
            cfg_path = alt
        else:
            print("找不到 supabase_config.json")
            return 1

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    url = (cfg.get("url") or "").rstrip("/")
    key = cfg.get("key") or ""
    if not url or not key:
        print("配置缺少 url 或 key")
        return 1

    try:
        import requests
    except ImportError:
        print("缺少 requests 库，请先 pip install requests")
        return 1

    payload = [
        {
            "gun_name": g,
            "gun_type": t,
            "build_name": b,
            "share_code": c,
            "mode": MODE,
            "season": SEASON,
            "source": s,
        }
        for (g, t, b, c, s) in DATA
    ]

    # 统计
    stat = {}
    for p in payload:
        stat[p["gun_name"]] = stat.get(p["gun_name"], 0) + 1

    print("=" * 50)
    print(f"共 {len(payload)} 条，覆盖 {len(stat)} 把枪")
    print("-" * 50)
    for k in sorted(stat, key=lambda x: -stat[x]):
        flag = "OK " if stat[k] >= 4 else "!! "
        print(f"  {flag}{k}: {stat[k]} 条")
    print("=" * 50)

    api = f"{url}/rest/v1/gun_codes"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,on_conflict=gun_name,build_name,mode,season,return=minimal",
    }

    try:
        r = requests.post(api, headers=headers, json=payload, timeout=40)
        if r.status_code in (200, 201, 204):
            print(f"上传成功: 共 {len(payload)} 条")
            return 0
        print(f"POST {r.status_code}: {r.text[:400]}")
        if r.status_code == 404:
            print("\n表 gun_codes 不存在，请先在 Supabase SQL Editor 执行建表语句")
        return 1
    except Exception as e:
        print(f"上传异常: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
