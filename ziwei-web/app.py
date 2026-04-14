from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, render_template, request

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_ZW_DIR = Path(__file__).resolve().parent
if str(_ZW_DIR) not in sys.path:
    sys.path.insert(0, str(_ZW_DIR))

from common.ai_report import AiReportError, generate_ziwei_report
from common.birth_form import parse_birth_form
from common.flask_security import init_security

from iztro_chart import build_professional_chart


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    limiter = init_security(app, testing=testing)

    def index():
        result = None
        error = None
        ai_report = None
        ai_error = None
        echo_form = None
        if request.method == "POST":
            action = (request.form.get("action") or "pan").strip()
            birth, err = parse_birth_form(
                request.form,
                gender_required_hint="请选择性别（全量紫微依赖性别）。",
            )
            if err:
                error = err
            elif birth is None:
                error = "输入有误。"
            else:
                dt = birth.dt
                gender = birth.gender_cn
                echo_form = {
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "hour": dt.hour,
                    "minute": dt.minute,
                    "gender": gender,
                }
                try:
                    result = build_professional_chart(
                        dt.year,
                        dt.month,
                        dt.day,
                        dt.hour,
                        dt.minute,
                        gender,
                    )
                except Exception as exc:  # noqa: BLE001
                    error = f"排盘失败（请确认已安装 py-iztro 与 pythonmonkey）：{exc}"
                    result = None
                if result is not None and action == "ai_report":
                    try:
                        ai_report = generate_ziwei_report(result)
                    except AiReportError as exc:
                        ai_error = str(exc)
        return render_template(
            "index.html",
            result=result,
            error=error,
            echo_form=echo_form,
            ai_report=ai_report,
            ai_error=ai_error,
        )

    if limiter.enabled:
        index = limiter.limit("120 per minute", methods=["POST"])(index)
    app.add_url_rule("/", "index", index, methods=["GET", "POST"])
    return app


app = create_app(testing=False)


if __name__ == "__main__":
    # debug 重载子进程会导致 pythonmonkey/内嵌 JS 引擎崩溃，必须关闭 use_reloader
    # threaded=False：内嵌 JS 运行时与多线程并发兼容性因环境而异，单线程更稳
    _dbg = os.environ.get("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")
    app.run(host="127.0.0.1", port=5002, debug=_dbg, use_reloader=False, threaded=False)
