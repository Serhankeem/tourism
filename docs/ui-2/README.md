# UI 2.0 review

Base: main b0a55ff. Branch: feat/ui-2-0-refresh. UI-only change; no merge or deployment.

## Changes

- Header: 오늘의 관광 날씨는? / 뉴스 / 브리프 / 리서치 / 관광지표 / 소개.
  Larger labels without English subtitles, direct Research access, a single active
  menu, existing mobile keyboard/Escape navigation retained.
- Header/footer use the supplied `site/assets/currentourism_logo_transparent_3x.png`
  original. It is readable and transparent; no new file was attached this turn.
  No logo regeneration, pixel changes, cropping or recoloring. Original ratio and
  home links verified. The existing alias `currentourism-logo.png` is also retained.
- Kakao banner has an independent accessible close button and localStorage
  persistence (storage exceptions are caught). The channel dialog/setup remains;
  no channel delivery is activated. To show it again, clear the site storage key
  `currentourism.kakao.dismissed`.
- Weather uses rain blue / cloudy slate / partly teal / sunny amber backgrounds,
  matching titles, icons and simulation pills in both home and Lab. Default score
  remains 68, with identical weights, inputs, reset and calculation function.
- About Us → 프로젝트 목적 → 운영 원칙 → Data Sources → Non-commercial Policy.
  Removed the About Research CTA; Research is directly in the header. Official
  reference URLs remain in expandable lists; source-health displays are retained.
- Data Sources uses a semantic five-column table, with locally scrollable mobile
  overflow. It distinguishes connected visitor data, TOURGO approval pending,
  metadata-only news/research and unvalidated Weather simulation.
- News/Research pagination uses < / > with accessible previous/next labels,
  numbered active pages, existing filters/search and 10/20 page sizes unchanged.
- Logo footer retains noncommercial and copyright notices.

## Validation

- Python: `python -m unittest discover -s tests -q` — 210 passed.
- Existing browser suites passed: home, Newsroom, reports, Macro, UI polish.
  UI polish covers 28 route/width combinations, focus, contrast and touch controls.
- Added `tests/ui-2.smoke.cjs`: widths 320/390/768/1440, all four weather states,
  both logo ratios, banner real click/dismiss/reload, channel dialog, sources
  table, routes, both pagers/20-item selection, no page JavaScript errors.
- Existing browser expectations were updated only for the requested six menus,
  new About headings and the added accessible arrow labels.
- `git diff --check` passed. No src/, macro_sources.json, collector_state/,
  site/data/ or .github/workflows changes; no added credentials.
- Weather calculation function SHA256 before/after:
  `48d4be16ed4476bdf01368eeaf8abe0f4b26e7abb9cfff7a03698f46985ec6d6`.
- Actual scheduled Actions/Pages deployment is not executed by this UI PR.
  Daily Briefing delivery, Analyst automation and measured Weather model remain
  deferred; source failures shown in screenshots reflect existing DB health.

## Screenshots

[Desktop overview](screenshots/overview-1440.png) ·
[Mobile overview](screenshots/overview-390.png) ·
[Desktop About](screenshots/about-1440.png) ·
[Mobile About](screenshots/about-390.png)

[Rain](screenshots/weather-rain.png) · [Cloudy](screenshots/weather-cloudy.png) ·
[Partly cloudy](screenshots/weather-partly.png) · [Sunny](screenshots/weather-sunny.png)

The screenshots contain the existing public metadata and simulated UI, not new
source data. Smaller 320px and tablet layouts were also checked by browser tests.
