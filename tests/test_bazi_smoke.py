from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _bazi_mod():
    key = "bazi_web_dynamic"
    if key not in sys.modules:
        p = ROOT / "bazi-web" / "app.py"
        spec = importlib.util.spec_from_file_location(key, p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        assert spec.loader
        spec.loader.exec_module(mod)
    return sys.modules[key]


def test_bazi_post_pan_renders_result() -> None:
    mod = _bazi_mod()
    app = mod.create_app(testing=True)
    c = app.test_client()
    rv = c.post(
        "/",
        data={
            "year": 2000,
            "month": 1,
            "day": 1,
            "hour": 12,
            "minute": 0,
            "gender": "男",
            "action": "pan",
        },
    )
    assert rv.status_code == 200
    text = rv.get_data(as_text=True)
    assert "排盘结果" in text
    assert "四柱" in text
