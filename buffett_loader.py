# -*- coding: utf-8 -*-
"""
버핏 투자 방식 로더
- MD 파일에서 핵심 체크리스트 추출
- 매수 전 마지막 질문 추출
- 일일 뉴스레터에 같이 표시할 인사이트 추출
"""
import os
import re
import random


def load_buffett_md(path="data/buffett_investment_method_korean.md"):
    """버핏 MD 파일 로드"""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_final_questions(md_text):
    """'매수 전 마지막 질문' 섹션 추출"""
    if not md_text:
        return []

    # 17번 섹션 찾기
    pattern = r"## 17\. 매수 전 마지막 질문(.*?)(?=## \d+\.)"
    match = re.search(pattern, md_text, re.DOTALL)
    if not match:
        return []

    section = match.group(1)
    # 번호 매겨진 질문 추출
    questions = re.findall(r"\d+\.\s*(.+?\?)", section)
    return [q.strip() for q in questions]


def extract_principles(md_text):
    """핵심 투자 원칙 표 추출 (2번 섹션)"""
    if not md_text:
        return []

    pattern = r"## 2\. 버핏식 투자 원칙(.*?)(?=## \d+\.)"
    match = re.search(pattern, md_text, re.DOTALL)
    if not match:
        return []

    section = match.group(1)
    # 표 행 추출
    rows = re.findall(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", section)

    principles = []
    for row in rows:
        principle, content, application = row
        # 헤더와 구분선 건너뛰기
        if principle.strip() in ["원칙", "---", ""] or "---" in principle:
            continue
        principles.append({
            "principle": principle.strip(),
            "content": content.strip(),
            "application": application.strip(),
        })
    return principles


def extract_one_liner(md_text):
    """한 줄 결론 추출"""
    if not md_text:
        return ""
    pattern = r"## 18\. 한 줄 결론.*?>\s*\*\*(.+?)\*\*"
    match = re.search(pattern, md_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def get_daily_checkpoint(md_text):
    """오늘의 체크포인트 1개를 선택해서 반환
    - 매일 다른 체크포인트를 보여줌 (날짜 기반 시드)
    """
    from datetime import datetime
    questions = extract_final_questions(md_text)
    principles = extract_principles(md_text)

    if not questions and not principles:
        return None

    # 오늘 날짜 기반 결정론적 선택
    today = datetime.now().date()
    seed = int(today.strftime("%Y%m%d"))
    rng = random.Random(seed)

    if principles and rng.random() < 0.6:
        # 60% 확률로 원칙 표시
        chosen = rng.choice(principles)
        return {
            "type": "principle",
            "title": chosen["principle"],
            "content": chosen["content"],
            "application": chosen["application"],
        }
    elif questions:
        chosen = rng.choice(questions)
        return {
            "type": "question",
            "title": "오늘의 점검 질문",
            "content": chosen,
            "application": "이 질문에 답할 수 없다면, 그 종목은 아직 살 준비가 되지 않았습니다.",
        }
    return None


def get_buffett_context():
    """뉴스레터에 표시할 버핏 컨텍스트 일체 반환"""
    md_text = load_buffett_md()
    if not md_text:
        return {
            "available": False,
            "one_liner": "",
            "daily_checkpoint": None,
            "questions": [],
        }

    return {
        "available": True,
        "one_liner": extract_one_liner(md_text),
        "daily_checkpoint": get_daily_checkpoint(md_text),
        "questions": extract_final_questions(md_text),
    }
