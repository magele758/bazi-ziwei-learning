"""全量紫微排盘：基于 py-iztro（iztro JS 的 Python 封装）。"""

from __future__ import annotations

import threading

from py_iztro import Astro

_astro_lock = threading.Lock()
_astro_singleton: Astro | None = None


def hour_to_iztro_time_index(hour: int) -> int:
    """
    将0–23 时映射为 iztro 时辰序号 0–12。
    0=早子时(00:00起)，12=晚子时(23:00起)；其余为丑–亥。
    """
    if hour == 0:
        return 0
    if hour == 23:
        return 12
    return (hour + 1) // 2


def fmt_star(s: dict) -> str:
    name = s.get("name") or ""
    parts = [name]
    b = s.get("brightness")
    if b:
        parts.append(f"[{b}]")
    m = s.get("mutagen")
    if m:
        parts.append(f"化{m}")
    return "".join(parts)


def build_professional_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    gender: str,
    fix_leap: bool = True,
) -> dict:
    """
    返回与 AstrolabeModel.model_dump() 一致的字典，含十二宫全星曜与神煞等。
    minute 当前仅作展示，边界仍按整点时辰（与 iztro 时辰槽一致）。
    """
    global _astro_singleton
    ti = hour_to_iztro_time_index(hour)
    solar = f"{year}-{month}-{day}"
    with _astro_lock:
        if _astro_singleton is None:
            _astro_singleton = Astro()
        raw = _astro_singleton.by_solar(solar, ti, gender, fix_leap, "zh-CN")
    data = raw.model_dump()
    palace_order = [
        "命宫",
        "兄弟",
        "夫妻",
        "子女",
        "财帛",
        "疾厄",
        "迁移",
        "仆役",
        "官禄",
        "田宅",
        "福德",
        "父母",
    ]

    def _palace_sort_key(row: dict) -> int:
        try:
            return palace_order.index(row.get("name", ""))
        except ValueError:
            return 99

    # 便于模板渲染的派生字段
    palaces_out = []
    for p in data.get("palaces", []):
        majors = [fmt_star(x) for x in (p.get("major_stars") or [])]
        minors = [fmt_star(x) for x in (p.get("minor_stars") or [])]
        adjs = [x.get("name", "") for x in (p.get("adjective_stars") or [])]
        dec = p.get("decadal") or {}
        palaces_out.append(
            {
                **p,
                "major_line": "、".join(majors) if majors else "—",
                "minor_line": "、".join(minors) if minors else "—",
                "adjective_line": "、".join(adjs) if adjs else "—",
                "decadal_line": (
                    f"{dec.get('heavenly_stem', '')}{dec.get('earthly_branch', '')} "
                    f"（约 {dec.get('range', ['?', '?'])[0]}–{dec.get('range', ['?', '?'])[1]} 岁）"
                    if dec
                    else "—"
                ),
                "ages_line": "、".join(str(a) for a in (p.get("ages") or [])),
            }
        )
    palaces_out.sort(key=_palace_sort_key)
    data["palaces_render"] = palaces_out
    data["time_index_used"] = ti
    data["solar_input"] = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
    ming_row = next((x for x in data.get("palaces", []) if x.get("name") == "命宫"), None)
    if ming_row:
        gz = f"{ming_row.get('heavenly_stem', '')}{ming_row.get('earthly_branch', '')}"
        maj = "、".join(fmt_star(s) for s in (ming_row.get("major_stars") or []))
        data["ming_palace_summary"] = f"{gz}宫 · {maj}" if maj else f"{gz}宫 · 无主星"
    else:
        data["ming_palace_summary"] = ""
    body_br = data.get("earthly_branch_of_body_palace") or ""
    for row in palaces_out:
        row["is_shen_gong_here"] = row.get("earthly_branch") == body_br
    return data
