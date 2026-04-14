from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _ziwei_mod():
    key = "ziwei_web_dynamic"
    if key not in sys.modules:
        p = ROOT / "ziwei-web" / "app.py"
        spec = importlib.util.spec_from_file_location(key, p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        assert spec.loader
        spec.loader.exec_module(mod)
    return sys.modules[key]


@pytest.mark.skipif(
    importlib.util.find_spec("py_iztro") is None,
    reason="py-iztro 未安装",
)
def test_ziwei_post_pan_renders_result() -> None:
    mod = _ziwei_mod()
    app = mod.create_app(testing=True)
    c = app.test_client()
    rv = c.post(
        "/",
        data={
            "year": 2000,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "gender": "女",
            "action": "pan",
        },
    )
    assert rv.status_code == 200
    text = rv.get_data(as_text=True)
    assert "命盘总览" in text
