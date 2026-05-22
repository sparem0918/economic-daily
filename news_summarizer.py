# -*- coding: utf-8 -*-
"""
뉴스 분석기
- 카테고리 자동 분류
- 키포인트 추출 (숫자, 핵심 문장)
- 헤드라인 점수 계산
"""
import re
from collections import Counter

import config


# 한국어 종결어미/조사 등 노이즈 단어 (헤드라인 추출 시 제외)
NOISE_WORDS = {
    "있다", "없다", "한다", "된다", "이다", "있는", "하는", "되는",
    "이상", "이하", "수준", "관련", "통해", "위해", "대한", "대해",
    "오는", "지난", "최근", "올해", "내년", "전년",
}


def _score_text(text):
    """텍스트의 정보량 점수 계산
    - 숫자(%, 원, 달러) 포함 시 가산
    - 길이 적당할 때 가산
    """
    if not text:
        return 0

    score = 0

    # 숫자 정보 가산점
    if re.search(r"\d+[.,]?\d*\s*%", text):
        score += 3
    if re.search(r"\d+[.,]?\d*\s*(억|조|만|천)", text):
        score += 3
    if re.search(r"\$\d+|\d+\s*달러|\d+\s*원", text):
        score += 2

    # 핵심 키워드 가산점
    impact_keywords = [
        "사상 최고", "사상 최저", "역대", "최대", "최저", "최고",
        "급등", "급락", "폭등", "폭락", "돌파", "붕괴",
        "발표", "결정", "인상", "인하", "동결",
    ]
    for kw in impact_keywords:
        if kw in text:
            score += 2

    # 길이 보너스 (너무 짧지도 길지도 않을 때)
    length = len(text)
    if 30 <= length <= 200:
        score += 1

    return score


def classify_category(item):
    """뉴스의 카테고리를 자동 분류
    - 제목 + 요약에서 키워드 매칭
    - 가장 많이 매칭된 카테고리 반환
    - 매칭 없으면 원래 source_category 반환
    """
    text = f"{item.get('title', '')} {item.get('summary', '')}"

    scores = {}
    for category, keywords in config.CATEGORY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            scores[category] = count

    if scores:
        # 최다 매칭 카테고리 반환
        return max(scores.items(), key=lambda x: x[1])[0]

    # 매칭 없으면 원래 카테고리
    return item.get("source_category", "종합")


def tag_buffett_principles(item):
    """뉴스를 버핏 원칙별로 태깅
    매칭되는 원칙 리스트 반환 (최대 3개)
    """
    text = f"{item.get('title', '')} {item.get('summary', '')}"

    matched = []
    for principle, keywords in config.BUFFETT_TAGS.items():
        for kw in keywords:
            if kw in text:
                matched.append(principle)
                break

    return matched[:3]


def extract_key_points(item):
    """뉴스에서 키포인트 문장 1-2개 추출
    - 요약에서 정보량 높은 문장 우선
    - 너무 길면 자르기
    """
    summary = item.get("summary", "").strip()
    if not summary:
        return []

    # 문장 단위로 분리 (한국어 종결부호)
    sentences = re.split(r"(?<=[.!?다요죠음음])\s+", summary)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [summary[:150]]

    # 각 문장 점수화
    scored = [(s, _score_text(s)) for s in sentences]
    scored.sort(key=lambda x: x[1], reverse=True)

    # 상위 2개 (단, 60자 이상)
    key_points = []
    for sentence, _ in scored:
        if len(sentence) >= 20:
            # 너무 길면 자르기
            if len(sentence) > 180:
                sentence = sentence[:177] + "..."
            key_points.append(sentence)
            if len(key_points) >= 2:
                break

    if not key_points and sentences:
        key_points = [sentences[0][:180]]

    return key_points


def select_headlines(items, max_count=None):
    """전체 뉴스에서 헤드라인급 뉴스 선별
    - 정보량 점수 + 카테고리 다양성 고려
    """
    if max_count is None:
        max_count = config.MAX_HEADLINES

    # 각 뉴스 점수화
    scored = []
    for item in items:
        title_score = _score_text(item.get("title", ""))
        summary_score = _score_text(item.get("summary", "")) * 0.3
        # 매체별 가중치 (모든 매체 균등하게)
        total = title_score + summary_score
        scored.append((item, total))

    # 점수 역순 정렬
    scored.sort(key=lambda x: x[1], reverse=True)

    # 카테고리 다양성: 같은 카테고리 연속 방지
    selected = []
    used_categories = Counter()
    for item, score in scored:
        cat = item.get("category", "종합")
        if used_categories[cat] >= 2:  # 카테고리당 최대 2개
            continue
        selected.append(item)
        used_categories[cat] += 1
        if len(selected) >= max_count:
            break

    return selected


def group_by_category(items, max_per_category=None):
    """카테고리별로 뉴스 그룹핑"""
    if max_per_category is None:
        max_per_category = config.MAX_NEWS_PER_CATEGORY

    groups = {}
    for item in items:
        cat = item.get("category", "종합")
        if cat not in groups:
            groups[cat] = []
        if len(groups[cat]) < max_per_category:
            groups[cat].append(item)

    # 카테고리 표시 순서
    category_order = [
        "증시", "금융", "산업", "IT/테크", "글로벌",
        "부동산", "정책/규제", "종합",
    ]

    ordered = {}
    for cat in category_order:
        if cat in groups and groups[cat]:
            ordered[cat] = groups[cat]

    # 기타 카테고리
    for cat, items_list in groups.items():
        if cat not in ordered and items_list:
            ordered[cat] = items_list

    return ordered


def analyze_market_pulse(items):
    """전체 뉴스 흐름에서 시장 분위기 추출
    - 상승/하락 키워드 카운트
    - 주요 키워드 빈도 (간단한 트렌드)
    """
    text = " ".join([f"{i.get('title','')} {i.get('summary','')}" for i in items])

    bullish_keywords = ["상승", "급등", "최고", "돌파", "회복", "호조", "흑자전환"]
    bearish_keywords = ["하락", "급락", "최저", "붕괴", "침체", "악화", "적자"]

    bullish_count = sum(text.count(kw) for kw in bullish_keywords)
    bearish_count = sum(text.count(kw) for kw in bearish_keywords)

    total = bullish_count + bearish_count
    if total == 0:
        sentiment = "중립"
        ratio = 0.5
    else:
        ratio = bullish_count / total
        if ratio > 0.6:
            sentiment = "긍정 우세"
        elif ratio < 0.4:
            sentiment = "부정 우세"
        else:
            sentiment = "혼조"

    # 상위 키워드 (간단 빈도)
    trend_keywords = [
        "코스피", "코스닥", "환율", "금리", "반도체", "AI", "삼성전자",
        "SK하이닉스", "현대차", "미국", "중국", "연준", "트럼프",
        "부동산", "유가", "금", "달러", "엔화",
    ]
    counter = Counter()
    for kw in trend_keywords:
        c = text.count(kw)
        if c > 0:
            counter[kw] = c

    top_keywords = [kw for kw, _ in counter.most_common(8)]

    return {
        "sentiment": sentiment,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "ratio": ratio,
        "top_keywords": top_keywords,
    }


def process_news(raw_data):
    """수집된 원본 뉴스를 가공
    - 카테고리 분류
    - 버핏 태그
    - 키포인트 추출
    - 헤드라인 선별
    - 시장 분위기 분석
    """
    items = raw_data.get("items", [])

    # 각 뉴스 가공
    processed = []
    for item in items:
        item["category"] = classify_category(item)
        item["buffett_tags"] = tag_buffett_principles(item)
        item["key_points"] = extract_key_points(item)
        processed.append(item)

    # 헤드라인 선별
    headlines = select_headlines(processed)

    # 카테고리별 그룹핑
    grouped = group_by_category(processed)

    # 시장 분위기
    pulse = analyze_market_pulse(processed)

    return {
        "generated_at": raw_data.get("generated_at"),
        "total_count": raw_data.get("total_count", len(processed)),
        "headlines": headlines,
        "grouped": grouped,
        "pulse": pulse,
        "all_items": processed,
    }
