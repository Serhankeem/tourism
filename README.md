# Tourism Pulse

관광산업 RSS 선별·분류·중복 제거 및 Newsroom용 JSON 생성기입니다. Python 3.10 이상과 표준 라이브러리만 사용합니다.

```bash
python3 -m unittest discover -s tests -v
python3 src/collector.py
python3 -m http.server 8000 --directory site
```

실제 수집은 `site/data/{news,briefing,health}.json`을 갱신합니다. 데모는 공개 데이터와 분리해 `python3 src/collector.py --demo --dir /tmp/tourism-demo`로 실행하세요.

[실수집 검증 결과·실패 원인·GitHub Actions 활성화 절차](docs/OPERATIONS_KR.md)

현재는 부분 수집을 검증한 상태이며 GitHub의 예약 실행·배포 성공은 아직 검증하지 않았습니다.
