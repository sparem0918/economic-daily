# -*- coding: utf-8 -*-
"""
뉴스 수집기
- 여러 RSS 피드에서 뉴스를 병렬로 수집
- 중복 제거 및 시간 필터링
- 캐시 처리
"""
import os
import json
import time
import hashlib
import re
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

import config


def _clean_html(text):
    """HTML 태그 제거 및 공백 정리"""
    if not text:
        return ""
    soup = BeautifulSoup(text, "lxml")
    cleaned = soup.get_text(separator=" ", strip=True)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _parse_pub_date(entry):
    """게시 시각을 datetime으로 파싱 (KST 기준)"""
    # feedparser가 제공하는 published_parsed 우선 사용
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(
                timezone(timedelta(hours=9))
            )
        except Exception:
            pass

    # 백업: published 문자열을 직접 파싱
    if hasattr(entry, "published"):
        try:
            dt = date_parser.parse(entry.published)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
            return dt.astimezone(timezone(timedelta(hours=9)))
        except Exception:
            pass

    # updated 백업
    if hasattr(entry, "updated"):
        try:
            dt = date_parser.parse(entry.updated)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
            return dt.astimezone(timezone(timedelta(hours=9)))
        except Exception:
            pass

    # 모두 실패하면 현재 시각
    return datetime.now(timezone(timedelta(hours=9)))


def _make_id(title, link):
    """뉴스 고유 ID 생성 (중복 제거용)"""
    raw = f"{title}|{link}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _fetch_one_feed(feed_info, timeout=10):
    """RSS 피드 1개를 가져와 파싱"""
    name = feed_info["name"]
    url = feed_info["url"]
    category = feed_info["category"]

    try:
        # User-Agent 설정으로 차단 회피
        feed = feedparser.parse(
            url,
            request_headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
    except Exception as e:
        print(f"[수집 실패] {name}: {e}")
        return []

    if feed.bozo and not feed.entries:
        print(f"[수집 경고] {name}: 피드를 읽지 못했습니다.")
        return []

    items = []
    for entry in feed.entries:
        title = _clean_html(getattr(entry, "title", ""))
        if not title:
            continue

        link = getattr(entry, "link", "")
        summary_raw = getattr(entry, "summary", "") or getattr(entry, "description", "")
        summary = _clean_html(summary_raw)

        pub_dt = _parse_pub_date(entry)

        items.append(
            {
                "id": _make_id(title, link),
                "title": title,
                "link": link,
                "summary": summary,
                "source": name,
                "source_category": category,
                "published": pub_dt.isoformat(),
                "published_dt": pub_dt,
            }
        )

    return items


def _cache_path():
    """캐시 파일 경로"""
    return os.path.join(config.CACHE_DIR, "news_cache.json")


def _load_cache():
    """캐시 로드 - 유효하면 반환, 만료되면 None"""
    path = _cache_path()
    if not os.path.exists(path):
        return None

    try:
        mtime = os.path.getmtime(path)
        age_minutes = (time.time() - mtime) / 60
        if age_minutes > config.CACHE_TTL_MINUTES:
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[캐시 로드 실패]: {e}")
        return None


def _save_cache(data):
    """캐시 저장"""
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    try:
        with open(_cache_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        print(f"[캐시 저장 실패]: {e}")


def collect_news(force_refresh=False):
    """모든 RSS 피드에서 뉴스를 수집하고 정리하여 반환"""
    # 캐시 확인
    if not force_refresh:
        cached = _load_cache()
        if cached:
            print(f"[캐시 사용] {len(cached.get('items', []))}건")
            return cached

    print(f"[뉴스 수집 시작] {len(config.RSS_FEEDS)}개 피드")
    all_items = []

    # 병렬 수집
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(_fetch_one_feed, feed): feed for feed in config.RSS_FEEDS
        }
        for future in as_completed(futures):
            try:
                items = future.result()
                all_items.extend(items)
                feed_name = futures[future]["name"]
                print(f"  - {feed_name}: {len(items)}건")
            except Exception as e:
                print(f"  - 오류: {e}")

    # 중복 제거 (같은 ID는 제거)
    seen = set()
    unique = []
    for item in all_items:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)

    # 시간 윈도우 필터링 (최근 N시간)
    now_kst = datetime.now(timezone(timedelta(hours=9)))
    cutoff = now_kst - timedelta(hours=config.NEWS_HOURS_WINDOW)

    filtered = [item for item in unique if item["published_dt"] >= cutoff]

    # 시간 윈도우 안에 뉴스가 너무 적으면 시간 제한 완화
    if len(filtered) < 20:
        filtered = unique

    # 시간 역순 정렬
    filtered.sort(key=lambda x: x["published_dt"], reverse=True)

    # datetime을 문자열로 변환 (JSON 직렬화 위해)
    for item in filtered:
        item["published_dt"] = item["published_dt"].isoformat()

    result = {
        "generated_at": now_kst.isoformat(),
        "total_count": len(filtered),
        "items": filtered,
    }

    _save_cache(result)
    print(f"[수집 완료] 총 {len(filtered)}건")
    return result


if __name__ == "__main__":
    # 단독 실행 시 테스트
    data = collect_news(force_refresh=True)
    print(f"\n총 {data['total_count']}건 수집")
    for item in data["items"][:5]:
        print(f"- [{item['source']}] {item['title']}")
