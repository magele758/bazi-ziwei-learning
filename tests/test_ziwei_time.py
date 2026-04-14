from __future__ import annotations

from common.ziwei_time import hour_to_iztro_time_index


def test_hour_to_iztro_time_index_zi_shi_boundaries() -> None:
    assert hour_to_iztro_time_index(0) == 0
    assert hour_to_iztro_time_index(23) == 12


def test_hour_to_iztro_time_index_day_hours() -> None:
    assert hour_to_iztro_time_index(1) == 1
    assert hour_to_iztro_time_index(2) == 1
    assert hour_to_iztro_time_index(3) == 2
    assert hour_to_iztro_time_index(22) == 11
