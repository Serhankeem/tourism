# Tourism Pulse

관광산업 RSS 선별·분류·중복 제거 및 Newsroom용 JSON 생성기입니다. Python 3.10 이상과 표준 라이브러리만 사용합니다.

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

전체 원장은 `site/data/archive.json`, 뉴스 전용 뷰는 `news.json`/`newsroom.json`, 기업공시는 `filings.json`, 통계 원자료는 `research.json`에 보존합니다. 기본 Newsroom에는 뉴스만 노출합니다.
