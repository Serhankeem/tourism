# Tourism Pulse

관광산업 뉴스의 제목·출처·발행일·원문 링크·카테고리·키워드만 공개하는 링크 큐레이션 엔진입니다. 본문·사진·썸네일·AI 요약은 제공하지 않습니다. Python 3.10 이상과 표준 라이브러리만 사용합니다.

```bash
python3 -m unittest discover -s tests -v
python3 src/engine.py
python3 -m http.server 8000 --directory site
```

실제 수집은 `site/data/{news,briefing,health}.json`을 갱신합니다. 데모는 공개 데이터와 분리해 `python3 src/collector.py --demo --dir /tmp/tourism-demo`로 실행하세요.

[실수집 검증 결과·실패 원인·GitHub Actions 활성화 절차](docs/OPERATIONS_KR.md)

기존 main의 자동 실행 성공 기록과 별개로, v0.2 변경은 PR 검증 단계입니다. v0.2 운영 반영은 검토·병합 후 확인해야 합니다.

[v0.2 관련성·카테고리·신규 출처·마이그레이션 검증](docs/v02/README.md)

[v0.3 다중 소스 Discovery·권리 게이트·backfill·운영 검증](docs/v03/README.md)

[PR #3 편집 기준 보완·공시 분리·국내 공급원 재조사](docs/v03/EDITORIAL.md)

전체 원장과 분류 근거는 Pages 밖의 `collector_state/archive.json`, 뉴스 전용 뷰는 `news.json`/`newsroom.json`, 기업공시는 `filings.json`, 통계 원자료는 `research.json`에 보존합니다. 기본 Newsroom에는 뉴스만 노출합니다.

국내 일일 뉴스 공급 경로와 최신 통계 오분류 검증: [2026-10-28 조사 보고서](docs/v03/DOMESTIC-SUPPLY-20261028.md). 해당 문서는 이전 운영 목적·수익모델 미확인 당시의 결과입니다. 최신 [링크 큐레이션 검증](docs/v03/LINK-CURATION.md)을 참조하세요.

무료·광고 없는 비상업 운영 조건은 `operating_policy.json`에 기록합니다. 조건이 바뀌면 비상업 전용 소스의 신규 게시가 중단됩니다. 수익화 전에는 기존 링크 노출도 재검토하고 필요한 제공자 허락을 받으세요.

## Research Library v0.4

실제 검증한 연구자료 110건의 메타데이터·원문 링크를 제공하는 독립 Research 메뉴를 추가했습니다. [기관별 조사·DB·운영·검증](docs/v04/README.md)을 참조하세요.

```bash
python3 -m src.reports.engine --progress
python3 -m src.reports.report
```

Research는 `reports.json`과 `reports_*` 원장만 사용하며 기존 Newsroom·KOSIS·기업공시 DB는 변경하지 않습니다. 주 1회 월요일 07:40 KST 예약 및 수동 실행을 지원합니다. v0.4는 별도 PR 검토 단계이며 main에 직접 병합하지 않습니다.
