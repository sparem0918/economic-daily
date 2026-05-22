# -*- coding: utf-8 -*-
"""
트럼프 임팩트 트래커 (trump_tracker.py)

기능:
1) 수집된 뉴스 중 트럼프 언급 뉴스 필터링
2) 토픽 자동 분류 (양자컴퓨터, 관세, 반도체, 자동차, 조선, 원자력 등)
3) 토픽별 한국 관련주 매핑
4) 헤드라인 점수로 정렬하여 토픽별 상위 뉴스 선별
5) 시간 윈도우 적용 (기본 48시간)

사용법 (app.py / build_static.py 안에서):
    import trump_tracker
    trump_section = trump_tracker.build_trump_section(processed_items)
    # 그리고 템플릿에 trump_section 으로 전달
"""

from datetime import datetime, timezone, timedelta
from collections import OrderedDict
import re

import trump_config


# ---------------------------------------------------------------
# 유틸리티
# ---------------------------------------------------------------
def _now_kst():
    return datetime.now(timezone(timedelta(hours=9)))


def _parse_dt(value):
    """published_dt / published 필드를 datetime 으로 파싱"""
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _text_of(item):
    """뉴스 항목에서 키워드 매칭 대상 텍스트 추출"""
    parts = [
        item.get("title", ""),
        item.get("summary", ""),
    ]
    # 키포인트가 이미 추출되어 있다면 함께 사용
    key_points = item.get("key_points", [])
    if isinstance(key_points, list):
        parts.extend(key_points)
    return " ".join(p for p in parts if p)


def _contains_any(text, keywords):
    """대소문자 무시 부분 일치 검사"""
    if not text:
        return False
    low = text.lower()
    for kw in keywords:
        if kw.lower() in low:
            return True
    return False


# ---------------------------------------------------------------
# 1) 트럼프 관련 여부 판정
# ---------------------------------------------------------------
def is_trump_related(item):
    text = _text_of(item)
    return _contains_any(text, trump_config.TRUMP_KEYWORDS)


# ---------------------------------------------------------------
# 2) 뉴스에서 토픽 감지 (복수 가능)
# ---------------------------------------------------------------
def detect_topics(item):
    text = _text_of(item)
    matched = []
    for topic_name, conf in trump_config.TRUMP_TOPICS.items():
        if _contains_any(text, conf["keywords"]):
            matched.append(topic_name)
    return matched


# ---------------------------------------------------------------
# 3) 헤드라인 점수 (정렬용, 간단 휴리스틱)
# ---------------------------------------------------------------
_IMPACT_KW = [
    "급등", "급락", "최고", "최저", "돌파", "폭등", "폭락",
    "행정명령", "관세", "지분", "보조금", "투자", "발표",
    "협상", "타결", "결렬", "행정부", "Executive Order",
]
_NUM_RE = re.compile(r"\d[\d,\.]*")


def _score_item(item):
    text = _text_of(item)
    score = 0
    # 숫자 포함 시 가점 (구체적 사실 가능성)
    score += min(len(_NUM_RE.findall(text)), 5)
    # 임팩트 키워드 가점
    for kw in _IMPACT_KW:
        if kw in text:
            score += 2
    # 길이 가점 (짧으면 정보량 적음)
    score += min(len(text) // 60, 5)
    return score


# ---------------------------------------------------------------
# 4) 시간 윈도우 필터
# ---------------------------------------------------------------
def _within_window(item, hours):
    dt = _parse_dt(item.get("published_dt") or item.get("published"))
    if not dt:
        return True  # 시간 정보 없으면 일단 포함
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
    cutoff = _now_kst() - timedelta(hours=hours)
    return dt >= cutoff


# ---------------------------------------------------------------
# 5) 메인: 트럼프 섹션 데이터 생성
# ---------------------------------------------------------------
def build_trump_section(all_items):
    """
    Args:
        all_items: news_collector / news_summarizer 가 만든 전체 뉴스 리스트
                   (각 item 은 title, summary, key_points, published_dt 등 보유)
    Returns:
        dict {
            "total_count": int,
            "topics": [
                {
                    "name": "양자컴퓨터",
                    "icon": "⚛",
                    "description": "...",
                    "items": [뉴스, ...],
                    "stocks": [관련주, ...],
                    "count": int,
                },
                ...
            ],
            "uncategorized": [뉴스, ...],  # 트럼프 관련이지만 토픽 미매칭
        }
    """
    if not all_items:
        return {"total_count": 0, "topics": [], "uncategorized": []}

    # 1) 시간 윈도우 + 트럼프 필터
    trump_items = [
        it for it in all_items
        if _within_window(it, trump_config.TRUMP_NEWS_HOURS_WINDOW)
        and is_trump_related(it)
    ]

    # 2) 토픽별 그룹화
    grouped = OrderedDict()  # topic -> [items]
    for topic_name in trump_config.TRUMP_TOPICS.keys():
        grouped[topic_name] = []
    uncategorized = []

    seen_in_topic = {t: set() for t in grouped.keys()}  # 중복 방지

    for it in trump_items:
        topics = detect_topics(it)
        if not topics:
            uncategorized.append(it)
            continue
        # 하나의 뉴스가 여러 토픽에 매칭될 수 있음 → 가장 우선 토픽에만 배치
        # (TRUMP_TOPICS 의 정의 순서를 우선순위로 사용)
        for t in trump_config.TRUMP_TOPICS.keys():
            if t in topics:
                # 같은 토픽 안에서 중복 ID 방지
                item_id = it.get("id") or it.get("link") or it.get("title", "")
                if item_id in seen_in_topic[t]:
                    break
                grouped[t].append(it)
                seen_in_topic[t].add(item_id)
                break

    # 3) 각 토픽 내 점수 정렬 + 개수 제한
    topics_out = []
    for topic_name, items in grouped.items():
        if not items:
            continue
        items_sorted = sorted(items, key=_score_item, reverse=True)
        items_sorted = items_sorted[: trump_config.MAX_NEWS_PER_TOPIC]

        topic_conf = trump_config.TRUMP_TOPICS[topic_name]
        stocks = trump_config.TOPIC_STOCKS.get(topic_name, [])
        stocks = stocks[: trump_config.MAX_STOCKS_PER_TOPIC]

        topics_out.append({
            "name": topic_name,
            "icon": topic_conf.get("icon", "•"),
            "description": topic_conf.get("description", ""),
            "items": items_sorted,
            "stocks": stocks,
            "count": len(items),  # 윈도우 내 매칭 원본 개수
        })

    # 4) 표시 토픽 수 제한 (뉴스 많은 토픽 우선)
    topics_out.sort(key=lambda x: x["count"], reverse=True)
    topics_out = topics_out[: trump_config.MAX_TOPICS_DISPLAYED]

    return {
        "total_count": len(trump_items),
        "topics": topics_out,
        "uncategorized": uncategorized[:5],
        "generated_at": _now_kst().isoformat(),
    }


# ---------------------------------------------------------------
# 단독 실행 시 mock 테스트
# ---------------------------------------------------------------
if __name__ == "__main__":
    mock = [
        {
            "id": "1",
            "title": "트럼프 행정부, 양자컴퓨팅 9곳에 20억달러 지원·지분 확보",
            "summary": "IBM 10억달러, 글로벌파운드리스 3억7500만달러. 인텔식 산업 지원 모델 재현.",
            "key_points": ["20억달러 인센티브 자금 배정"],
            "source": "트레이딩키",
            "published_dt": _now_kst().isoformat(),
            "link": "http://example.com/1",
        },
        {
            "id": "2",
            "title": "트럼프 \"반도체 100% 관세 부과\" 발언, 한국 수출 영향",
            "summary": "삼성전자·SK하이닉스 대미 수출에 직접 관세 가능성. 환율 변동성 확대.",
            "key_points": [],
            "source": "한국경제",
            "published_dt": _now_kst().isoformat(),
            "link": "http://example.com/2",
        },
        {
            "id": "3",
            "title": "MASGA 본격화…한미 조선업 협력 한화오션 수주 기대",
            "summary": "트럼프 행정부 조선업 동맹 추진. HD현대중공업·한화오션 수혜 전망.",
            "key_points": [],
            "source": "조선비즈",
            "published_dt": _now_kst().isoformat(),
            "link": "http://example.com/3",
        },
        {
            "id": "4",
            "title": "코스피 외국인 1조 순매수 사상 최고치",
            "summary": "기관도 동반 매수. 반도체 대형주 강세.",
            "key_points": [],
            "source": "연합뉴스",
            "published_dt": _now_kst().isoformat(),
            "link": "http://example.com/4",
        },
    ]
    section = build_trump_section(mock)
    print("=" * 60)
    print(f"트럼프 관련 뉴스 총 {section['total_count']}건")
    print("=" * 60)
    for t in section["topics"]:
        print(f"\n{t['icon']} {t['name']} ({t['count']}건)")
        print(f"   {t['description']}")
        for it in t["items"]:
            print(f"   - {it['title']}")
        if t["stocks"]:
            print(f"   관련주: " + ", ".join(s["name"] for s in t["stocks"]))
    if section["uncategorized"]:
        print(f"\n[미분류 트럼프 뉴스 {len(section['uncategorized'])}건]")
        for it in section["uncategorized"]:
            print(f"   - {it['title']}")
