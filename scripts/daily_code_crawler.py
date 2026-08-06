#!/usr/bin/env python3
"""
每日密码爬虫
支持多源采集 + AI 提取 + 交叉验证
"""

import os
import json
import time
import hashlib
import requests
from datetime import date
from bs4 import BeautifulSoup

# ========= 配置 =========
BAIDU_URL = "https://www.baidu.com/s?wd=三角洲行动今日密码"
DOUYIN_SEARCH = "https://www.douyin.com/search/三角洲行动今日密码"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")


# ========= 工具函数 =========
def md5(text):
    return hashlib.md5(text.encode()).hexdigest()


def fetch_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return ""


def extract_with_ai(html, source):
    """调用智谱 AI 提取密码（兜底用）"""
    if not ZHIPU_API_KEY:
        return []

    prompt = f"""
你是一个《三角洲行动》攻略助手。
从下面网页内容中提取今日（{date.today()}）的每日密码信息。
返回 JSON 数组，每项包含：code, date, map, source。
只返回 JSON，不要解释。

网页内容：
{html[:8000]}
"""
    try:
        # 示例：智谱 GLM-4 调用，实际按你原脚本调整
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Authorization": f"Bearer {ZHIPU_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "glm-4-flash",
            "messages": [{"role": "user", "content": prompt}]
        }
        r = requests.post(url, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        result = r.json()
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
        return []


def parse_baidu(html):
    results = []
    soup = BeautifulSoup(html, "html.parser")

    for item in soup.select("div.result, div.c-container"):
        text = item.get_text(" ", strip=True)
        if "密码" not in text:
            continue

        code = None
        for word in text.split():
            if word.isdigit() and len(word) == 4:
                code = word
                break

        if code:
            results.append({
                "code": code,
                "date": str(date.today()),
                "map": "",
                "source": "baidu"
            })
    return results


def parse_douyin(html):
    results = []
    soup = BeautifulSoup(html, "html.parser")

    for item in soup.select("span, div"):
        text = item.get_text(" ", strip=True)
        if "密码" not in text:
            continue

        code = None
        for word in text.split():
            if word.isdigit() and len(word) == 4:
                code = word
                break

        if code:
            results.append({
                "code": code,
                "date": str(date.today()),
                "map": "",
                "source": "douyin"
            })
    return results


# ========= 交叉验证（核心修复点）=========
def cross_validate(all_results):
    if not all_results:
        return None

    # ✅ 先过滤空 code，防止 None.strip() 崩溃
    valid_inputs = []
    for r in all_results:
        code = (r.get("code") or "").strip()
        if not code:
            continue
        valid_inputs.append(r)

    if not valid_inputs:
        return None

    groups = {}
    for r in valid_inputs:
        code = (r.get("code") or "").strip()
        d = (r.get("date") or "").strip()
        m = (r.get("map") or "").strip()
        src = (r.get("source") or "").strip()

        key = f"{d}|{code}"
        if key not in groups:
            groups[key] = {
                "code": code,
                "date": d,
                "map": m,
                "sources": [],
                "confidence": 0.5
            }
        groups[key]["sources"].append(src)

    best = None
    best_score = -1

    for item in groups.values():
        score = len(set(item["sources"])) * 0.3 + 0.5
        if item["code"].isdigit() and len(item["code"]) == 4:
            score += 0.2
        item["confidence"] = min(score, 1.0)

        if score > best_score:
            best_score = score
            best = item

    if best:
        best["source_count"] = len(set(best["sources"]))
        best["sources"] = list(set(best["sources"]))

    return best


# ========= 主流程 =========
def crawl_daily_code():
    all_results = []

    print("[百度] 抓取中...")
    baidu_html = fetch_page(BAIDU_URL)
    baidu_data = parse_baidu(baidu_html)
    print(f"[百度] 提取到 {len(baidu_data)} 条")
    all_results.extend(baidu_data)

    print("[抖音] 抓取中...")
    douyin_html = fetch_page(DOUYIN_SEARCH)
    douyin_data = parse_douyin(douyin_html)
    print(f"[抖音] 提取到 {len(douyin_data)} 条")
    all_results.extend(douyin_data)

    # AI 兜底
    if len(all_results) < 2:
        print("[AI] 尝试智谱提取...")
        ai_results = extract_with_ai(baidu_html, "baidu")
        print(f"[AI] 提取到 {len(ai_results)} 条")
        all_results.extend(ai_results)

    print(f"共采集到 {len(all_results)} 条候选")

    best = cross_validate(all_results)

    if best:
        print("✅ 交叉验证结果：")
        print(json.dumps(best, ensure_ascii=False, indent=2))
        return best
    else:
        print("❌ 未找到可靠密码")
        return None


if __name__ == "__main__":
    crawl_daily_code()