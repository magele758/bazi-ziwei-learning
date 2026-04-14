"""公历出生时间与性别：从表单解析（Flask/Werkzeug MultiDict 兼容）。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class BirthInput:
    dt: datetime
    gender_cn: str  # 男 / 女


def parse_birth_form(form: Any, *, gender_required_hint: str) -> tuple[BirthInput | None, str | None]:
    """
    从 request.form 解析。成功返回 (BirthInput, None)，失败返回 (None, 错误文案)。
    """
    y = form.get("year", type=int)
    m = form.get("month", type=int)
    d = form.get("day", type=int)
    h = form.get("hour", type=int, default=12)
    mi = form.get("minute", type=int, default=0)
    gender = form.get("gender", type=str)
    if y is None or m is None or d is None:
        return None, "请输入合法的公历日期。"
    if gender not in ("男", "女"):
        return None, gender_required_hint
    try:
        return BirthInput(datetime(y, m, d, h, mi), gender), None
    except ValueError:
        return None, "请输入合法的公历日期时间。"
