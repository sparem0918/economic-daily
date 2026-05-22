# GitHub Pages 배포 가이드

이 문서는 본 앱을 GitHub Pages에 무료로 배포해서, 내 PC를 켜지 않고도 어디서든 모바일·PC로 접속할 수 있게 하는 방법을 단계별로 안내합니다.

배포가 완료되면 다음과 같은 상태가 됩니다.

- 매시간 GitHub 서버가 알아서 RSS를 수집하고 HTML을 빌드합니다.
- 빌드된 HTML이 자동으로 GitHub Pages에 배포됩니다.
- `https://본인아이디.github.io/저장소명/` 주소로 모바일에서도 접속됩니다.
- 본인 PC는 꺼져 있어도 됩니다.
- 완전 무료입니다.

---

## 1단계. GitHub 계정과 Git 준비

1. https://github.com 에서 무료 가입합니다.
2. Windows라면 https://git-scm.com/download/win 에서 Git을 설치합니다.
3. 설치 후 `cmd`에서 한 번만 본인 정보를 설정합니다.

```bash
git config --global user.name "본인이름"
git config --global user.email "본인이메일@example.com"
```

---

## 2단계. 새 저장소(repository) 만들기

1. GitHub 우상단 **+ 버튼 → New repository** 클릭
2. **Repository name**: 예) `economic-daily`
3. **Public** 선택 (Public이어야 GitHub Actions가 무제한 무료입니다)
4. **Add a README file** 체크하지 말기 (이미 있음)
5. **Create repository** 클릭

---

## 3단계. 코드 업로드

방법은 두 가지입니다. 편한 쪽으로 진행하세요.

### 방법 A. 명령줄 (권장)

압축을 푼 `economic_news_app` 폴더에서 `cmd`를 열고 다음을 차례대로 실행합니다.

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/본인아이디/economic-daily.git
git push -u origin main
```

마지막 푸시 단계에서 GitHub 로그인 창이 뜨면 로그인합니다.

### 방법 B. 웹 업로드

1. 만든 저장소 페이지로 이동
2. **uploading an existing file** 링크 클릭
3. `economic_news_app` 안의 **모든 파일과 폴더**를 드래그해서 업로드
   (`.github` 폴더가 빠지지 않도록 주의. 숨김 폴더라 못 보일 수 있으니 탐색기에서 숨김 파일 보이기 설정 필요)
4. **Commit changes** 클릭

---

## 4단계. GitHub Pages 활성화

1. 저장소 페이지에서 **Settings** 탭 클릭
2. 왼쪽 메뉴에서 **Pages** 클릭
3. **Source** 항목에서:
   - **Deploy from a branch** 선택
   - **Branch**: `gh-pages` 선택 (처음에는 없을 수 있음. 5단계 진행 후 다시 와서 설정)
   - **Folder**: `/ (root)` 선택
   - **Save** 클릭

---

## 5단계. 첫 빌드 실행

자동으로 매시간 도는 워크플로가 있지만, 첫 회는 수동 실행이 빠릅니다.

1. 저장소의 **Actions** 탭 클릭
2. 왼쪽 목록에서 **Build and Deploy to GitHub Pages** 선택
3. 오른쪽 위 **Run workflow** 드롭다운 → **Run workflow** 버튼 클릭
4. 1~3분 기다리면 워크플로가 초록색 체크로 완료됨
5. 완료되면 `gh-pages` 브랜치가 자동 생성됨
6. **Settings → Pages**로 다시 가서 **Branch**를 `gh-pages`로 지정 (안 되어 있으면)

---

## 6단계. 접속 확인

빌드 완료 후 1~2분 더 기다린 뒤 다음 주소로 접속합니다.

```
https://본인아이디.github.io/economic-daily/
```

성공하면 신문 스타일의 뉴스레터가 보입니다. 모바일에서도 같은 주소로 접속됩니다.

---

## 자동 갱신 주기

`.github/workflows/build.yml`에 정의된 cron 식이 매시간 정각에 빌드를 실행합니다. 다음과 같이 변경할 수 있습니다.

| 갱신 주기 | cron 식 |
|---|---|
| 매시간 (기본값) | `0 * * * *` |
| 30분마다 | `*/30 * * * *` |
| 매일 오전 7시 KST | `0 22 * * *` (KST는 UTC+9이므로 UTC 22시 = KST 7시) |
| 평일 출근 시간만 | `0 22-12/1 * * 0-4` |

수정 후 커밋·푸시하면 즉시 반영됩니다.

---

## 모바일 홈 화면에 추가

매일 보는 사이트이므로 휴대폰 홈 화면에 추가하면 앱처럼 쓸 수 있습니다.

**iPhone (Safari)**: 공유 버튼 → "홈 화면에 추가"
**Android (Chrome)**: 우상단 메뉴 → "홈 화면에 추가"

---

## 변경 사항 반영하는 법

`config.py`에서 RSS 피드를 추가하거나 디자인을 수정한 뒤:

```bash
git add .
git commit -m "RSS 피드 추가"
git push
```

푸시 즉시 워크플로가 트리거되어 1~3분 안에 배포됩니다.

---

## 문제 해결

### 워크플로가 실패할 때

- 저장소의 **Actions** 탭에서 실패한 빌드 클릭 → 로그 확인
- 가장 흔한 원인: **수집된 뉴스가 0건** (RSS 서버 일시 장애)
- 이 경우 의도적으로 빌드를 실패시켜 **이전 배포를 그대로 유지**합니다. 다음 시간 빌드에서 자동 복구됩니다.

### 페이지가 404일 때

- **Settings → Pages**에서 Branch가 `gh-pages`로 되어 있는지 확인
- 첫 배포 후 GitHub Pages CDN이 활성화되는 데 5~10분 걸릴 수 있음

### CSS가 깨져 보일 때

- 저장소 이름과 URL 경로가 일치하는지 확인 (`/economic-daily/` 부분)
- 다른 이름으로 만들었다면 그 이름으로 접속

### Actions 무료 한도

- Public repo면 **무제한 무료**입니다.
- Private repo도 월 2000분 무료. 1시간마다 빌드해도 한 달 약 30~60분만 사용합니다.

---

## 커스텀 도메인 (선택)

본인 도메인이 있다면 더 짧은 주소로 접속할 수 있습니다.

1. **Settings → Pages → Custom domain**에 도메인 입력
2. 도메인 DNS 설정에서 GitHub Pages IP 또는 CNAME으로 변경
3. HTTPS 자동 발급됨

자세한 절차는 GitHub 공식 가이드를 참조하세요.

---

## 비용 정리

| 항목 | 비용 |
|---|---|
| GitHub 계정 | 무료 |
| Public repo | 무료 |
| GitHub Actions (Public) | 무제한 무료 |
| GitHub Pages | 무료 (월 100GB 트래픽까지) |
| HTTPS | 무료 |
| **합계** | **0원** |
