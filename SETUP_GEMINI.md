# AI 종합 요약 추가하기 (Gemini API)

매시간 GitHub 서버가 RSS를 수집한 뒤, Google Gemini AI를 호출해 **하루 경제 뉴스를 한 문단으로 종합 요약**한 "데일리 브리프"를 페이지 상단에 표시하는 기능입니다.

비용은 **무료**입니다. Google Gemini 2.5 Flash 무료 티어는 하루 1500회 호출이 가능한데, 우리 앱은 매시간 1번만 호출하므로 하루 24회 → 한도의 1.6%만 사용합니다.

전체 설정 시간은 약 **6분**입니다.

---

## 1단계. Gemini API 키 발급 (5분)

**1)** https://aistudio.google.com/apikey 접속

**2)** 본인 Google 계정으로 로그인

**3)** **"+ Create API key"** 버튼 클릭

**4)** 프로젝트 선택 창이 뜨면 **"Create API key in new project"** 선택

**5)** 발급된 API 키가 표시됩니다. 다음과 같은 형태입니다:

```
AIzaSyA-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**복사 아이콘을 눌러 키를 복사**하세요. (창을 닫기 전에 꼭 복사. 나중에 다시 확인할 수도 있지만 번거롭습니다)

> ⚠️ **이 키는 비밀번호와 같습니다.** 절대 코드에 직접 적거나, GitHub에 그대로 올리거나, 다른 사람에게 공유하지 마세요. 노출되면 즉시 https://aistudio.google.com/apikey 에서 삭제하고 새로 만드세요.

---

## 2단계. GitHub Secret에 등록 (1분)

GitHub Secrets는 API 키 같은 민감 정보를 안전하게 보관하는 GitHub 기능입니다. Actions 워크플로에서만 읽을 수 있고, 외부에서는 절대 볼 수 없습니다.

**1)** 본인 repo 페이지로 이동 (`https://github.com/본인아이디/economic-daily`)

**2)** 상단 **Settings** 탭 클릭

**3)** 좌측 메뉴에서 **Secrets and variables → Actions** 클릭

**4)** **New repository secret** 버튼 클릭

**5)** 다음과 같이 입력:
   - **Name**: `GEMINI_API_KEY` (이름은 반드시 이걸로. 대소문자 정확히)
   - **Secret**: 1단계에서 복사한 키를 그대로 붙여넣기

**6)** **Add secret** 클릭

---

## 3단계. 적용된 코드를 GitHub에 푸시 (1분)

새 zip에는 Gemini 통합 코드(`gemini_summarizer.py`, 템플릿/CSS 업데이트, 워크플로 수정)가 포함되어 있습니다. 이 파일들을 본인 repo에 반영해야 합니다.

cmd로 `economic_news_app` 폴더에서:

```cmd
git add .
git commit -m "Add Gemini AI daily brief"
git push
```

푸시 즉시 GitHub Actions가 자동으로 빌드를 시작합니다. **Actions** 탭에서 진행 상황을 볼 수 있고, 보통 2~3분 안에 완료됩니다.

---

## 4단계. 확인

빌드 완료 후 본인 사이트 (`https://본인아이디.github.io/economic-daily/`)를 새로고침하면, **시장 펄스 아래·헤드라인 위**에 다음과 같은 새 섹션이 보입니다.

```
● DAILY BRIEF ── 오늘의 종합                       AI 종합 요약

오늘 한국 경제는 삼성전자가 노사 임금협상 타결과 함께 8% 급등하며
코스피 사상 최고가를 견인했다. 반도체 호황으로 상위 10대 대기업
수출 비중이 사상 첫 50%를 돌파했으며, 한국은행은 기준금리를...

→ 삼성전자 8% 급등, 그룹 시총 2200조원 돌파
→ 반도체 수출 비중 사상 첫 50% 돌파
→ 한은 기준금리 동결, 환율 1380원대 안정

5건의 뉴스 종합                                   GEMINI-2.5-FLASH
```

이 섹션은 매시간 빌드 때마다 새로 생성됩니다.

---

## 작동 방식

- 워크플로가 RSS로 뉴스를 수집
- 수집된 뉴스의 제목 + 핵심 포인트를 Gemini에 보냄
- Gemini가 한 문단 요약 + 3개 포인트를 JSON으로 응답
- 응답을 HTML에 삽입해 정적 배포

**무료 한도 관리**: 시간당 1회 호출 = 하루 24회 사용. Gemini 2.5 Flash 무료 한도(하루 1500회)의 1.6%만 사용하므로 한도 초과 걱정은 없습니다.

**비용 0원**: 코드 카드 등록 없이도 사용 가능. 한도 초과 시에도 청구되지 않고 호출만 거부됩니다.

---

## 문제 해결

### 브리프 섹션이 안 보일 때

GitHub Actions의 빌드 로그를 확인하세요. **Actions 탭 → 최근 빌드 → Build static site 단계**에서 다음 중 하나가 보일 겁니다.

| 로그 메시지 | 의미 | 해결 |
|---|---|---|
| `[Gemini] GEMINI_API_KEY 환경변수가 없어 요약 생성을 건너뜁니다.` | Secret 미등록 또는 이름 오타 | Secret 이름을 `GEMINI_API_KEY`로 정확히 다시 등록 |
| `[Gemini] HTTP 오류: 400` | 잘못된 API 키 | 키를 다시 발급해서 Secret 갱신 |
| `[Gemini] HTTP 오류: 429` | 한도 초과 (거의 발생 안 함) | 1시간 기다리거나 모델을 `gemini-2.5-flash-lite`로 변경 |
| `[Gemini] 요약 완료` | 정상 작동 ✓ | 페이지 새로고침 |

### 모델 변경하기

`config.py`에서 `GEMINI_MODEL` 값을 바꾸고 푸시하면 됩니다.

```python
GEMINI_MODEL = "gemini-2.5-flash"        # 기본 (권장)
# GEMINI_MODEL = "gemini-2.5-flash-lite" # 더 빠르고 RPM 2배, 품질 약간 ↓
# GEMINI_MODEL = "gemini-3.5-flash"      # 최신 (2026-05 출시, 무료)
```

### 로컬에서 테스트하려면

Windows cmd에서:

```cmd
set GEMINI_API_KEY=AIzaSy...본인키
python app.py
```

또는 `run.bat` 실행 전에 위 `set` 명령을 한 번 실행하면 됩니다.

---

## 끝!

이제 매시간마다 AI가 그 시점까지의 한국 경제 뉴스를 자동으로 종합 요약해서 페이지 상단에 보여줍니다. PC를 켜둘 필요 없이, 어디서든 모바일·PC로 접속하면 됩니다.
