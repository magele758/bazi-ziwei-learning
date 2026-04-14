from __future__ import annotations

from lunar_python import Solar


def test_solar_to_four_pillars_shape() -> None:
    """固定公历时刻：四柱应为四组各2 个汉字。"""
    solar = Solar.fromYmdHms(2000, 1, 1, 12, 0, 0)
    ec = solar.getLunar().getEightChar()
    pillars = [ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime()]
    assert len(pillars) == 4
    for p in pillars:
        assert len(p) == 2
