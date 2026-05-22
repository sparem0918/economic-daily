# -*- coding: utf-8 -*-
"""
경제 뉴스 뉴스레터 웹앱 메인
- Flask 기반
- 모바일/PC 반응형
- 30분 캐시
"""
import os
import sys
import locale
from datetime import datetime, timezone, timedelta

from flask import Flask, render_template, jsonify, request

import config
import news_collector
import news_summarizer
import buffett_loader
import gemini_summarizer
import trump_tracker


# Windows 콘솔 한글 출력 보장
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


app = Flask(__name__)


def get_kst_now():
    """현재 KST 시각"""
    return datetime.now(timezone(timedelta(hours=9)))


def format_korean_date(dt):
    """한국어 날짜 포맷 (2026년 5월 21일 목요일)"""
    if isinstance(dt, str):
        from dateutil import parser as dp
        dt = dp.parse(dt)

    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    weekday = weekdays[dt.weekday()]
    return f"{dt.year}년 {dt.month}월 {dt.day}일 {weekday}요일"


def format_relative_time(dt_str):
    """상대 시간 표시 (3시간 전, 어제, ...)"""
    if not dt_str:
        return ""
    try:
        from dateutil import parser as dp
        dt = dp.parse(dt_str)
        now = get_kst_now()
        diff = now - dt

        seconds = diff.total_seconds()
        if seconds < 60:
            return "방금"
        elif seconds < 3600:
            return f"{int(seconds / 60)}분 전"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}시간 전"
        elif seconds < 86400 * 2:
            return "어제"
        else:
            return f"{int(seconds / 86400)}일 전"
    except Exception:
        return ""


# Jinja2 필터 등록
app.jinja_env.filters["korean_date"] = format_korean_date
app.jinja_env.filters["relative_time"] = format_relative_time


@app.route("/")
def index():
    """메인 뉴스레터 페이지"""
    force = request.args.get("refresh") == "1"
    raw = news_collector.collect_news(force_refresh=force)
    processed = news_summarizer.process_news(raw)
    buffett = buffett_loader.get_buffett_context()

    # Gemini 종합 요약 (API 키 없거나 실패하면 None)
    brief = gemini_summarizer.generate_brief(
        processed.get("all_items", []),
        force_refresh=force,
    )

    # 트럼프 임팩트 트래커 (트럼프 관련 뉴스 0건이면 템플릿에서 자동 숨김)
    trump_section = trump_tracker.build_trump_section(
        processed.get("all_items", [])
    )

    now = get_kst_now()

    return render_template(
        "newsletter.html",
        date_str=format_korean_date(now),
        time_str=now.strftime("%H:%M"),
        total_count=processed["total_count"],
        headlines=processed["headlines"],
        grouped=processed["grouped"],
        pulse=processed["pulse"],
        brief=brief,
        buffett=buffett,
        trump_section=trump_section,
        generated_at=raw.get("generated_at"),
    )


@app.route("/api/news")
def api_news():
    """JSON API 엔드포인트"""
    force = request.args.get("refresh") == "1"
    raw = news_collector.collect_news(force_refresh=force)
    processed = news_summarizer.process_news(raw)
    # all_items는 너무 크므로 제외
    processed.pop("all_items", None)
    return jsonify(processed)


@app.route("/api/refresh")
def api_refresh():
    """캐시 강제 갱신"""
    raw = news_collector.collect_news(force_refresh=True)
    return jsonify({
        "status": "ok",
        "count": raw.get("total_count", 0),
        "generated_at": raw.get("generated_at"),
    })


@app.route("/health")
def health():
    """헬스 체크"""
    return jsonify({"status": "ok", "time": get_kst_now().isoformat()})


if __name__ == "__main__":
    print("=" * 60)
    print("경제 뉴스 뉴스레터 - Buffett Edition")
    print("=" * 60)
    print(f"  주소     : http://localhost:{config.PORT}")
    print(f"  로컬망   : http://<PC-IP>:{config.PORT}  (모바일에서 접속 시 사용)")
    print(f"  강제갱신 : http://localhost:{config.PORT}/?refresh=1")
    print(f"  헬스체크 : http://localhost:{config.PORT}/health")
    print("=" * 60)
    print("  종료하려면 Ctrl+C 를 누르세요.")
    print("=" * 60)

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
