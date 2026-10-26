// Optional browser regression: requires Playwright + Chromium and a local server.
// TOURISM_TEST_URL=http://127.0.0.1:8001 node tests/newsroom.smoke.cjs
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
(async () => {
 const browser = await chromium.launch({headless:true});
 try {
  const page = await browser.newPage();
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(process.env.TOURISM_TEST_URL || 'http://127.0.0.1:8001');
  await page.waitForFunction(()=>!newsLoading);
  assert.equal(await page.locator('#rss-health-chip').textContent(),'PARTIAL FETCH');
  await page.locator('[data-nav="news"]').click();
  assert.equal(await page.locator('#news-items .news-item').count(),2);
  await page.locator('#news-search').fill('웰니스');
  assert.equal(await page.locator('#news-items .news-item').count(),1);
  await page.locator('#news-items [data-detail]').click();
  assert.match(await page.locator('#modal-title').textContent(),/웰니스/);
  await page.locator('#modal-close').click();
  await page.locator('#news-items [data-bookmark]').click();
  // IDs remain stable when a collection refresh changes ordering.
  await page.route('**/data/news.json?*',async route=>{
   const response=await route.fetch();const data=await response.json();
   data.articles.reverse();await route.fulfill({json:data});
  });
  await page.evaluate(()=>loadLiveNews());
  assert.match(await page.locator('#news-items [data-bookmark]').textContent(),/저장됨/);
  await page.locator('#news-search').fill('');
  await page.locator('[data-filter="저장"]').click();
  assert.equal(await page.locator('#news-items .news-item').count(),1);
  await page.route('**/data/health.json?*',route=>route.fulfill({json:{
   status:'failed',checked_at:'2026-10-26T13:30:00+09:00',successful_sources:0,
   source_count:4,sources:[{name:'시험 장애',status:'error'}]
  }}));
  await page.evaluate(()=>loadLiveNews());
  assert.equal(await page.locator('#rss-health-chip').textContent(),'FETCH FAILED');
  await page.locator('[data-filter="전체"]').click();
  assert.equal(await page.locator('#news-items .news-item').count(),2);
  await page.locator('[data-nav="briefing"]').click();
  assert.equal(await page.locator('#briefing-state').textContent(),'새 기사 없음');
  assert.deepEqual(errors,[]);
  console.log('PASS: live articles, search, detail, stable bookmark, partial/all-failure status, preservation, empty briefing; no JS errors');
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
