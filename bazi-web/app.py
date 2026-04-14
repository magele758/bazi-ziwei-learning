from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, render_template, request
from lunar_python import Solar

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from common.ai_report import AiReportError, generate_bazi_report
from common.bazi_wuxing import wuxing_counter
from common.birth_form import parse_birth_form
from common.flask_security import init_security


def pillar_rows(ec) -> list[dict]:
    specs = [
        (
            "年",
            ec.getYear,
            ec.getYearGan,
            ec.getYearZhi,
            ec.getYearHideGan,
            ec.getYearShiShenGan,
            ec.getYearShiShenZhi,
            ec.getYearDiShi,
        ),
        (
            "月",
            ec.getMonth,
            ec.getMonthGan,
            ec.getMonthZhi,
            ec.getMonthHideGan,
            ec.getMonthShiShenGan,
            ec.getMonthShiShenZhi,
            ec.getMonthDiShi,
        ),
        (
            "日",
            ec.getDay,
            ec.getDayGan,
            ec.getDayZhi,
            ec.getDayHideGan,
            ec.getDayShiShenGan,
            ec.getDayShiShenZhi,
            ec.getDayDiShi,
        ),
        (
            "时",
            ec.getTime,
            ec.getTimeGan,
            ec.getTimeZhi,
            ec.getTimeHideGan,
            ec.getTimeShiShenGan,
            ec.getTimeShiShenZhi,
            ec.getTimeDiShi,
        ),
    ]
    rows = []
    for label, gz_f, gan_f, zhi_f, hide_f, ssg_f, ssz_f, dishi_f in specs:
        hide = hide_f()
        ssz = ssz_f()
        rows.append(
            {
                "label": label,
                "ganzhi": gz_f(),
                "gan": gan_f(),
                "zhi": zhi_f(),
                "canggan": " ".join(hide),
                "shishen_gan": ssg_f(),
                "shishen_zhi": " ".join(ssz) if isinstance(ssz, list) else ssz,
                "dishi": dishi_f(),
            }
        )
    return rows


def yun_rows(ec, gender: int) -> tuple[dict, list[dict], list[dict]]:
    yun = ec.getYun(gender, 1)
    meta = {
        "forward": yun.isForward(),
        "start_year": yun.getStartYear(),
        "start_month": yun.getStartMonth(),
        "start_day": yun.getStartDay(),
        "start_solar": yun.getStartSolar().toYmd(),
    }
    da_list: list[dict] = []
    for dy in yun.getDaYun(12):
        idx = dy.getIndex()
        row = {
            "index": idx,
            "ganzhi": dy.getGanZhi() or "童限",
            "years": f"{dy.getStartYear()}–{dy.getEndYear()}",
            "ages": f"{dy.getStartAge()}–{dy.getEndAge()}岁",
        }
        da_list.append(row)

    liunian_sample: list[dict] = []
    for dy in yun.getDaYun(12):
        if dy.getIndex() < 1:
            continue
        for ln in dy.getLiuNian(10):
            liunian_sample.append(
                {
                    "dayun_gz": dy.getGanZhi(),
                    "year": ln.getYear(),
                    "age": ln.getAge(),
                    "ganzhi": ln.getGanZhi(),
                }
            )
        break
    return meta, da_list, liunian_sample


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
                gender_required_hint="请选择性别（排大运需要）。",
            )
            if err:
                error = err
            elif birth is None:
                error = "输入有误。"
            else:
                dt = birth.dt
                gender = 1 if birth.gender_cn == "男" else 0
                echo_form = {
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "hour": dt.hour,
                    "minute": dt.minute,
                    "gender": birth.gender_cn,
                }
                solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0)
                lunar = solar.getLunar()
                ec = lunar.getEightChar()
                y, mo, da, ti = ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime()
                pillars = [y, mo, da, ti]
                ymeta, dayun, liunian = yun_rows(ec, gender)
                result = {
                    "solar": f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}",
                    "gender": birth.gender_cn,
                    "lunar_cn": lunar.toString(),
                    "lunar_ymd": f"{lunar.getMonth()}月{lunar.getDay()}日",
                    "time_zhi": lunar.getTimeZhi(),
                    "pillars": {"年": y, "月": mo, "日": da, "时": ti},
                    "pillars_joined": " ".join(pillars),
                    "pillar_table": pillar_rows(ec),
                    "shengxiao": lunar.getYearShengXiao(),
                    "nayin": {
                        "年": lunar.getYearNaYin(),
                        "月": lunar.getMonthNaYin(),
                        "日": lunar.getDayNaYin(),
                        "时": lunar.getTimeNaYin(),
                    },
                    "wuxing": dict(wuxing_counter(pillars)),
                    "xunkong": {
                        "年": ec.getYearXunKong(),
                        "月": ec.getMonthXunKong(),
                        "日": ec.getDayXunKong(),
                        "时": ec.getTimeXunKong(),
                    },
                    "taiyuan": ec.getTaiYuan(),
                    "taixi": ec.getTaiXi(),
                    "minggong_bazi": ec.getMingGong(),
                    "shengong_bazi": ec.getShenGong(),
                    "yun_meta": ymeta,
                    "dayun": dayun,
                    "liunian_first_yun": liunian,
                }
                if action == "ai_report":
                    try:
                        ai_report = generate_bazi_report(result)
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
    _dbg = os.environ.get("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")
    app.run(host="127.0.0.1", port=5001, debug=_dbg, use_reloader=False, threaded=True)
