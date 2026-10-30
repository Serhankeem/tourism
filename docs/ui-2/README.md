# UI 2.0 review

**Merge blocker — replacement airplane logo is not yet available to this workspace.**
Required original: 1774 × 887 PNG, SHA256
`7f92affea61c57197f2b015576cb7bcaf604defb0ac270894157d8e94d070b7f`.
The current 867 × 498 pin logo is **not** this replacement. The conversation
preview appears solid orange and no downloadable original or matching workspace/
latest-main asset was available. Do not regenerate, recolor, reconstruct or claim
that the existing file is the requested new asset. Await a download URL/repo path.
Current screenshots still show the old pin logo and are not final logo acceptance.


Base: main b0a55ff. Branch: feat/ui-2-0-refresh. UI-only change; no merge or deployment.

## Changes

- Header: 오늘의 관광 날씨는? / 뉴스 / 브리프 / 리서치 / 관광지표 / 소개.
  Larger labels without English subtitles, direct Research access, a single active
  menu, existing mobile keyboard/Escape navigation retained.
- Header/footer use the supplied `site/assets/currentourism_logo_transparent_3x.png`
  original. This is the existing pin logo, not the newly requested airplane logo.
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
  reference URLs remain in expandable lists. Newsroom and Research status lists
  are now separate native details disclosures, collapsed by default, with keyboard
  Enter/click operation and original actual statuses/links preserved.
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

## PR #10 follow-up verification

- Python 210 passed; all six browser suites passed again.
- Added explicit default-collapsed, keyboard Enter expansion, click collapse and
  retained-source-link assertions at all four widths.
- 390/1440 home/About screenshots refreshed for the disclosure change. These
  retain the old logo until the original replacement file is supplied.
- src/, data, workflows and tourism-balance permission gates remain unchanged.
- New-logo SHA/1774×887/browser-cache/airplane screenshot verification is pending
  the exact original PNG; existing-logo checks are not a substitute.
