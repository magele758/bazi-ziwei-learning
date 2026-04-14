from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.ai_report import AiReportError, generate_ziwei_report

from iztro_chart import build_professional_chart

app = Flask(__name__)


def parse_form() -> tuple[datetime | None, str | None, str | None]:
    y = request.form.get("year", type=int)
    m = request.form.get("month", type=int)
    d = request.form.get("day", type=int)
    h = request.form.get("hour", type=int, default=12)
    mi = request.form.get("minute", type=int, default=0)
    gender = request.form.get("gender", type=str)
    if y is None or m is None or d is None:
        return None, None, "请输入合法的公历日期。"
    if gender not in ("男", "女"):
        return None, None, "请选择性别（全量紫微依赖性别）。"
    try:
        return datetime(y, m, d, h, mi), gender, None
    except ValueError:
        return None, None, "请输入合法的公历日期时间。"


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    ai_report = None
    ai_error = None
    echo_form = None
    if request.method == "POST":
        action = (request.form.get("action") or "pan").strip()
        dt, gender, err = parse_form()
        if err:
            error = err
        elif dt is None:
            error = "输入有误。"
        else:
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


if __name__ == "__main__":
    # debug 重载子进程会导致 pythonmonkey/内嵌 JS 引擎崩溃，必须关闭 use_reloader
    # threaded=False：内嵌 JS 运行时与多线程并发兼容性因环境而异，单线程更稳
    app.run(host="127.0.0.1", port=5002, debug=True, use_reloader=False, threaded=False)
