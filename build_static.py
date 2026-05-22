# -*- coding: utf-8 -*-
"""
정적 사이트 빌더 (GitHub Pages 배포용)
- Flask test_client로 HTML 한 장을 추출
- /static/style.css 등을 상대 경로로 치환
- site/ 폴더에 index.html, static/, .nojekyll 생성
- 뉴스 0건이면 빌드 실패로 종료 (이전 배포 유지)
"""
import os
import sys
import shutil
import json
from datetime import datetime, timezone, timedelta

# Flask 앱 임포트
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app
import news_collector
import news_summarizer

OUTPUT_DIR = "site"


def ensure_clean_output():
    """출력 디렉터리 초기화"""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "static"), exist_ok=True)


def copy_static_files():
    """CSS 등 정적 파일 복사"""
    src = "static"
    dst = os.path.join(OUTPUT_DIR, "static")
    if os.path.exists(src):
        for fname in os.listdir(src):
            shutil.copy(os.path.join(src, fname), os.path.join(dst, fname))
            print(f"  복사: static/{fname}")


def rewrite_paths_for_static(html):
    """정적 호스팅에 맞게 HTML 경로 치환
    - /static/* → static/* (상대 경로, 어떤 base URL에서도 동작)
    - window.location.href = '/?refresh=1' → window.location.reload()
      (정적 사이트에서 쿼리 새로고침은 무의미하므로 단순 reload)
    """
    import re

    html = html.replace('href="/static/', 'href="static/')
    html = html.replace('src="/static/', 'src="static/')

    # 새로고침 핸들러: 따옴표/공백 변형까지 모두 치환
    # window.location.href='/?refresh=1' 또는
    # window.location.href = "/?refresh=1" 등
    html = re.sub(
        r"""window\.location\.href\s*=\s*['"]/\?refresh=1['"]""",
        "window.location.reload()",
        html,
    )
    return html


def add_build_meta(html):
    """빌드 메타 정보를 HTML 끝에 주석으로 추가"""
    now_kst = datetime.now(timezone(timedelta(hours=9)))
    meta = (
        f"\n<!-- "
        f"Built at {now_kst.isoformat()} | "
        f"Source: economic-news-app | "
        f"Static build for GitHub Pages "
        f"-->\n"
    )
    return html + meta


def build_index_html():
    """메인 페이지 HTML 빌드"""
    # 강제 새로고침으로 최신 뉴스 수집
    raw = news_collector.collect_news(force_refresh=True)
    if raw.get("total_count", 0) == 0:
        print("=" * 60)
        print("[빌드 중단] 수집된 뉴스가 0건입니다.")
        print("이전 배포를 유지하기 위해 빌드를 실패 처리합니다.")
        print("=" * 60)
        sys.exit(1)

    # Flask 라우트를 통해 렌더링
    with app.app.test_client() as client:
        response = client.get("/")
        if response.status_code != 200:
            print(f"[오류] HTTP 상태 코드 {response.status_code}")
            sys.exit(1)
        html = response.get_data(as_text=True)

    html = rewrite_paths_for_static(html)
    html = add_build_meta(html)

    out_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  생성: index.html ({len(html):,} 자, 뉴스 {raw['total_count']}건)")


def build_api_json():
    """JSON 데이터 부가 생성 (외부에서 데이터만 가져갈 수 있도록)"""
    with app.app.test_client() as client:
        response = client.get("/api/news")
        if response.status_code != 200:
            return
        data = response.get_json()

    api_dir = os.path.join(OUTPUT_DIR, "api")
    os.makedirs(api_dir, exist_ok=True)
    out_path = os.path.join(api_dir, "news.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"  생성: api/news.json")


def create_nojekyll():
    """GitHub Pages가 _로 시작하는 폴더를 무시하지 않도록 설정"""
    with open(os.path.join(OUTPUT_DIR, ".nojekyll"), "w") as f:
        pass
    print(f"  생성: .nojekyll")


def create_robots_txt():
    """기본 robots.txt"""
    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n")
    print(f"  생성: robots.txt")


def main():
    print("=" * 60)
    print("Economic Daily - Static Site Builder")
    print("=" * 60)

    ensure_clean_output()
    copy_static_files()
    build_index_html()
    build_api_json()
    create_nojekyll()
    create_robots_txt()

    print("=" * 60)
    print(f"[빌드 성공] 출력 디렉터리: {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
