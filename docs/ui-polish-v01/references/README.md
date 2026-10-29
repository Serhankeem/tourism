# Mobbin 디자인 참고 문서의 출처

- 사용자 지정 URL: <https://getdesign.md/mobbin/design-md>
- 조회일: 2026-10-29. 지정 페이지와 홈페이지 모두 HTTP 403으로 열리지 않았습니다.
  차단을 우회하거나 지정 페이지를 읽었다고 표시하지 않았습니다.
- 대신 공식 npm `getdesign@0.6.26` 배포본에 포함된 Mobbin 템플릿을 사용했습니다.
  registry.npmjs.org 실제 접근 200. 배포 tarball의 SHA-512를 npm integrity와 대조했습니다.
- 패키지: <https://www.npmjs.com/package/getdesign>
- 프로젝트: <https://github.com/VoltAgent/awesome-design-md> (`cli` 디렉터리)
- 의존성/설치 스크립트 없이 임시 경로에 배포본을 풀고 CLI 소스/README를 읽은 뒤
  실제 `--help`, `add mobbin --out ...`을 실행했습니다. 저장소 의존성은 늘리지 않았습니다.

```bash
GETDESIGN_DISABLE_TELEMETRY=1 node /tmp/currentourism-getdesign/package/bin/cli.mjs --help
GETDESIGN_DISABLE_TELEMETRY=1 node /tmp/currentourism-getdesign/package/bin/cli.mjs \
  add mobbin --out docs/ui-polish-v01/references/mobbin-design.md
# 일반 환경의 동등 명령:
# GETDESIGN_DISABLE_TELEMETRY=1 npx getdesign@0.6.26 add mobbin --out docs/ui-polish-v01/references/mobbin-design.md
```

루트 `DESIGN.md`는 덮어쓰지 않았습니다. CLI의 선택적 사용 통계 전송도 비활성화했습니다.
이 문서는 독립 작성자의 Mobbin 디자인 분석이며 Mobbin의 공식 디자인 시스템이나
제휴/후원을 뜻하지 않습니다. 콘텐츠 중심 여백·타입 위계·pill 컨트롤·얇은 테두리만
참고하고, Mobbin 고유 색상·Saans 폰트·80px 제목·마케팅 화면은 적용하지 않았습니다.
여행기류의 원본 로고, Deep Blue/Orange, 한국어 시스템 폰트와 기존 IA가 우선입니다.
