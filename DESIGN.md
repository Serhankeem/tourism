# 여행기류 · currentourism

This guide records the user's additional brand/homepage requirements for the UI
redesign. It does not replace Research Library's collection and rights policies.

## Brand

- Primary / Deep Blue: `#173B73`; Accent / Orange: `#F47735`.
- White and light neutral surfaces, navy/charcoal text, readable spacing.
- Official user-supplied transparent logo: `site/assets/currentourism-new-airplane-logo.png`.
  Preserve original Korean lettering, airplane icon, curve, color and aspect ratio.
  Do not recreate or extract a different mark from the inline preview.
- Entire logo is an accessible Overview home link on desktop and mobile.
- No old Tourism Pulse logo, working-title label or old slogan in the public UI.
- Mobbin is a design/UX reference, not a partner or sponsor.

## Navigation and home

- Navigation v2.1 header: 오늘의 관광 날씨는? / 뉴스 disclosure / 관광지표 / 소개.
  News disclosure routes to 뉴스, 데일리 브리핑, 리서치. Always show four top-level
  items, including mobile (logo first, 2×2 items on narrow screens). No hamburger.
- Disclosure has aria-expanded/controls, keyboard focus, outside-click/Escape close;
  selected subpage activates the News group, hash/history stays intact.
- Newsroom secondary navigation: 뉴스 / 리서치. Keep `#research` direct access,
  home discovery link, filters and full-DB search/pagination intact.
- Research keyword search is first in a Blue Gray panel. Desktop filters use 2–3
  columns; mobile details collapse without clearing conditions. Show applied count
  and reset; reset preserves selected 10/20 page size. Institution stats remain
  available in a separate disclosure (collapsed by default on mobile).
- Overview: Industry News + Market Weather; Key Indicators; Inbound Tourism +
  Analyst's Note. Desktop columns stack on mobile.
- Use existing news editorial order and original issue dates. Display empty/stale
  states truthfully. No separate home article DB, copied prose or generated news.
- Weather remains an explicitly labeled simulation with unvalidated weights;
  its inputs, computation and reset remain unchanged. Home reflects its inputs.
- Keep observed statistics, source/reference periods and actual/forecast labels;
  never fill missing months. Notes are dated editorial observations, not summaries.
- Footer: original logo home link, 소개, Data Sources and noncommercial notice.
- Kakao channel banner may be dismissed with localStorage persistence. No delivery activation.
- Rain/cloudy/partly/sunny colors are shared between home and Weather Lab; model unchanged.

## About and provenance

- About Us, 프로젝트 목적, 운영 원칙, Data Sources table, Non-commercial Policy.
- Retain prior source URLs, distinguish connected feeds from investigation targets,
  and distinguish latest network status from publication availability.
- Free, ad-free, no paid subscription. Rights belong to publishers/rightsholders.
  Metadata/link curation is not a blanket permission to reuse protected content.
- Legacy `#sources` resolves to About's Data Sources section.
- Do not modify news/report DBs, source permissions, operating_policy.json,
  collection schedules or Pages publication method for a design change.

## Verification

Use the existing Python suite, Newsroom and Research browser regressions, and
`tests/home.smoke.cjs` for header/routes/history/mobile/menu/real metadata/freshness/
About/metrics/weather. Capture desktop/mobile home and About screenshots.
