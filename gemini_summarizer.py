# -*- coding: utf-8 -*-
"""
Gemini API 종합 요약 생성기
- gemini-2.5-flash 무료 티어 (하루 1500회) 사용
- 환경변수 GEMINI_API_KEY 필요. 없으면 None 반환하고 앱은 정상 동작
- 30분 캐시로 동일 뉴스에 대한 중복 호출 방지
"""
import os
import re
import json
import time
import requests
from datetime import datetime, timezone, timedelta

import config


GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
DEFAULT_MODEL = "gemini-2.5-flash"
CACHE_PATH = os.path.join("cache", "brief_cache.json")
CACHE_TTL_MINUTES = 30


def _build_prompt(items, max_items=40):
    """수집된 뉴스로부터 LLM 프롬프트 생성

    토큰을 아끼기 위해 상위 max_items 건만 사용한다.
    각 뉴스는 카테고리, 제목, 첫 번째 핵심 포인트만 포함.
    """
    selected = items[:max_items]

    news_lines = []
    for i, item in enumerate(selected, 1):
        title = item.get("title", "").strip()
        key_points = item.get("key_points") or []
        first_point = (
            key_points[0] if key_points else item.get("summary", "")[:160]
        )
        cat = item.get("category", "")
        news_lines.append(f"{i}. [{cat}] {title}\n   {first_point}")

    news_block = "\n".join(news_lines)

    now_kst = datetime.now(timezone(timedelta(hours=9)))
    date_str = now_kst.strftime("%Y년 %m월 %d일")

    prompt = f"""당신은 한국 경제 뉴스를 한 문단으로 종합 요약하는 신문 기자입니다.

오늘 날짜: {date_str}

다음은 오늘 수집된 한국 경제 뉴스 {len(selected)}건입니다.

{news_block}

위 뉴스를 종합해서 작성하세요.

요구사항:
1. summary: 3~4문장으로 오늘 한국 경제의 핵심 흐름을 요약 (증시·산업·금융·정책 중 가장 중요한 이슈 중심)
2. points: 2~3개의 짧은 불릿 포인트. 각 항목은 한 줄 (40자 이내). 투자자가 주목할 변화·숫자·이벤트
3. 톤은 차분하고 객관적인 신문 브리프 스타일
4. 추측, 매수 추천, 미래 예측은 절대 하지 말 것
5. 종목명·기관명·숫자 같은 구체적 사실만 인용, 출처 자체는 표시하지 않음
6. summary는 400자 이내

반드시 다음 JSON 형식으로만 답하세요. 다른 텍스트를 추가하지 마세요.

{{
  "summary": "핵심 흐름 문단",
  "points": ["주목 포인트 1", "주목 포인트 2", "주목 포인트 3"]
}}
"""
    return prompt


def _load_cache():
    """캐시 로드 (유효하면 dict 반환, 아니면 None)"""
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        mtime = os.path.getmtime(CACHE_PATH)
        age_min = (time.time() - mtime) / 60
        if age_min > CACHE_TTL_MINUTES:
            return None
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(data):
    """캐시 저장"""
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Gemini] 캐시 저장 실패: {e}")


def _extract_json(text):
    """LLM 응답에서 JSON 부분만 추출
    - ```json ... ``` 코드블록 케이스
    - 그냥 { ... } 가 본문에 있는 케이스
    - 전체가 JSON인 케이스 (responseMimeType 사용 시)
    """
    if not text:
        return None

    # 코드블록 우선
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        return m.group(1)

    # 첫 { 부터 마지막 } 까지
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return None


def generate_brief(items, force_refresh=False):
    """Gemini로 종합 요약 생성

    Args:
        items: list of news dict (from news_summarizer.process_news)
        force_refresh: True면 캐시 무시

    Returns:
        dict {"summary": str, "points": list[str], "generated_at": str, "model": str}
        또는 None (API 키 없음, API 호출 실패, 응답 파싱 실패 시)
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[Gemini] GEMINI_API_KEY 환경변수가 없어 요약 생성을 건너뜁니다.")
        return None

    if not items:
        return None

    # 캐시 확인
    if not force_refresh:
        cached = _load_cache()
        if cached:
            print("[Gemini] 캐시된 요약 사용")
            return cached

    model = getattr(config, "GEMINI_MODEL", DEFAULT_MODEL)
    url = GEMINI_API_URL.format(model=model)
    prompt = _build_prompt(items)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }

    response = None
    try:
        print(f"[Gemini] {model} 호출 중... (뉴스 {len(items)}건)")
        response = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        # 응답 구조: candidates[0].content.parts[0].text
        candidates = data.get("candidates", [])
        if not candidates:
            print(f"[Gemini] candidates 비어 있음. 응답: {str(data)[:300]}")
            return None

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            print(f"[Gemini] parts 비어 있음. 응답: {str(data)[:300]}")
            return None

        text = parts[0].get("text", "")
        json_text = _extract_json(text)
        if not json_text:
            print(f"[Gemini] JSON 추출 실패. 원본: {text[:300]}")
            return None

        result = json.loads(json_text)

        # 검증
        if not isinstance(result, dict) or "summary" not in result:
            print(f"[Gemini] 응답 구조 오류: {result}")
            return None

        # points 정규화
        points = result.get("points", [])
        if not isinstance(points, list):
            points = []
        points = [str(p).strip() for p in points if p]

        normalized = {
            "summary": str(result["summary"]).strip(),
            "points": points[:5],  # 최대 5개
            "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
            "model": model,
            "news_count": len(items),
        }

        _save_cache(normalized)
        print(
            f"[Gemini] 요약 완료: summary {len(normalized['summary'])}자, "
            f"points {len(normalized['points'])}개"
        )
        return normalized

    except requests.exceptions.HTTPError as e:
        msg = response.text[:300] if response is not None else ""
        print(f"[Gemini] HTTP 오류: {e}\n  응답: {msg}")
        return None
    except requests.exceptions.Timeout:
        print("[Gemini] 타임아웃")
        return None
    except json.JSONDecodeError as e:
        print(f"[Gemini] JSON 파싱 실패: {e}")
        return None
    except Exception as e:
        print(f"[Gemini] 예상치 못한 오류: {e}")
        return None


if __name__ == "__main__":
    # 단독 실행 시 더미 테스트
    test_items = [
        {
            "title": "코스피 사상 최고치 돌파",
            "category": "증시",
            "key_points": ["코스피가 외국인 1조원 순매수로 3000선 돌파"],
        }
    ]
    result = generate_brief(test_items, force_refresh=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
