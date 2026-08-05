"""
AI 提取工具 —— 用智谱 GLM-4.6 从网页/视频字幕文本中提取结构化数据
支持 fallback 到 DeepSeek / Kimi（免费额度）
"""
import os
import json
import re
from openai import OpenAI

# ---------- 智谱 GLM ----------
GLM_API_KEY = os.getenv("ZHIPU_API_KEY", "")
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

# ---------- DeepSeek 兜底 ----------
DS_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DS_BASE_URL = "https://api.deepseek.com/v1"

def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """优先智谱，失败切 DeepSeek"""
    # 1. 尝试智谱
    if GLM_API_KEY:
        try:
            client = OpenAI(api_key=GLM_API_KEY, base_url=GLM_BASE_URL)
            resp = client.chat.completions.create(
                model="glm-4.6",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=2048,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[WARN] 智谱调用失败: {e}")

    # 2. 兜底 DeepSeek
    if DS_API_KEY:
        try:
            client = OpenAI(api_key=DS_API_KEY, base_url=DS_BASE_URL)
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=2048,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[WARN] DeepSeek 也失败: {e}")

    # 3. 全挂了返回空
    return ""

# ============ 改枪码提取 ============
BUILD_SYSTEM_PROMPT = """你是一个游戏数据提取助手。从文本中提取三角洲行动（Delta Force）的改枪码信息。
输出严格 JSON 数组，每个元素包含字段：
- weapon_name: 枪械名称（如 M7战斗步枪、K416突击步枪）
- build_code: 改枪码字符串（如 6JQJDAK0BAC7RIM3B0293）
- title: 配枪标题/描述
- tier: 强度评级 T0/T1/T2（根据文本推断，不确定填T1）
- category: 枪种（突击步枪/冲锋枪/狙击枪/战斗步枪/轻机枪/霰弹枪/手枪）
- tags: 标签数组（如 ["架枪","跑刀","中远距离"]）
- confidence: 0-1 的置信度

只输出 JSON，不要任何解释。"""

def extract_weapon_builds(text: str) -> list[dict]:
    """从大段文本中提取改枪码"""
    # 先用正则粗筛有没有改枪码特征
    if not re.search(r'[A-Z0-9]{10,}', text):
        return []

    user_prompt = f"请从以下游戏攻略文本中提取所有改枪码信息：\n\n{text[:4000]}"
    result = _call_llm(BUILD_SYSTEM_PROMPT, user_prompt)

    try:
        # 去掉可能的 markdown 代码块包裹
        result = re.sub(r'^```json\s*', '', result.strip())
        result = re.sub(r'\s*```$', '', result)
        data = json.loads(result)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        print(f"[WARN] JSON 解析失败: {result[:200]}")
        return []

# ============ 跑刀路线提取 ============
ROUTE_SYSTEM_PROMPT = """从文本中提取三角洲行动跑刀路线信息。
输出严格 JSON 数组，每个元素包含：
- map_name: 地图名（零号大坝/航天基地/巴克什/终极战场）
- title: 路线标题
- difficulty: easy/medium/hard
- expected_loot: 预期收益描述
- risk_level: low/medium/high
- steps: 步骤数组，每个步骤 {order:序号, action:动作描述, location:地点}
- tips: 注意事项"""

def extract_routes(text: str) -> list[dict]:
    user_prompt = f"请从以下跑刀攻略中提取路线信息：\n\n{text[:4000]}"
    result = _call_llm(ROUTE_SYSTEM_PROMPT, user_prompt)
    try:
        result = re.sub(r'^```json\s*', '', result.strip())
        result = re.sub(r'\s*```$', '', result)
        data = json.loads(result)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []

# ============ 每日密码提取 ============
CODE_SYSTEM_PROMPT = """从文本中提取三角洲行动每日密码。
输出严格 JSON 对象：
- code: 密码字符串
- date: 日期 YYYY-MM-DD（如果文本提到）
- confidence: 0-1 置信度
- source_detail: 来源说明"""

def extract_daily_code(text: str) -> dict | None:
    # 关键词过滤
    keywords = ["密码", "每日", "密码门", "开门密码", "安全箱密码"]
    if not any(kw in text for kw in keywords):
        return None

    user_prompt = f"请从以下信息中提取三角洲行动每日密码：\n\n{text[:2000]}"
    result = _call_llm(CODE_SYSTEM_PROMPT, user_prompt)
    try:
        result = re.sub(r'^```json\s*', '', result.strip())
        result = re.sub(r'\s*```$', '', result)
        return json.loads(result)
    except json.JSONDecodeError:
        return None

# ============ 干员分析提取 ============
OPERATOR_SYSTEM_PROMPT = """从文本中提取三角洲行动干员分析信息。
输出严格 JSON 数组，每个元素包含：
- operator_name: 干员名
- role: 定位（突击/支援/侦察/工程）
- overall_rating: 综合评分 0-10
- strengths: 优势数组
- weaknesses: 劣势数组
- best_maps: 适合地图数组
- best_weapons: 推荐武器数组
- playstyle: 打法风格描述
- tips: 实用技巧"""

def extract_operators(text: str) -> list[dict]:
    user_prompt = f"请从以下干员攻略中提取分析信息：\n\n{text[:5000]}"
    result = _call_llm(OPERATOR_SYSTEM_PROMPT, user_prompt)
    try:
        result = re.sub(r'^```json\s*', '', result.strip())
        result = re.sub(r'\s*```$', '', result)
        data = json.loads(result)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
