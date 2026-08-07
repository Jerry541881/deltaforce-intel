"""
每日密码爬虫 - 极简版
B站搜不到就安静退出，等管理员手动加
"""

import os, re, json, signal, requests
from datetime import date
from urllib.parse import quote

signal.signal(signal.SIGALRM, lambda s, f: os._exit(0))
signal.alarm(120)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com"
}

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.raise_for_status()
        return r.text
    except:
        return ""

def crawl_bilibili_today(today):
    html = fetch(f"https://search.bilibili.com/all?keyword={quote('三角洲行动 今日密码')}")
    if not html:
        return None

    bvs = re.findall(r'/video/(BV\w+)', html)
    if not bvs:
        return None

    url = f"https://www.bilibili.com/video/{bvs[0]}"
    page = fetch(url)
    if not page:
        return None

    m = re.search(r'(今天|今日).{0,15}?(\d{4})', page)
    return m.group(2) if m else None

def write_to_supabase(code, today_str):
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL 未配置")
        return
    if not SUPABASE_KEY:
        print("❌ SUPABASE_SERVICE_ROLE_KEY 未配置")
        print("   请在 GitHub Settings → Secrets 中配置 SUPABASE_SERVICE_ROLE_KEY")
        return

    url = f"{SUPABASE_URL}/rest/v1/daily_codes"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    data = [{
        "code_date": today_str,
        "code_value": code,
        "verified": True,
        "source": "bilibili"
    }]

    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"📤 Supabase 返回状态码: {r.status_code}")
        if r.status_code in (200, 201, 204):
            print(f"✅ 写入 Supabase 成功: {code}")
        else:
            print(f"⚠️ Supabase 返回错误: {r.status_code}")
            print(f"   返回内容: {r.text[:300]}")
    except Exception as e:
        print(f"⚠️ 写库异常: {e}")

def crawl():
    today = date.today().strftime("%Y-%m-%d")
    print(f"🗓️ 采集 {today} 每日密码")

    code = crawl_bilibili_today(today)
    if code:
        print(f"✅ B站找到今日密码: {code}")
        write_to_supabase(code, today)
    else:
        print("❌ B站未找到今日密码")
        print("👉 请在 Supabase 手动添加")

    signal.alarm(0)

if __name__ == "__main__":
    crawl()