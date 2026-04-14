"""紫微 iztro 时辰槽映射（纯函数，无第三方依赖，便于单测）。"""

from __future__ import annotations


def hour_to_iztro_time_index(hour: int) -> int:
    """
    将 0–23 时映射为 iztro 时辰序号 0–12。
    0=早子时(00:00起)，12=晚子时(23:00 起)；其余为丑–亥。
    """
    if hour == 0:
        return 0
    if hour == 23:
        return 12
    return (hour + 1) // 2
