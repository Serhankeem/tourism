# 여행기류 · currentourism

This guide records the user's additional brand/homepage requirements for the UI
redesign. It does not replace Research Library's collection and rights policies.

## Brand

- Primary / Deep Blue: `#173B73`; Accent / Orange: `#F47735`.
- White and light neutral surfaces, navy/charcoal text, readable spacing.
- Official user-supplied transparent logo: `site/assets/currentourism_logo_transparent_3x.png`.
  Preserve original Korean lettering, map pin, curve, color and aspect ratio.
  Do not recreate or extract a different mark from the inline preview.
- Entire logo is an accessible Overview home link on desktop and mobile.
- No old Tourism Pulse logo, working-title label or old slogan in the public UI.
- Mobbin is a design/UX reference, not a partner or sponsor.

## Navigation and home

- UI 2.0 header: logo / 오늘의 관광 날씨는? / 뉴스 / 브리프 / 리서치 / 관광지표 / 소개.
  Six primary menus; no English sublabels; visible active state.
- Mobile toggle with expanded state, Escape dismissal and focus return;
  page selection closes the menu. No left sidebar.
- Newsroom secondary navigation: 뉴스 / 리서치. Keep `#research` direct access,
  home discovery link, filters and full-DB search/pagination intact.
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
