// Synthetic fixtures exist only inside this isolated browser context.
const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const base=process.env.TOURISM_TEST_URL||'http://127.0.0.1:8010',dir=process.env.BRIEF_OUTPUT||'/tmp/currentourism-pr11';fs.mkdirSync(dir,{recursive:true});
 try{
  for(const width of [320,390,768,1440]){
   const context=await browser.newContext({viewport:{width,height:1000},permissions:['clipboard-read','clipboard-write']});const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base);await page.waitForFunction(()=>window.MacroMonitor?.database&&window.BriefingUI?.edition);
   assert.match(await page.locator('#data-observation').textContent(),/2026-09/);assert.doesNotMatch(await page.locator('#data-observation').textContent(),/24 OCT 2026/);
   for(const route of ['overview','briefing']){
    await page.evaluate(r=>navigate(r),route);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    if([390,1440].includes(width))await page.screenshot({path:`${dir}/after-${route}-${width}.png`,fullPage:true});
   }
   // No fake archives on disk: route mocks create a known historical edition.
   const item={title:'브라우저 인공 테스트 항공 노선',source:'테스트',published_at:'2026-10-29T09:00:00+09:00',category:'항공·숙박',keywords:['항공'],url:'https://example.org/test-news'};
   const historical={schema_version:5,mode:'live_rss',briefing_date:'2026-10-29',generated_at:'2026-10-29T10:30:00+09:00',last_successful_fetch:'2026-10-29T10:29:00+09:00',status:'candidates_ready',items:[item]};
   await page.route('**/data/briefing_archive.json?*',r=>r.fulfill({json:{mode:'live_rss',briefings:[historical]}}));
   await page.evaluate(()=>BriefingUI.load());await page.locator('#briefing-edition').selectOption('2026-10-29');
   assert.equal(await page.locator('#briefing-news-list .news-item').count(),1);assert.match(await page.locator('#briefing-state').textContent(),/과거 브리프/);
   assert.equal(await page.locator('#briefing-news-list a').getAttribute('href'),item.url);
   await page.locator('#copy-brief').click();const copied=await page.evaluate(()=>navigator.clipboard.readText());assert.ok(copied.includes(item.title));assert.ok(copied.includes(item.published_at));assert.ok(copied.includes(item.url));
   await page.route('**/data/briefing.json?*',r=>r.fulfill({json:{...historical,briefing_date:'2026-10-30',generated_at:new Date().toISOString(),items:[],status:'no_recent_articles'}}));
   await page.evaluate(()=>BriefingUI.load());assert.equal(await page.locator('#briefing-edition').inputValue(),'2026-10-29','Refresh preserves selected historical edition');
   await page.locator('#briefing-edition').selectOption('current');assert.match(await page.locator('#briefing-state').textContent(),/신규 뉴스 없음/);assert.match(await page.evaluate(()=>BriefingUI.text()),/복사할 뉴스가 없습니다/);
   await page.route('**/data/briefing.json?*',r=>r.fulfill({status:503}));await page.evaluate(()=>BriefingUI.load());assert.match(await page.locator('#briefing-state').textContent(),/실패/);
   const original=await page.evaluate(()=>JSON.parse(JSON.stringify(MacroMonitor.database)));
   await page.evaluate(()=>{const db=JSON.parse(JSON.stringify(MacroMonitor.database)),i=db.indicators.find(i=>i.id==='kto_inbound');i.latest.value=1234567;i.latest.period='2026-10';i.latest.comparisons={...i.latest.comparisons,yoy_pct:12.3};i.observations.push({...i.latest});DataObservation.render(db,MacroMonitor.health);});
   assert.match(await page.locator('#data-observation').textContent(),/1,234,567/);assert.match(await page.locator('#data-observation').textContent(),/2026-10/);assert.match(await page.locator('#data-observation').textContent(),/\+12.30%/);
   await page.evaluate(db=>DataObservation.render(db,{status:'failed'}),original);assert.match(await page.locator('#data-observation').textContent(),/마지막 검증값 유지/);
   await page.evaluate(()=>DataObservation.render({mode:'verified_official_statistics',indicators:[{id:'kto_tourism_receipts',connected:true,latest:{value:999999999}}]},null));assert.match(await page.locator('#data-observation').textContent(),/관찰 불가/);assert.doesNotMatch(await page.locator('#data-observation').textContent(),/999,999,999/);
   assert.deepEqual(errors,[]);await context.close();
  }
  console.log('PASS: briefing archive/date/copy/empty/failure preservation; official observations/updates/failure/financial exclusion; four widths');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
