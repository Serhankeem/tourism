# Tourism Pulse 실수집 및 운영 검증

검증일: 2026-10-26 (Asia/Seoul). **로컬 실수집 부분 성공, GitHub 예약 실행·배포는 미검증**입니다.

## 실제 네트워크 결과

| 출처 | 관측 결과 | 처리 및 다음 조치 |
| --- | --- | --- |
| 문체부 보도자료 | HTTP 503, 응답 본문 `upstream connect error ... connection timeout` | 게이트웨이에서 상위 서버 연결 실패. 원본 사이트의 HTTP 403 또는 영구 차단으로 단정할 수 없음. 다른 실행 위치에서 재검증 필요 |
| Korea.net Food/Travel | HTTP 302, 동일 경로로 반복 리디렉션 | RSS와 공식 RSS 안내 페이지 모두 실패. 정상 RSS 주소를 운영기관에 확인해야 함 |
| KOSIS 최근수록자료 | HTTP 503, 동일한 게이트웨이 연결 실패 본문 | 원본 거부 여부는 확인 불가. 다른 실행 위치에서 재검증 필요 |
| 서울시 문화 RSS | HTTP 200, 유효 RSS 20개 항목 | 관광산업 관련 기사 2건 선별, 원문 본문 수집 없이 제목·출처·발행일·URL 저장 |

이전 온보딩의 `Tunnel connection failed: 403 Forbidden`은 HTTPS 터널을 만들기 전 프록시에서 발생했습니다. 원본 사이트의 403으로 볼 근거가 없습니다. 현재 저장된 네트워크 정책은 unrestricted이며 서울시 HTTPS 수집이 실제로 성공했습니다. 설정값만으로 전체 연결 성공을 가정하지 않았습니다.

실수집 기사:

- [제주·철원의 로컬 메뉴를 서울에서 맛보세요! '로컬트립 가을소풍'](https://mediahub.seoul.go.kr/archives/2019815) — 2026-10-22, 지역
- [봉은사 명상부터 한옥 전시까지 '웰니스 트래블 위크'](https://mediahub.seoul.go.kr/archives/2019810) — 2026-10-21, 지역

현재 두 기사 모두 최근 24시간 밖이므로 브리핑 후보는 0건입니다. 최대 5건이며 부족한 수를 과거 기사나 가상 데이터로 채우지 않습니다. `site/data/health.json`에 출처별 실패 종류·HTTP 상태·성공/선별 개수가 기록되어 있습니다.

## 대체 출처 검토

- 서울시 [공식 RSS 이용안내](https://mediahub.seoul.go.kr/staticpage/rss.do)의 문화(06), 경제(04), 교통(01), 안전(02), 주택(03), 환경(05), 복지(07) 피드는 실제 XML 수신에 성공했습니다. 기존 필터 기준 추가 6개 피드에서는 관광산업 선별 기사가 없었습니다. 문화 피드가 현재 사용 가능한 공식 대안이며 다른 분야 피드를 무작정 추가하지 않았습니다. 서울 지역 소식만으로 전국 산업·국가통계를 대체할 수는 없습니다.
- 대한민국 정책브리핑의 `https://www.korea.kr/rss/policy.xml`, `https://www.korea.kr/rss/pressrelease.xml`, `https://www.korea.kr/rss/dept_mct.xml`은 이 환경에서 게이트웨이 503으로 실패했습니다. 대체 성공 출처로 등록하지 않았습니다.
- UN Tourism `https://www.unwto.org/rss.xml`, OECD `https://www.oecd.org/en/topics/tourism.rss` 후보 URL은 HTTP 403 응답으로 실패했습니다. 유효한 공식 RSS인지도 검증되지 않아 등록하지 않았습니다. 이 403만으로 원본/중간장비 중 어느 곳의 정책인지 확정할 수 없습니다.
- 공공데이터포털의 한국관광공사 TourAPI나 KOSIS 통계 API는 향후 공식 통계·관광정보 보완 후보입니다. 뉴스 RSS의 동등한 대체물이 아니며, 인증키·API 스키마·이용조건 확인 및 별도 어댑터 구현이 필요합니다. 이번 작업에서 API 수집 성공으로 계산하지 않았습니다.

## 구현 동작

- 기존 수집·중복 제거·6개 주제 분류를 유지하고, 한국어 띄어쓰기와 웰니스·지역관광 사업 신호를 보완했습니다. 제목에 산업 신호가 없으면 RSS 설명에 같은 주제의 서로 다른 산업 신호가 2개 이상 있어야 통과합니다. 단순 여행·맛집 소개는 제외합니다. 이는 규칙 기반 선별이며 분류 정확도를 보장하는 AI 분석은 아닙니다.
- 잘못된 날짜·5분 넘는 미래 날짜를 배제하고 RSS/Atom이 아닌 응답을 실패로 기록합니다.
- 완전 실패 시 기존 news.json과 briefing.json은 그대로 보존하고 health.json만 갱신하며 프로세스는 종료 코드 1을 반환합니다. 일부 실패 시 성공 출처 자료와 기존 기사를 합치고 `partial`을 기록합니다.
- 브리핑은 최근 24시간 기사 중 관련성 내림차순, 동점이면 최신순으로 최대 5건을 생성합니다. 정상 수집마다 재작성하므로 오전 10:30 실행도 같은 규칙을 적용합니다. 완전 실패하면 기존 브리핑의 생성 시각을 유지합니다.
- Newsroom은 5분마다 JSON을 다시 읽습니다. 부분·전체 실패를 표시하고, 순서 변경 시에도 기사 해시 ID로 저장 상태를 유지합니다. 기존 파란색 CSS와 레이아웃은 변경하지 않았습니다.

## 테스트 및 재현

```bash
cd /workspace/tourism
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 src/collector.py
python3 -m http.server 8001 --bind 127.0.0.1 --directory site
```

- Python 회귀 테스트 **32개 통과**: RSS/Atom, 주제 6종, 날짜, URL, 중복, 반복 실행, 실패 보존, 실패 원인 구분, 24시간·최대 5건·동점 최신순 브리핑 등을 검증했습니다.
- actionlint **v1.7.7 통과**: 공식 릴리스 체크섬 확인 후 실행했습니다. shellcheck/pyflakes 외부 검사기는 사용하지 않았습니다. 문법 검증은 원격 Actions 성공을 뜻하지 않습니다.
- Chromium/Playwright 브라우저 검사 통과: 실제 JSON 2건 표시, 검색, 상세, 저장, 순서 변경 후 저장 유지, 부분 실패 표시, 가상 전체 장애 시 기존 표시 보존, 빈 브리핑. JavaScript 실행 오류 0건. 전체 장애 시나리오는 테스트용 응답으로 검증했습니다.

브라우저 검사 재현은 선택 사항이며 Playwright와 Chromium이 별도로 필요합니다. 이 클라우드에는 브라우저를 저장소 밖 `/workspace/tourism-runtime/pw-browsers`에 설치했습니다.

```bash
PLAYWRIGHT_BROWSERS_PATH=/workspace/tourism-runtime/pw-browsers node tests/newsroom.smoke.cjs
```

브라우저 검사는 현재 검증 스냅샷(부분 성공·기사 2건)을 전제로 합니다. 이후 피드 결과가 달라지면 기대 결과를 확인해야 합니다. Python 표준 라이브러리 테스트와 운영 수집기는 Playwright를 요구하지 않습니다.

## GitHub에 반영한 뒤 필요한 설정

1. 별도 브랜치의 PR을 검토한 뒤 `main`에 병합합니다. PR에서는 회귀 테스트만 실행하고 수집·배포 작업은 건너뜁니다.
2. 저장소 Settings → Actions에서 워크플로 실행을 허용하고, 저장소 정책이 `contents: write`를 허용하는지 확인합니다. 브랜치 보호가 봇의 직접 커밋을 막는 경우 데이터 커밋 정책 또는 배포 방식을 따로 조정해야 합니다.
3. Settings → Pages의 Source를 **GitHub Actions**로 설정합니다. github-pages 환경이 main 배포를 허용해야 합니다.
4. Actions → **Tourism Pulse RSS collector** → Run workflow를 main에서 실행합니다.
5. 수집·데이터 커밋·Pages 배포·실패 진단 artifact를 확인합니다. 전부 실패하면 진단을 보존·게시한 후 워크플로를 실패 처리합니다. 일부 실패는 health의 `partial`과 실행 요약에 그대로 남습니다.
6. 다음 예약 실행과 배포된 Newsroom 데이터까지 확인한 뒤 자동 운영 여부를 판단합니다.

워크플로는 **UTC 짝수 시각 17분마다(2시간 간격)** 및 **UTC 01:30(한국시간 10:30)** 실행되도록 구성했습니다. GitHub 예약 실행은 지연·누락될 수 있어 정각 실행을 보장하지 않습니다. main의 관련 코드가 변경되면 push 실행도 동작합니다. 데이터만 갱신하는 봇 커밋은 다시 수집을 촉발하지 않습니다.

초기 실수집 검증 시 GitHub API로 조회한 Actions 실행 기록은 **0건**이었습니다. PR 테스트 성공과 main의 수집·배포 성공은 구분해야 합니다. Actions 권한 설정과 Pages 설정 조회는 `Resource not accessible by integration` HTTP 403으로 제한되어 실제 설정을 확인하지 못했습니다. 이는 RSS 네트워크 오류와 별개의 GitHub API 권한 문제입니다. 현재 RSS에는 API 키가 필요하지 않으며 코드·워크플로에 API 키나 비밀번호를 넣지 않았습니다. 향후 인증 API를 추가할 때는 GitHub Secrets로 전달해야 합니다.

## PR 검토: 영구 보존과 공개 반영 경로

수집 JSON은 artifact에만 두지 않고 `site/data/*.json`을 봇 커밋으로 저장소 main에 push합니다. 따라서 러너가 종료돼도 Git 이력에 남고 다음 실행의 checkout에서 복원됩니다. artifact는 별도의 유한 보존 기간을 가진 진단 자료이며 영구 저장소로 취급하지 않습니다.

데이터 커밋 성공 후 동일한 작업 디렉터리의 `site`를 Pages artifact로 업로드하고 `actions/deploy-pages`로 게시합니다. 공개 HTML은 같은 사이트의 `data/news.json`, `data/briefing.json`, `data/health.json`을 읽으며 열려 있는 화면도 5분마다 갱신합니다. 수집 봇의 GITHUB_TOKEN 커밋이 다른 워크플로를 촉발하지 않아도 같은 실행 안에서 배포하므로 공개 갱신이 가능합니다.

쓰기 권한·브랜치 보호·Pages 정책 때문에 저장이나 배포가 실패하면 실행도 실패하며 공개 갱신을 보장하지 않습니다. 커밋까지 성공하고 Pages가 실패하면 저장된 데이터는 남지만 공개 화면은 이전 배포를 유지합니다. 완전 수집 실패 시 기존 뉴스·브리핑은 보존하고 health만 커밋·게시한 뒤 실패 처리합니다. 최초 실행에 이전 뉴스가 없으면 실패 상태만 공개합니다.

예약식 `17 */2 * * *`는 한국시간 01:17, 03:17, …, 23:17(2시간 간격)에 해당합니다. `30 1 * * *`는 한국시간 매일 10:30입니다. 한국은 현재 서머타임을 사용하지 않습니다. `workflow_dispatch`로 main에서 수동 실행할 수 있으며 main 병합 전에는 main에 이 워크플로가 없어 UI에 표시되지 않을 수 있습니다. 이 구조와 로컬 테스트를 확인했으나 실제 예약 실행·영구 커밋·공개 Pages 갱신은 main 병합 후 검증해야 합니다.

추가 검증: 워크플로의 데이터 저장 셸 명령을 임시 로컬 Git 원격에서 그대로 실행하고 새 checkout으로 복원해 뉴스·브리핑 바이트 보존 및 갱신된 실패 health의 영구 커밋을 확인했습니다. 이는 러너 종료 후 복원 구조에 대한 로컬 검증이며 GitHub 원격 실행이나 Pages 배포 성공을 의미하지 않습니다. 변경 파일 12개의 자격증명·개인 이메일 패턴 검사에서도 실제 키·비밀번호·개인 연락처가 검출되지 않았습니다(GitHub 봇 noreply 주소 제외).
