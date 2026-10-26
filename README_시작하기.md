# Tourism Pulse · News Engine v0.1 (2026-10-25)

**초기 실행 가능한 소스 코드입니다. 아직 외부 서버에 배포하지 않았고, 실시간 자동 수집도 켜지 않았습니다.** 최초 배포와 GitHub 예약 작업 활성화 후부터 정해진 간격으로 수집합니다. 원문 기반 AI 핵심 요약·카카오톡 발송은 **다음 단계**입니다.

## 포함된 구성

| 경로 | 기능 |
| --- | --- |
| `src/collector.py` | Python 표준 라이브러리로 RSS/Atom 읽기, 날짜·URL 검증, 관광산업 키워드 관련성 판정, 주제별 분류, 중복 제거, 기존 기사 보존 |
| `sources.json` | RSS 출처 4종 및 콘텐츠 발췌 허용 여부 설정 |
| `site/index.html` | 기존 딥 블루/주황 로고 공개 웹사이트. 자동 수집 JSON 파일을 읽어 Newsroom/브리핑 후보를 표시. 카카오톡 채널 버튼 별도 유지 |
| `.github/workflows/collect.yml` | 2시간 간격 수집 + 오전 10:30(KST) 실행, 테스트, JSON 갱신, GitHub Pages 배포 |
| `tests/test_collector.py` | RSS/Atom 파싱, 관련성 분류, 날짜, URL, 중복, 출처 장애 시 원본 보존 검증 |
| `fixtures/sample.xml` | 가상 테스트용 RSS. 실뉴스 아님 |
| `관리자 시안(별도 보관)` | 운영자 화면의 **디자인 예시**. 로그인 보안이 없어 서비스 사이트에 배포하면 안 됨 |

## 로컬 테스트 (Windows PowerShell 또는 macOS 터미널)

Python 3.10 이상이 필요합니다. 추가 패키지를 설치할 필요는 없습니다.

```bash
cd tourism_pulse_news_engine
python -m unittest discover -s tests -v
python src/collector.py --demo
python -m http.server 8000 --directory site
```

브라우저에서 `http://localhost:8000`을 열고 Newsroom을 확인합니다. 가상 RSS 데이터만 표시되므로 상단에 `TEST DATA`로 나타납니다. **실제 기사라고 공개하면 안 됩니다.**

실제 수집 시도는 다음 명령으로 수행합니다.

```bash
python src/collector.py
```

이를 실행하면 `site/data/news.json`, `site/data/briefing.json`, `site/data/health.json`을 생성합니다. 이 실행 환경에서는 외부 RSS의 실제 반환 여부를 검증하지 못했습니다. 기관 서버 설정에 따라 특정 피드가 차단될 수 있습니다. 자동 운영 전에 네트워크 접근 가능한 컴퓨터에서 실수집을 확인하세요.

## GitHub로 자동 운영 시작하기

1. GitHub에 새 저장소를 만들고 **이 폴더 내용 전체(숨김 `.github` 포함)**를 업로드합니다. `관리자 시안(별도 보관)`은 사이트 폴더 밖에 있으므로 Pages에 포함되지 않습니다.
2. GitHub의 `Settings → Actions → General`에서 Actions가 저장소 콘텐츠에 기록할 수 있도록 `Read and write permissions`를 선택합니다. `Settings → Pages → Build and deployment`의 `Source`는 `GitHub Actions`로 설정합니다.
3. `Actions → Tourism Pulse RSS collector → Run workflow`를 실행합니다. 수집 결과가 갱신되면 Pages 사이트에 뉴스 피드가 나타납니다. HTTPS 배포 주소는 성공한 Actions 실행 페이지에서 확인하세요.
4. 이후 GitHub Actions 예약 실행으로 **한국시간 약 2시간마다** 수집하고 **오전 10:30**에 브리핑 후보 JSON을 다시 작성합니다. 각 원문은 링크만 제공하고 본문을 통째로 가져오지 않습니다. **오전 11시 카카오톡은 아직 미연결**입니다.
5. `site/data/health.json` 또는 워크플로 실패 알림을 확인합니다. 수집이 모두 실패하면 프로그램이 종료 코드 1을 반환하며 기존 Newsroom 데이터는 삭제하지 않습니다. GitHub 작업 자체가 실패하면 실패 기록이 Actions에 남습니다.

**일정 주의:** GitHub Actions 예약 실행은 분 단위 정확성·항상 실행을 보장하지 않습니다. 이는 초기 검증용입니다. 상용 발송 시스템의 시각 보장이 필요하면 운영용 Cron/작업 큐로 이전하세요.

## 데이터 모델 및 이용 조건

- `news.json`: `generated_at`, `last_successful_fetch`, `count`, `mode`, `articles[]`
- 각 뉴스: `id`, `title`, `published_at`, `date`, `source`, `source_id`, `category`, `desc`, `summary_type`, `url`, `related_sources` 등
- `briefing.json`: 최근 24시간 내 게시된 뉴스 중 관련성 상위 최대 5건의 **브리핑 후보 목록**
- `health.json`: 수집 실행 시각, 출처별 성공/실패, 마지막 정상 수집 시각
- 저장 범위: 최근 45일, 최대 450건. RSS 원문 기사 전체 본문은 다운로드하지 않음.

기본 출처에서는 `reuse_excerpt: false`로 설정되어 **RSS 설명문도 그대로 게시하지 않습니다**. 제목/출처/시간/원문 URL을 바탕으로 선별하며, 본문이 없는 항목에 AI가 기사를 읽고 요약했다고 표시하지 않습니다. 발췌 또는 AI 요약은 각 출처·기사별 재사용과 AI 처리 권한을 확인한 뒤 추가합니다. 기관 RSS 사용 가능과 개별 뉴스의 요약 재이용 허가는 같지 않습니다.

## 다음 단계

- 실제 RSS 네트워크 수집 및 수집 품질 점검 (1~2주)
- 출처별 라이선스 검토 및 요약 가능한 자료의 범위 확정
- AI 원문 기반 요약 엔진 연결 + 허위사실/숫자 검증 + 보류 정책
- 오래된 통계/시장 날씨 시뮬레이션을 공식 통계 API로 교체
- GitHub 알림/로그 → 운영용 Admin 권한 제어와 모니터링 연계
- 별도 카카오톡 채널 서비스 계약과 합법적 대량 발송 연동

## RSS 공식 안내 페이지

- 문화체육관광부: https://www.mcst.go.kr/site/s_etc/rss/rssService.jsp
- KOSIS: https://kosis.kr/serviceInfo/rssGuide.do
- Korea.net: https://www.korea.net/Others/Subscribe-to-Koreanet/RSS-Service
- 서울시: https://mediahub.seoul.go.kr/staticpage/rss.do
- GitHub Actions 예약: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
