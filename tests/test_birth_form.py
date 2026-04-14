from __future__ import annotations

from common.birth_form import parse_birth_form
from werkzeug.datastructures import MultiDict


def test_parse_birth_form_ok() -> None:
    f = MultiDict(
        [
            ("year", "2000"),
            ("month", "6"),
            ("day", "15"),
            ("hour", "14"),
            ("minute", "30"),
            ("gender", "男"),
        ]
    )
    birth, err = parse_birth_form(f, gender_required_hint="选性别")
    assert err is None and birth is not None
    assert birth.gender_cn == "男"
    assert birth.dt.year == 2000 and birth.dt.month == 6 and birth.dt.day == 15


def test_parse_birth_form_gender_hint() -> None:
    f = MultiDict([("year", "2000"), ("month", "1"), ("day", "1"), ("gender", "")])
    _, err = parse_birth_form(f, gender_required_hint="自定义提示")
    assert err == "自定义提示"
