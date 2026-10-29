# 여행기류 · UX/UI Design Refinement v1.0

PR #6 병합 후 최신 main `31790dc`에서 `feat/currentourism-ui-polish-v01`을 만들고,
제품 파일을 수정하기 **전에** 7개 페이지의 PC/모바일 화면을 캡처했습니다.
이번 변경은 디자인·반응형·접근성 표시 보완이며 main에 직접 병합하지 않습니다.

## 변경 전 분석과 개선

| 영역 | 변경 전 | 적용 결과 |
| --- | --- | --- |
| 공통 | 작은 보조 글자, 화면마다 다른 간격·컨트롤 크기 | 4/8/12/16/24/32/48px 간격 토큰, 카드 20px·pill 컨트롤, 선명한 텍스트 대비 |
| 타이포그래피 | 본문과 출처의 위계·행간이 약함 | 한국어 시스템 폰트 유지, 제목 29–38px, 목록 제목 18–20px, 출처/날짜 12px, 충분한 행간 |
| 헤더 | 로고/메뉴 간격, 작은 영어 보조 라벨 | 균형 잡힌 96px 헤더, 명확한 활성 표시·focus·hover, 모바일 확장·Escape·감소된 모션 대응 |
| 홈 | 큰 색면과 작은 출처·상태 텍스트 | 뉴스 제목/메타정보 구분, 절제된 중립 날씨 카드, 실적/전망 지표, 차트·에디토리얼 위계 정돈 |
| Newsroom | 작은 필터·버튼, 목록 위계가 약함 | full-width pill 검색, 일관된 44px 필터/페이지 버튼, 제목·출처·저장 상태·hover 정리 |
| Research | 모바일 기관·필터가 1열로 길게 쌓임 | 기관·복합 필터 2열, 공통 검색/칩/목록/접근 구분, 긴 영문 제목 줄바꿈 |
| 차트 | 고정 640px viewBox가 모바일에서 축소돼 글자가 작아짐 | 컨테이너 너비에 맞는 viewBox·막대 폭, 보이는 축/월 12px 이상, 실제 3개 월만 유지 |
| Macro | ‘연동 예정’의 대비 2.39:1 | 문구/수치는 그대로, 대비가 충분한 보조색으로 수정 |
| Weather | 슬라이더 접근 가능한 이름 누락 | 기존 화면 라벨을 input에 연결, 키보드 조정·44px 조작 영역, 계산식/리셋 보존 |
| About | 장문·출처 정보의 크기와 간격이 작음 | 문단 폭·행간·섹션 제목·출처 상태와 링크 정돈, 구성/출처/정책 그대로 유지 |

### 공통 디자인 시스템

- `site/currentourism.polish.css`를 공통 표시 계층으로 추가했습니다.
- 브랜드 Deep Blue `#173B73`, Orange `#F47735`와 원본 PNG를 유지합니다.
  흰 캔버스, 연한 중립 면, 얇은 테두리와 작은 그림자를 사용합니다.
- 새로운 폰트 다운로드·아이콘 라이브러리·이미지·AI 기사 요약은 추가하지 않았습니다.
- 5개 주 메뉴, 뉴스/리서치 보조 탭, Overview 섹션 순서를 유지합니다.
- 모바일 카카오 안내 버튼은 같은 동작·접근 가능한 이름을 유지하면서 작은 원형으로
  표시해 콘텐츠 가림을 줄였습니다. 채널 연결/발송 기능을 새로 만들지 않았습니다.
- root `DESIGN.md`는 변경하지 않았습니다. Mobbin 참고 문서는 [별도 경로](references/README.md)에
  보관합니다. 웹 URL 403, 공식 npm CLI 사용법·가져오기·독립 분석 문서임을 구분했습니다.
- 이 CSS 파일명은 기존 Actions의 `site/currentourism.*` 감시 경로와 일치합니다.
  배포 트리거를 위해 워크플로를 변경할 필요가 없습니다.

### 실제 UI 측정

[브라우저 측정값](checks/design-metrics.json)은 같은 데이터에서 공통 표시 계층 적용 전/후를
비교합니다. 첫 스크린샷은 원래 main 상태에서 별도로 캡처했습니다.

| 390px 모바일 Research | 전 | 후 |
| --- | ---: | ---: |
| 제목 글자 | 16px | 18px |
| 기관 버튼 배치 | 1열 | 2열 |
| 검색/선택 필터 배치 | 1열 | 2열 |
| 페이지 버튼 높이 | 34px | 44px |
| 첫 자료의 문서 내 시작 위치 | 1,538px | 1,449px |

1440px Research 제목은 18→20px, 페이지 버튼은 34→44px입니다.
PC에서는 행간과 컨트롤 여백이 늘어 전체 페이지가 길어집니다.

## 변경 전후 화면

1440px와 390px의 실제 공개 DB 화면입니다. 기사/보고서 본문이나 가상 자료는 없습니다.

| 화면 | PC 전 | PC 후 | 모바일 전 | 모바일 후 |
| --- | --- | --- | --- | --- |
| Overview | [전](before/overview-desktop.png) | [후](after/overview-desktop.png) | [전](before/overview-mobile.png) | [후](after/overview-mobile.png) |
| Newsroom | [전](before/news-desktop.png) | [후](after/news-desktop.png) | [전](before/news-mobile.png) | [후](after/news-mobile.png) |
| Research | [전](before/research-desktop.png) | [후](after/research-desktop.png) | [전](before/research-mobile.png) | [후](after/research-mobile.png) |
| Daily Briefing | [전](before/briefing-desktop.png) | [후](after/briefing-desktop.png) | [전](before/briefing-mobile.png) | [후](after/briefing-mobile.png) |
| Macro Monitor | [전](before/macro-desktop.png) | [후](after/macro-desktop.png) | [전](before/macro-mobile.png) | [후](after/macro-mobile.png) |
| Market Weather | [전](before/weather-desktop.png) | [후](after/weather-desktop.png) | [전](before/weather-mobile.png) | [후](after/weather-mobile.png) |
| About | [전](before/about-desktop.png) | [후](after/about-desktop.png) | [전](before/about-mobile.png) | [후](after/about-mobile.png) |

추가 확인: [1024px 홈](checks/overview-1024.png), [1024px 뉴스](checks/news-1024.png),
[1024px 리서치](checks/research-1024.png), [768px 홈](checks/overview-768.png),
[768px 뉴스](checks/news-768.png), [768px 리서치](checks/research-768.png).

## 검증 결과

- 기존 Python 단위/회귀 테스트 **155개 통과**.
- 기존 Newsroom Playwright 통과: 검색/카테고리/저장/상세/6필드/10·20 페이지/전체 원문 URL/
  실패 상태·기존 데이터 보존/브리핑/통계·공시 제외.
- 기존 Research Playwright 통과: 실제 **110개** 자료, 전체 DB 검색/복합 필터/정렬/
  10·20 페이지/빈 상태/실패 보존/PC·모바일.
- 기존 홈 Playwright 통과: 원본 PNG 바이트 일치·비율·홈 이동/5개 메뉴/해시·뒤로 이동/
  About 9기관/지표 3개월/날씨 입력·리셋/실제 뉴스/24시간 0건 상태.
- 신규 `tests/ui-polish.smoke.cjs`: **4개 너비 × 7개 페이지 = 28개 조합** 통과.
  가로 넘침 0, 활성 메뉴·로고 비율·40px 이상 버튼/선택 조작 영역·실제 차트 글자
  11.5px 이상·키보드 focus/Tab/Escape·긴 실제 영문 보고서 제목·날씨 키보드 계산·
  감소된 모션을 확인했습니다.
- axe-core **4.14.0**, WCAG 2 A/AA·2.1 AA 태그 자동 검사 **위반 0건**.
  [원시 결과와 자동 판단 보류 항목](checks/responsive-accessibility.json)도 보존합니다.
- 자동 판단이 보류된 SVG 글자는 흰 바탕의 실제 색 `#52647A`, `#1B477B`로
  대비 4.5:1 이상을 추가 계산하고 화면을 검토했습니다. 숨겨진 카카오 대화상자
  참조 대상이 DOM에 존재하는 것도 검증했습니다. 자동 검사 결과가 전체 WCAG 인증이나
  모든 스크린리더·실물 기기 검증을 뜻하지는 않습니다.
- JS 구문, Git 공백 검사 통과. 기존 Actions를 바꾸지 않았으며 PR에서는 기존 Python
  검사가 실행됩니다. 브라우저/axe 검사는 로컬 Chromium에서 실행했습니다.

```bash
python -m unittest discover -s tests -q
python -m http.server 8010 --directory site
# Playwright + Chromium 환경, 별도 터미널:
TOURISM_TEST_URL=http://127.0.0.1:8010 node tests/newsroom.smoke.cjs
TOURISM_TEST_URL=http://127.0.0.1:8010 node tests/reports.smoke.cjs
TOURISM_TEST_URL=http://127.0.0.1:8010 node tests/home.smoke.cjs
TOURISM_TEST_URL=http://127.0.0.1:8010 AXE_SCRIPT_PATH=/path/to/axe.min.js \
  POLISH_OUTPUT=/tmp/currentourism-polish node tests/ui-polish.smoke.cjs
```

axe는 임시 경로의 공식 npm 배포본을 사용했으며 배포 tarball integrity를 확인했습니다.
런타임 의존성은 추가하지 않았습니다. `AXE_SCRIPT_PATH`를 생략하면 나머지 UI 검사만 실행하며
접근성 검사를 실행했다고 출력하지 않습니다.

## 보존한 기능·데이터

[해시 대조 결과](integrity.json)에 **45개 보호 파일**을 기록했습니다. 뉴스/연구 DB와 전체
원장, 수집 엔진, 관련성·중복 정책, 이용조건, 비상업 정책, 공식 PNG 두 파일,
루트 DESIGN.md, GitHub Actions 워크플로가 모두 기준 main과 바이트 단위로 같습니다.

뉴스·Research의 제목/출처/발행일/링크/분류/키워드·접근 구분, 기본 10/선택 20 페이지와
검색/필터 초기화, 실제 통계·기간과 3개 월, 날씨 입력/계산 가중치, 브리핑 생성,
2시간/매일 10:30/매주 월요일 일정, Pages Git 저장·배포 구조를 바꾸지 않았습니다.
차트의 viewBox/막대 폭·색상/축 글자/리사이즈 표시만 조정했습니다.

## 남은 점·후속 과제

1. 모바일 Research는 모든 기관·필터를 노출하므로 첫 자료까지 스크롤이 남습니다.
   접기/고정 필터 같은 동작 확장은 이번 디자인 PR에서 추가하지 않았습니다.
2. 네이티브 select의 표시/팝업 모양과 포커스는 실제 iOS/Android에서도 후속 확인이 필요합니다.
   이번 결과는 Chromium 4개 너비와 키보드 검증 범위입니다.
3. 미연동 거시지표, 정적 스냅샷의 기준기간, 시뮬레이션 가중치 미검증, 공급원 접근 실패는
   디자인으로 해결하거나 정상 운영처럼 표시하지 않았습니다. 데이터/기능 후속 과제입니다.
4. 공개 GitHub Pages 화면은 PR 검토·병합·기존 배포 작업 완료 후 확인해야 합니다.
   이번 작업에서 main 병합이나 운영 배포 완료를 주장하지 않습니다.
