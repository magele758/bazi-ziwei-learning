from __future__ import annotations

from common.bazi_wuxing import wuxing_counter


def test_wuxing_counter_known_pillars() -> None:
    c = wuxing_counter(["甲子", "丙寅"])
    assert c["木"] == 2
    assert c["火"] == 1
    assert c["水"] == 1
