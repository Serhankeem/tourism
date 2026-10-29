# currentourism 홈페이지·브랜드 UI 개편

Research PR #5가 병합된 최신 main에서 `feat/currentourism-home-redesign`을
분리했습니다. Research 엔진/DB를 초기화하거나 v0.4 PR을 다시 만들지 않았습니다.
이번 변경은 별도 UI PR이며 main에 직접 병합하지 않습니다.

## 구현

- Deep Blue `#173B73`, Orange `#F47735`, 밝은 배경 및 카드.
- 좌측 사이드바 제거. 모든 페이지에 동일한 상단 5개 메뉴와 활성 표시.
- 모바일 메뉴 열기/닫기, Escape·초점 복귀, 메뉴 선택 시 닫기.
- 전체 브랜드 영역은 키보드로 접근 가능한 Overview 홈 링크.
- 뉴스룸의 뉴스/리서치 보조 탭, 홈 리서치 링크와 `#research` 직접 접근.
- 주소 해시 및 뒤로/앞으로 이동 지원. 기존 `#sources`는 About의 출처 섹션.
- 홈 순서: Industry News + Market Weather → Key Indicators →
  Inbound Tourism + Analyst's Note. 모바일에서는 세로 배치.
- 홈 기사는 기존 Newsroom 데이터와 서버 편집 순서를 그대로 사용합니다.
  제목의 특정 키워드만으로 한국 관련성을 새로 추정하지 않습니다.
  원래 발행일을 표시하며 최근 24시간 발행 0건/데이터 없음 상태도 구분합니다.
- 홈 날씨는 기존 시뮬레이터 입력과 결과를 공유합니다. 계산식/초기화 보존,
  미검증 가중치 및 실제 시장 종합지수가 아님을 표시합니다.
- 기존 지표 수치·차트의 3개 관측 월·에디토리얼 기준일을 유지합니다.
  새 수치나 결측 월을 생성하지 않았습니다. 실적/약수치/전망 표시 보완.
- About 소개 / References / Data Sources / Non-commercial Policy.
  이전 출처 URL을 보존하고 최신 실행 상태, 통계·공시 별도 보관,
  Research 9개 기관의 연결 여부와 실제 공개 건수를 구분합니다.
- Mobbin과 여행신문의 참고 목적을 표시하며 제휴/후원을 주장하지 않습니다.
- 푸터에 브랜드·About·Data Sources·비상업 안내.
- 수집 예약/토큰/Pages 배포 방법은 그대로 유지하며, CSS/JS 및 향후 로고
  파일만 수정해도 기존 main 배포 경로가 실행되도록 경로 조건만 추가합니다.

## 공식 PNG 적용

사용자가 main에 업로드한 `site/assets/currentourism_logo_transparent_3x.png`를
요청한 `site/assets/currentourism-logo.png`에 **바이트 그대로 복사**했습니다.
업로드 원본도 보존합니다. 이미지 생성·수정·리샘플링·색상/배경 변경은 없습니다.

- 원본 867 × 498px, RGBA PNG, 알파 범위 0–255(투명 배경).
- 두 파일의 SHA-256 동일:
  `1a344104f9c0038dc7b910c61ae9b43d90de57d66ca7e6bd8516a6012c7ae705`.
- HTML 치수도 원본에 맞췄으며 CSS는 비율을 유지한 표시 크기만 조정합니다.
- 실제 PNG 표시, 텍스트 대체 표시 숨김, PC/모바일 비율, 이미지 키보드/클릭
  홈 이동을 브라우저에서 확인했습니다. 스크린샷을 공식 이미지로 갱신했습니다.
- 로고 미수신에 따른 Draft 사유를 해소했습니다. PR은 검토용이며 main 병합과
  운영 Pages 배포는 수행하지 않았습니다.

## 검증

- 기존 단위/회귀 테스트 **155개 통과**.
- `tests/newsroom.smoke.cjs`: 기존 검색·필터·저장·상세/원문·10/20 페이지 이동,
  전체 URL 확인·실패 보존·브리핑·통계/공시 제외 통과.
- `tests/reports.smoke.cjs`: 실제 110건 전체 검색·기관/국내외/유형/분야 필터,
  정렬·페이지 이동·실패 보존·PC/모바일 통과. 변경된 보조 탭/출처 경로로
  탐색하도록 수정했으며 기존 기능 검증은 유지했습니다.
- `tests/home.smoke.cjs`: 실제 Newsroom DB 32건과 Research DB 110건으로
  홈 원문 링크·섹션 순서·열 비율·24시간 발행 0건/빈 상태·5개 메뉴·활성 표시·
  모바일 메뉴·키보드 Escape·홈 링크·직접 경로/뒤로 이동·출처 9기관·차트·
  시뮬레이터 변경/초기화·가로 넘침 없음 통과. JS 오류 없음.
- Playwright Chromium, 데스크톱 1440px / 모바일 390px.
- actionlint v1.7.12, JS 구문, Git 공백 검사 통과.
- DB/원장/운영 정책/수집 소스/엔진 보호 결과: [integrity.json](integrity.json).
- 브라우저 회귀는 로컬에서 실제 공개 DB로 실행했습니다. GitHub의 기존
  두 워크플로는 Python 155개 테스트를 수행하며 PR에서 운영 배포하지 않습니다.
  공개 Pages 반영은 검토·병합 후 확인 대상입니다.

## 화면

아래는 **사용자가 제공한 공식 투명 PNG 적용 상태**입니다.

- [홈 전체 · PC](screenshots/home-desktop.png)
- [홈 전체 · 모바일](screenshots/home-mobile.png)
- [About · PC](screenshots/about-desktop.png)
- [About · 모바일](screenshots/about-mobile.png)
- [헤더 브랜드 영역](screenshots/brand-header.png) — 공식 원본 PNG

```bash
python -m unittest discover -s tests -q
python -m http.server 8010 --directory site
# Playwright/Chromium 설치 환경에서 별도 터미널로:
TOURISM_TEST_URL=http://127.0.0.1:8010 node tests/home.smoke.cjs
TOURISM_TEST_URL=http://127.0.0.1:8010 node tests/newsroom.smoke.cjs
TOURISM_TEST_URL=http://127.0.0.1:8010 node tests/reports.smoke.cjs
```
