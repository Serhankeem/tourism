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
  const base=process.env.TOURISM_TEST_URL || 'http://127.0.0.1:8001';
  const archiveSnapshot=await (await page.request.get(base+'/data/archive.json')).json();
  const snapshot=await (await page.request.get(base+'/data/newsroom.json')).json();
  const expectedCount=snapshot.articles.length;
  assert.ok(expectedCount>0,'Browser smoke requires a nonempty real or fixture snapshot');
  const selected=snapshot.articles[0];
  await page.goto(base);
  await page.waitForFunction(()=>!newsLoading);
  assert.equal(await page.locator('#rss-health-chip').textContent(),'PARTIAL FETCH');
  await page.locator('[data-nav="news"]').click();
  assert.equal(await page.locator('#news-items .news-item').count(),expectedCount);
  await page.locator('#news-search').fill(selected.title);
  assert.equal(await page.locator('#news-items .news-item').count(),1);
  await page.locator('#news-items [data-detail]').click();
  assert.equal(await page.locator('#modal-title').textContent(),selected.title);
  const selectedCategory=await page.evaluate(c=>normalizeCategory(c),selected.category);
  assert.equal(await page.locator('#modal-category').textContent(),selectedCategory);
  if(selected.relevance_evidence)assert.match(await page.locator('#modal-impact').textContent(),/Direct|Indirect/);
  await page.locator('#modal-close').click();
  await page.locator('#news-items [data-bookmark]').click();
  // IDs remain stable when a collection refresh changes ordering.
  await page.route('**/data/newsroom.json?*',async route=>{
   const response=await route.fetch();const data=await response.json();
   data.articles.reverse();await route.fulfill({json:data});
  });
  await page.evaluate(()=>loadLiveNews());
  assert.match(await page.locator('#news-items [data-bookmark]').textContent(),/저장됨/);
  await page.locator('#news-search').fill('');
  await page.locator('[data-filter="'+selectedCategory+'"]').click();
  assert.ok(await page.locator('#news-items .news-item').count()>0);
  await page.locator('[data-filter="저장"]').click();
  assert.equal(await page.locator('#news-items .news-item').count(),1);
  await page.route('**/data/health.json?*',route=>route.fulfill({json:{
   status:'failed',checked_at:'2026-10-26T13:30:00+09:00',successful_sources:0,
   source_count:4,sources:[{name:'시험 장애',status:'error'}]
  }}));
  await page.evaluate(()=>loadLiveNews());
  assert.equal(await page.locator('#rss-health-chip').textContent(),'FETCH FAILED');
  await page.locator('[data-filter="전체"]').click();
  assert.equal(await page.locator('#news-items .news-item').count(),expectedCount);
  await page.locator('[data-nav="briefing"]').click();
  const briefing=await (await page.request.get(base+'/data/briefing.json')).json();
  assert.equal(await page.locator('#briefing-state').textContent(),briefing.items.length?'브리핑 후보 생성':'새 기사 없음');
  // Compatibility: old categories still work with new filter buttons.
  await page.unroute('**/data/newsroom.json?*');
  const inverse={'관광정책':'정책','인바운드':'수요','여행산업':'산업','문화·트렌드':'지역','경제·시장':'리서치'};
  await page.route('**/data/newsroom.json?*',route=>route.fulfill({status:404,body:'not found'}));
  await page.route('**/data/news.json?*',route=>route.fulfill({json:{...archiveSnapshot,articles:archiveSnapshot.articles.map(a=>({...a,category:inverse[a.category]||a.category,record_type:a.source_id==='kosis_recent'?undefined:a.record_type}))}}));
  await page.evaluate(()=>loadLiveNews());
  await page.locator('[data-nav="news"]').click();
  await page.locator('[data-filter="'+selectedCategory+'"]').click();
  assert.ok(await page.locator('#news-items .news-item').count()>0);
  await page.locator('[data-filter="전체"]').click();
  assert.equal(await page.locator('#news-items .news-item').count(),expectedCount);
  for(const filing of archiveSnapshot.articles.filter(a=>(a.record_type||'news')!=='news'||a.archived_only)){
   assert.equal(await page.locator('#news-items').getByText(filing.title,{exact:true}).count(),0);
  }
  const labels=await page.locator('#news-items .news-meta').allTextContents();
  assert.ok(labels[0].includes('한국 관광산업 직접 관련'));
  assert.deepEqual(errors,[]);
  console.log('PASS: live articles, search, detail, stable bookmark, partial/all-failure status, preservation, briefing and legacy fallback, filing exclusion and editorial labels; no JS errors');
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
