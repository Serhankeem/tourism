/* Real official seed; simulated failures stay in browser memory and are never saved. */
const {chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true});const base=process.env.TOURISM_TEST_URL||'http://127.0.0.1:8010';const dir=process.env.MACRO_SCREENSHOTS||'/tmp/macro-v05';fs.mkdirSync(dir,{recursive:true});const errors=[];
 try{
  const request=await browser.newContext();const snap=await(await request.request.get(base+'/data/macro.json')).json();
  const inbound=snap.indicators.find(i=>i.id==='kto_inbound'),outbound=snap.indicators.find(i=>i.id==='kto_outbound');assert.ok(inbound.months>=36&&outbound.months>=36);
  assert.equal(snap.indicators.filter(i=>i.connected&&i.priority===1).length,2);assert.equal(snap.indicators.filter(i=>i.connected&&i.country).length,5);
  assert.ok(snap.indicators.filter(i=>i.connected).every(i=>i.observations.every(o=>/^[a-f0-9]{64}$/.test(o.file_sha256)&&o.verification_status==='official_file_validated')));
  for(const path of ['/data/macro_archive.json','/macro_sources.json','/collector_state/macro_archive.json'])assert.equal((await request.request.get(base+path)).status(),404);
  const wait=async p=>p.waitForFunction(()=>window.MacroMonitor?.database&&/핵심 월간/.test(document.getElementById('macro-status').textContent));
  for(const width of [1440,1024,768,390]){
   const page=await browser.newPage({viewport:{width,height:1000},isMobile:width===390});page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await wait(page);
   const home=await page.locator('#home-macro-kpis [data-value]').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.value)));assert.deepEqual(home,[inbound.latest.value,outbound.latest.value]);
   assert.equal(await page.locator('#home-macro-kpis').getByText('미연동',{exact:true}).count(),2);
   assert.match(await page.locator('#home-macro-status').textContent(),/핵심 월간 2\/4개/);
   assert.equal(await page.locator('#chart-overview rect').count(),12);assert.equal(await page.locator('#chart-overview rect').last().getAttribute('data-value'),String(inbound.latest.value));
   const weather=await page.locator('#weather-score').textContent();assert.equal(weather,'68');
   if(width===1440||width===390){await page.evaluate(()=>document.activeElement?.blur());await page.screenshot({path:`${dir}/home-${width}.png`,fullPage:true});}
   await page.evaluate(()=>navigate('macro'));assert.equal(await page.locator('#rss-health-chip').isVisible(),false,'News health is not Macro health');
   assert.deepEqual(await page.locator('#macro-kpis [data-value]').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.value))),home);
   assert.equal(await page.locator('#macro-registry .macro-registry-row').count(),snap.indicators.length);
   if(width>=1024){await page.locator('#macro-registry').focus();await page.keyboard.press('End');await page.waitForFunction(()=>document.getElementById('macro-registry').scrollTop>0);assert.ok(await page.locator('#macro-registry').evaluate(n=>n.scrollTop>0),'Registry keyboard scroll');await page.locator('#macro-registry').evaluate(n=>n.scrollTop=0);}
   const latestText=await page.locator('#macro-kpis').textContent();assert.match(latestText,new RegExp(inbound.latest_period));assert.match(latestText,/확정 여부 미표기/);
   assert.equal(await page.locator('#chart-macro rect').count(),36);await page.locator('#macro-range').selectOption('12');assert.equal(await page.locator('#chart-macro rect').count(),12);
   await page.locator('#macro-range').selectOption(String(inbound.months));assert.equal(await page.locator('#chart-macro rect').count(),inbound.months);
   await page.locator('#chart-toggle-macro [data-chart="growth"]').click();assert.equal(await page.locator('#chart-macro .macro-series-gap').count(),12,'No fabricated prior-year growth for first twelve months');
   await page.locator('#chart-toggle-macro [data-chart="count"]').click();assert.equal(await page.locator('#chart-macro .macro-series-gap').count(),0);
   await page.locator('#macro-metric').selectOption('kto_outbound');assert.equal(await page.locator('#chart-macro rect').last().getAttribute('data-value'),String(outbound.latest.value));
   assert.match(await page.locator('#macro-comparisons').textContent(),/전월 대비/);assert.match(await page.locator('#macro-comparisons').textContent(),/전년 동월 대비/);assert.match(await page.locator('#macro-comparisons').textContent(),/연초 누적/);
   await page.locator('#macro-metric').selectOption('kto_inbound_jp');assert.match(await page.locator('#macro-chart-meta').textContent(),/일본/);
   await page.locator('#macro-metric').selectOption('kto_inbound');await page.locator('#macro-range').selectOption('36');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   assert.equal(await page.locator('#weather-score').textContent(),weather,'Actual statistics never change simulation weights/input');
   if(width===1440||width===390){await page.evaluate(()=>document.activeElement?.blur());await page.screenshot({path:`${dir}/macro-${width}.png`,fullPage:true});}
   // Missing monthly observation is a gap, not 0 or a previous available month.
   await page.evaluate(()=>{const i=MacroMonitor.database.indicators.find(i=>i.id==='kto_inbound');const period=i.observations.at(-2).period;i.observations=i.observations.filter(o=>o.period!==period);MacroMonitor.renderCharts();});
   assert.equal(await page.locator('#chart-macro .macro-series-gap').count(),1);assert.equal(await page.locator('#chart-macro rect').count(),35);await page.evaluate(()=>MacroMonitor.load());
   // All-fetch failure retains the last valid DB and an explicit failure label.
   await page.route('**/data/macro.json?*',r=>r.fulfill({status:503,body:'BROWSER TEST OUTAGE'}));await page.evaluate(()=>MacroMonitor.load());assert.deepEqual(await page.locator('#macro-kpis [data-value]').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.value))),home);assert.match(await page.locator('#macro-status').textContent(),/이전 검증값 보존/);assert.match(await page.locator('#macro-kpis').textContent(),/자료 수집 실패/);await page.unroute('**/data/macro.json?*');await page.evaluate(()=>MacroMonitor.load());
   await page.route('**/data/macro_health.json?*',async route=>{const response=await route.fetch();const health=await response.json();health.status='failed';health.sources[0].status='error';await route.fulfill({json:health});});await page.evaluate(()=>MacroMonitor.load());assert.match(await page.locator('#macro-status').textContent(),/수집 실패/);assert.deepEqual(await page.locator('#macro-kpis [data-value]').evaluateAll(nodes=>nodes.map(n=>Number(n.dataset.value))),home);await page.unroute('**/data/macro_health.json?*');
   await page.close();
  }
  const empty=await browser.newPage();await empty.route('**/data/macro.json?*',r=>r.fulfill({status:404,body:'missing'}));await empty.goto(base+'/#macro');await empty.waitForFunction(()=>window.MacroMonitor&&/검증된 공식 통계 데이터가 없습니다/.test(document.getElementById('macro-status').textContent));assert.equal(await empty.locator('#macro-kpis [data-value]').count(),0);assert.equal(await empty.locator('#chart-macro rect').count(),0);
  assert.deepEqual(errors,[]);console.log('PASS: real official monthly history, home/Macro exact values, 4 widths, definitions/pending financial metrics, ranges/gaps/missing growth, source-date/finality, refresh/all-failure preservation, empty initial state, private archive isolation and unchanged weather simulation');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
