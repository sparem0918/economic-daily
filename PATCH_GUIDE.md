# 트럼프 임팩트 트래커 — 적용 가이드

`economic_news_app` 프로젝트에 끼워 넣는 애드온입니다.
새 파일 3개를 복사하고, 기존 파일 2개에 5줄 정도만 추가하면 됩니다.

## 1. 추가되는 기능

페이지 상단(헤드라인 섹션 아래)에 "트럼프 영향" 섹션이 새로 생깁니다.

- 최근 48시간 동안 수집된 뉴스 중 **트럼프·美 행정부 언급 뉴스만** 자동 필터링
- 정책·산업 토픽별로 자동 분류
  - 양자컴퓨터 / 관세·무역 / 반도체 / 자동차 / 조선 / 원자력·에너지 / 방산·우주 / 암호화폐 / AI·빅테크 / 중국 견제
- 각 토픽마다 **시장에서 통상 묶이는 한국 관련주** 자동 표시 (종목명·코드·시장 구분)
- 토픽별 헤드라인 점수로 정렬, 카테고리별 상위 5건만 노출
- 다크모드 자동 대응

## 2. 파일 복사

압축을 풀면 다음 4개 파일이 있습니다. 기존 `economic_news_app` 폴더의 같은 위치에 그대로 복사하세요.

```
economic_news_app/
├── trump_config.py                       ← 신규 (루트에 추가)
├── trump_tracker.py                      ← 신규 (루트에 추가)
├── templates/
│   └── _trump_section.html               ← 신규 (templates 폴더에 추가)
└── static/
    └── trump_style.css                   ← 신규 (static 폴더에 추가)
```

이 4개는 기존 파일을 덮어쓰지 않습니다.

## 3. 기존 파일 2개 수정

### 3-1. `app.py` 와 `build_static.py` 둘 다 동일하게 수정

`app.py`(로컬 실행용)와 `build_static.py`(GitHub Pages 빌드용) **두 파일 모두** 같은 수정이 필요합니다.

**(a) 파일 상단의 import 영역에 한 줄 추가**

기존 코드 어딘가에 `import news_summarizer` 또는 `from news_summarizer import ...` 가 있을 텐데, 그 근처에 추가하세요.

```python
import trump_tracker
```

**(b) 템플릿 렌더링 직전에 트럼프 섹션 데이터 생성**

코드에서 `render_template("newsletter.html", ...)` 또는 비슷한 호출이 있는 부분을 찾습니다. 그 호출 **직전에** 다음을 추가하고, 호출 인자에 `trump_section=trump_section` 을 추가하세요.

수정 전(예시):
```python
processed = news_summarizer.process_news(raw)
html = render_template(
    "newsletter.html",
    items=processed["items"],
    headlines=processed["headlines"],
    pulse=processed["pulse"],
    grouped=processed["grouped"],
    buffett=buffett_data,
    generated_at=processed["generated_at"],
)
```

수정 후:
```python
processed = news_summarizer.process_news(raw)
trump_section = trump_tracker.build_trump_section(processed["items"])   # ← 추가
html = render_template(
    "newsletter.html",
    items=processed["items"],
    headlines=processed["headlines"],
    pulse=processed["pulse"],
    grouped=processed["grouped"],
    buffett=buffett_data,
    generated_at=processed["generated_at"],
    trump_section=trump_section,                                         # ← 추가
)
```

> 변수명(`processed`, `raw`)은 본인 코드 기준으로 맞춰 쓰세요. 핵심은 **process_news 가 만든 items 리스트를 `trump_tracker.build_trump_section()` 에 넘기고, 결과를 템플릿에 전달**하는 두 가지입니다.

### 3-2. `templates/newsletter.html` 에 두 군데 추가

**(a) `<head>` 안에서 기존 CSS 링크 바로 다음 줄에 추가**

```html
<link rel="stylesheet" href="static/trump_style.css">
```

또는 Flask 사용 시:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='trump_style.css') }}">
```

**(b) 트럼프 섹션을 표시할 위치에 include 추가**

추천 위치는 "오늘의 헤드라인" 섹션 바로 아래입니다. 적당한 곳에 한 줄만 넣으면 됩니다.

```html
{% include '_trump_section.html' %}
```

> 트럼프 관련 뉴스가 0건이면 섹션 자체가 자동으로 숨겨지도록 템플릿에 조건이 들어 있습니다. 빈 박스가 표시될 걱정은 없습니다.

### 3-3. (선택) `config.py` 에 트럼프 RSS 피드 추가

기본 RSS 피드만으로도 작동하지만, 글로벌·국제 카테고리 피드를 추가하면 트럼프 뉴스 수집량이 늘어납니다.

`config.py` 의 `RSS_FEEDS = [...]` 리스트 **마지막에** 다음을 추가:

```python
# === 트럼프 트래커 보강용 ===
{"name": "한국경제 국제", "url": "https://rss.hankyung.com/feed/international.xml", "category": "글로벌"},
{"name": "한국경제 정치", "url": "https://rss.hankyung.com/feed/politics.xml", "category": "글로벌"},
{"name": "매일경제 국제", "url": "https://www.mk.co.kr/rss/30300018/", "category": "글로벌"},
{"name": "이투데이 증권", "url": "https://www.etoday.co.kr/rss/rss_section.xml?id=22", "category": "증시"},
```

또는 `trump_config.py` 에 정의된 목록을 그대로 끌어다 쓰는 방법도 있습니다.

`config.py` 끝부분에 추가:
```python
from trump_config import TRUMP_RSS_FEEDS
RSS_FEEDS.extend(TRUMP_RSS_FEEDS)
```

## 4. 동작 확인 (로컬)

```cmd
run.bat
```

PC 브라우저에서 `http://localhost:5000` 접속 → 상단 헤드라인 아래에 빨간 줄로 강조된 **"트럼프 영향"** 섹션이 보이면 정상.

트럼프 관련 뉴스가 시간상 없으면 섹션이 표시되지 않습니다. 이 경우 시간 윈도우를 늘려서 테스트:

```python
# trump_config.py
TRUMP_NEWS_HOURS_WINDOW = 168  # 7일
```

## 5. GitHub Pages 배포 적용

이미 GitHub Pages + Actions 로 배포 중이시면 git 으로 푸시만 하면 자동 재빌드됩니다.

```cmd
git add .
git commit -m "Add Trump impact tracker"
git push
```

푸시 후 GitHub 의 **Actions 탭**에서 워크플로 실행 상태를 확인하세요. 3분 정도 후 사이트가 갱신됩니다.

## 6. 커스터마이징 가이드

### 토픽 추가/수정
`trump_config.py` 의 `TRUMP_TOPICS` 사전에서 추가·삭제·키워드 수정 가능합니다.

```python
TRUMP_TOPICS["바이오"] = {
    "icon": "✚",
    "keywords": ["FDA", "임상", "신약", "바이오"],
    "description": "FDA 정책 변화와 한국 바이오 영향",
}
```

### 관련주 목록 변경
`TOPIC_STOCKS` 사전 수정. 시장 테마 분류는 시간이 지나면 바뀌니 분기에 한 번씩 점검 권장.

### 시간 윈도우 변경
```python
# trump_config.py
TRUMP_NEWS_HOURS_WINDOW = 24  # 기본 48시간 → 24시간
```

### 표시 개수 조정
```python
MAX_TOPICS_DISPLAYED = 6      # 화면에 보일 토픽 카드 수
MAX_NEWS_PER_TOPIC = 3        # 토픽당 뉴스 개수
MAX_STOCKS_PER_TOPIC = 4      # 토픽당 관련주 칩 개수
```

## 7. 문제 해결

**섹션이 안 보임**
- 트럼프 키워드를 포함한 뉴스가 윈도우 내(48시간)에 없을 가능성. `trump_config.py` 의 `TRUMP_NEWS_HOURS_WINDOW` 를 168로 늘려 보세요.
- `app.py` 에서 `trump_section=trump_section` 인자를 빠뜨렸는지 확인.

**ImportError: No module named 'trump_config'**
- `trump_config.py` 와 `trump_tracker.py` 가 `app.py` 와 같은 폴더에 있어야 합니다.

**스타일이 안 먹힘**
- `newsletter.html` 에서 `trump_style.css` 링크가 누락됐는지 확인.
- 브라우저 캐시. `Ctrl+Shift+R` 로 강제 새로고침.

**한국 관련주 칩이 안 보임**
- 해당 토픽이 `TOPIC_STOCKS` 사전에 정의되지 않은 경우. 직접 추가하시거나 빈 리스트로 두면 됩니다.

## 8. 버핏 원칙과의 관계

트럼프 임팩트 트래커는 **테마 모니터링용**이며 매수 신호가 아닙니다.
한국 관련주 칩에 표시된 종목들은 **시장이 통상 묶는 테마 분류**이고, 실제 사업 연관성·재무 안정성·해자 여부는 별도로 검증해야 합니다.

`buffett_investment_method_korean.md` 의 11~17번 섹션(종목 검토 순서, 매수 전 질문)을 함께 참고하세요. 특히:

- 사업 이해도(11-1): 트럼프 정책 수혜만으로 매수하지 말고, 실제 매출 구조에서 관련 사업 비중을 확인
- 5년 매출·이익 추이(11-2): 단발성 테마인지 구조적 수혜인지 구분
- 부채 안정성(11-6): 테마주 상승 후 유상증자·CB 발행 이력 점검
- 밸류에이션(11-8): 급등 후 PER·PBR이 이미 과열 구간인지 확인

## 9. 라이선스 / 면책

본 도구는 공개 RSS 기반의 보조 정보 제공 목적이며, 종목 추천이 아닙니다.
관련주 매핑은 작성 시점의 시장 통상 분류이고 시점에 따라 변경됩니다.
투자 판단과 그 결과에 대한 책임은 전적으로 본인에게 있습니다.
