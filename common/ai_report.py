"""调用 OpenAI 兼容 Chat Completions API生成命理学习向解读（服务端密钥，不经过浏览器）。"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

SYSTEM_BAZI = """你是一位熟悉传统四柱八字的学习向讲解者。用户会提供由程序排盘得到的结构化数据（非口述）。
要求：
1. 用简体中文，用【总览】【四柱与十神要点】【大运流年提示】【学习提醒】这类【】小标题分段，条目前加「-」，口语化、好懂。
2. 只作文化、性格与人生课题角度的可能性讨论，避免铁口直断、恐吓式断言；明确说明命理非科学、仅供参考。
3. 不要编造盘中没有的干支；若信息不足请说明。
4. 不要输出 JSON 或代码块。"""

SYSTEM_ZIWEI = """你是一位熟悉紫微斗数命盘结构的学习向讲解者。用户会提供程序排出的十二宫与星曜摘要。
要求：
1. 用简体中文，用【总览】【命宫与身宫】【十二宫要点】【大限与学习提醒】等【】标题分段，条目前加「- 」，口语化。
2. 只作教学与文化视角的可能性分析；无主星、借星等情况要按传统说法解释清楚，避免绝对化。
3. 不要编造盘中没有的星曜或宫位；明确命理仅供参考。
4. 不要输出 JSON 或代码块。"""


class AiReportError(Exception):
    """配置缺失或 API 调用失败。"""


def _chat(messages: list[dict[str, str]], *, timeout: float = 120.0) -> str:
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise AiReportError("未配置环境变量 OPENAI_API_KEY。请在运行前 export，或在 conda 环境中设置。")
    base = (os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = (os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip()
    url = f"{base}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.65,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        raise AiReportError(
            f"模型 API 返回错误 HTTP {e.response.status_code}。"
            "请检查 OPENAI_BASE_URL、OPENAI_MODEL 与 OPENAI_API_KEY 是否有效。"
        ) from e
    except httpx.RequestError as e:
        raise AiReportError(f"无法连接模型 API：{e}") from e
    try:
        return (data["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError) as e:
        raise AiReportError("模型响应格式异常，请稍后重试或更换模型。") from e


def bazi_user_content(result: dict) -> str:
    """将八字排盘结果压成给模型的正文（避免上传无关大字段）。"""
    slim = {
        "公历": result.get("solar"),
        "性别": result.get("gender"),
        "农历": result.get("lunar_cn"),
        "四柱": result.get("pillars"),
        "四柱细表": result.get("pillar_table"),
        "纳音": result.get("nayin"),
        "旬空": result.get("xunkong"),
        "五行计数": result.get("wuxing"),
        "胎元胎息": {"胎元": result.get("taiyuan"), "胎息": result.get("taixi")},
        "命宫身宫_八字法": {"命宫": result.get("minggong_bazi"), "身宫": result.get("shengong_bazi")},
        "大运元信息": result.get("yun_meta"),
        "大运表": result.get("dayun"),
        "流年示例_首步大运十年": result.get("liunian_first_yun"),
    }
    return "以下为由程序排出的四柱数据（JSON）：\n```json\n" + json.dumps(slim, ensure_ascii=False, indent=2) + "\n```"


def ziwei_user_content(result: dict) -> str:
    """紫微结果可能很大，只传解读所需摘要。"""
    palaces = []
    for p in result.get("palaces_render") or []:
        palaces.append(
            {
                "宫": p.get("name"),
                "干支": f"{p.get('heavenly_stem', '')}{p.get('earthly_branch', '')}",
                "主星": p.get("major_line"),
                "辅星": p.get("minor_line"),
                "杂曜": (p.get("adjective_line") or "")[:200],
                "长生12": p.get("changsheng12"),
                "大限": p.get("decadal_line"),
                "小限岁数": p.get("ages_line"),
                "身宫在此": p.get("is_shen_gong_here"),
                "来因宫": p.get("is_original_palace"),
            }
        )
    slim = {
        "输入与历法": {
            "阳历": result.get("solar_date"),
            "农历": result.get("lunar_date"),
            "性别": result.get("gender"),
            "时辰": result.get("time"),
            "时辰范围": result.get("time_range"),
        },
        "命宫摘要": result.get("ming_palace_summary"),
        "命身主与五行局": {
            "命主": result.get("soul"),
            "身主": result.get("body"),
            "身宫地支": result.get("earthly_branch_of_body_palace"),
            "命宫位地支": result.get("earthly_branch_of_soul_palace"),
            "五行局": result.get("five_elements_class"),
        },
        "十二宫": palaces,
    }
    body = json.dumps(slim, ensure_ascii=False, indent=2)
    return "以下为由程序排出的紫微斗数摘要（JSON）：\n```json\n" + body + "\n```"


def generate_bazi_report(result: dict) -> str:
    return _chat(
        [
            {"role": "system", "content": SYSTEM_BAZI},
            {"role": "user", "content": bazi_user_content(result)},
        ]
    )


def generate_ziwei_report(result: dict) -> str:
    return _chat(
        [
            {"role": "system", "content": SYSTEM_ZIWEI},
            {"role": "user", "content": ziwei_user_content(result)},
        ]
    )
