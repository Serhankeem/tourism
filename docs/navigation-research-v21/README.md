# Navigation / Research UX v2.1

Base: latest main `6e0742d` (PR #12 merged).
Branch: `feat/navigation-research-ux-v21`. UI-only; main merge/production deploy not performed.

## Navigation

- Four always-visible top-level items: 오늘의 관광 날씨는? → #weather,
  뉴스 disclosure, 관광지표 → #macro, 소개 → #about.
- News has three links: 뉴스 → #news / 데일리 브리핑 → #briefing / 리서치 → #research.
  Removed the old full hamburger and the abbreviated 브리프 label.
- Desktop single row; at ≤1080px logo first and menu second. ≤550px uses 2×2
  controls so no text is shortened or clipped at 320px. All controls ≥44px tall.
- Native button with aria-expanded/aria-controls, link navigation with aria-current.
  Current News/Briefing/Research activates the parent News button as well.
- Tab, Enter, Space, Escape (returns focus), optional ArrowDown to first link,
  outside click, focus leaving the group, and route selection dismiss the submenu.
  Ordinary navigation disclosure links are used rather than an incomplete ARIA menu.
- Existing navigate/hash/popstate flow remains; no data logic changes.
- Legacy overflow-y:auto from the hamburger container is explicitly removed.
  On 2×2 mobile layouts the dropdown starts below the full menu grid, preserving
  access to all top-level controls. All three links were hit-tested above content.
- ResizeObserver measures sticky-header height for scroll-padding so source anchors
  remain visible at every tested width.

## Research

- Prominent keyword search first; Blue Gray panel, white fields, defined borders,
  52px/16px search input, Navy labels, Deep Blue focus border/3px outline.
- All five dropdowns remain: publisher, region, report type, field, sort. Desktop
  uses 3 columns (2 at tablet sizes); mobile ≤768px starts details collapsed.
- Existing filtered()/sorting/metadata/date/source/link logic is unchanged.
- Closing filters doesn't clear the query or selections. Responsive layout changes
  only toggle disclosure visibility; they do not reset applied conditions.
- Applied count includes nonempty keyword, four categorical filters and nondefault
  sort. Page size is not counted. Reset clears these six conditions and returns to
  page1 while retaining the chosen 10/20 size; defaults remain newest/10.
- Publisher statistics, counts, update/source status and publisher buttons remain
  intact in a separate disclosure: desktop open, mobile collapsed. This keeps the
  search and results near each other; it is not a removal of institution statistics.
- The panel and result list have separate surfaces. Mobile reset and filter toggles
  are keyboard-accessible. Research's existing no-floating-channel presentation is
  applied to the whole banner so the close button is not left floating alone.

## Validation

- Python: **221 passed** (`python -m unittest discover -s tests -q`).
- Browser: **9 suites passed**: home, newsroom, reports, macro, ui-polish,
  ui-2, briefing-observation, market-weather-v2, navigation-research-v21.
- New suite covers **320/390/768/1024/1440px**: four persistent top controls;
  every route, parent/child active state, disclosure click/Space/Enter/Tab/Escape,
  external click, all popup links unclipped and on top, back/forward/direct hashes;
  actual report DB compound filters/count/reset, preserved collapsed selections,
  pagination/size, institution counts, focus and sticky-anchor visibility.
- UI-polish still covers 28 page/width combinations, visible keyboard focus,
  touch targets and readable charts. Existing navigation tests now open the actual
  News disclosure before clicking a nested link rather than clicking a hidden link.
- No JS page errors. Syntax and git diff --check passed.
- No src/, site/data/, collector_state/, source config, permission gate or Actions
  changes. Official airplane logo bytes retain SHA256
  `7f92affea61c57197f2b015576cb7bcaf604defb0ac270894157d8e94d070b7f`.
- News/Briefing/archive/Research DB, Macro computations, Market Weather v2,
  Data Observation and TOURGO approval behavior remain covered by regression.
- Browser tests read the real public report DB; no fixture JSON is published.
  GitHub PR checks are separate from real scheduled execution/Pages deployment.

## Screenshots

| View | Desktop 1440px | Mobile 390px |
|---|---|---|
| Navigation closed | [view](screenshots/navigation-closed-1440.png) | [view](screenshots/navigation-closed-390.png) |
| Navigation open | [view](screenshots/navigation-open-1440.png) | [view](screenshots/navigation-open-390.png) |
| Research panel + results | [view](screenshots/research-1440.png) | [view](screenshots/research-390.png) |

Research screenshots use the real DB after reset; the test-selected 20/page remains
selected by design. Institution statistics were collapsed with their own control
for a compact view. Desktop filter controls remain visible; mobile details are
collapsed and conditions count is visible. No collection or model behavior changed.
