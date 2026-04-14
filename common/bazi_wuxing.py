"""八字四柱五行计数（纯 Python，便于单测）。"""

from __future__ import annotations

from collections import Counter

GAN_WUXING = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

ZHI_WUXING = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}


def wuxing_counter(pillars: list[str]) -> Counter[str]:
    c: Counter[str] = Counter()
    for p in pillars:
        if len(p) != 2:
            continue
        g, z = p[0], p[1]
        c[GAN_WUXING.get(g, "?")] += 1
        c[ZHI_WUXING.get(z, "?")] += 1
    return c
