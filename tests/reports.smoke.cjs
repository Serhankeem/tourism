// Real report DB only: search/filter the entire DB, paginate 10/20, PC/mobile.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true});
 async function openResearch(page){
  if(await page.locator('#page-research').isVisible())return;
  if(await page.locator('#page-overview').isVisible()){await page.locator('.home-research-link a').click();return;}
  if(await page.locator('#menu-toggle').isVisible())await page.locator('#menu-toggle').click();
  await page.locator('.primary-navigation [data-nav="news"]').click();
  await page.locator('#page-news .news-subnav [data-goto="research"]').click();
 }
 const base=process.env.TOURISM_TEST_URL||'http://127.0.0.1:8010';
 const screenshots=process.env.REPORTS_SCREENSHOTS||'/tmp/research-screenshots';fs.mkdirSync(screenshots,{recursive:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1100}});const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const snapshot=await(await page.request.get(base+'/data/reports.json')).json();const count=snapshot.reports.length;
  assert.ok(count>20,'Real data is required for pagination verification');
  const fields=['access_type','category','keywords','published_at','publisher','report_type','title','url'];
  for(const r of snapshot.reports)assert.deepEqual(Object.keys(r).sort(),fields);
  await page.goto(base);await page.waitForFunction(()=>window.ResearchLibrary?.database.reports.length>0);
  await openResearch(page);
  assert.equal(await page.locator('#rss-health-chip').isVisible(),false);
  assert.equal(await page.locator('.kakao-float').isVisible(),false);
  assert.equal(await page.locator('#research-count').textContent(),String(count));
  assert.equal(await page.locator('#research-results .research-card').count(),10);
  const firstTitles=await page.locator('#research-results h3').allTextContents();
  await page.locator('[data-report-page="2"][aria-label="연구자료 2페이지"]').click();
  assert.equal(await page.locator('[data-report-page="2"][aria-label="연구자료 2페이지"]').getAttribute('aria-current'),'page');
  assert.notDeepEqual(await page.locator('#research-results h3').allTextContents(),firstTitles);
  await page.locator('#research-page-size').selectOption('20');
  assert.equal(await page.locator('#research-results .research-card').count(),20);
  assert.match(await page.locator('#research-result-count').textContent(),/1–20/);
  const last=snapshot.reports.find(r=>!firstTitles.includes(r.title));assert.ok(last);
  await page.locator('#research-search').fill(last.title);
  assert.ok((await page.locator('#research-results h3').allTextContents()).includes(last.title),'Search must include all pages');
  assert.equal(await page.evaluate(()=>ResearchLibrary.state.page),1);
  await page.locator('#research-search').fill('');await page.locator('#research-page-size').selectOption('10');
  const publisher='한국문화관광연구원';
  await page.locator('#research-publisher').selectOption(publisher);
  const pcount=snapshot.reports.filter(r=>r.publisher===publisher).length;
  assert.match(await page.locator('#research-result-count').textContent(),new RegExp('검색 결과 '+pcount+'건'));
  assert.equal(await page.locator('#research-results .research-card').count(),Math.min(10,pcount));
  assert.match(await page.locator('#research-results .research-meta').first().textContent(),/발간연도 \d{4}년/);
  await page.locator('#research-region').selectOption('해외');assert.equal(await page.locator('#research-results .research-card').count(),0);
  await page.locator('#research-region').selectOption('');await page.locator('#research-publisher').selectOption('');
  const type=snapshot.reports[0].report_type;
  await page.locator('#research-type').selectOption(type);
  const tcount=snapshot.reports.filter(r=>r.report_type===type).length;
  assert.match(await page.locator('#research-result-count').textContent(),new RegExp('검색 결과 '+tcount+'건'));
  await page.locator('#research-type').selectOption('');
  const category=snapshot.reports[0].category;
  await page.locator('#research-category').selectOption(category);
  const ccount=snapshot.reports.filter(r=>r.category===category).length;
  assert.match(await page.locator('#research-result-count').textContent(),new RegExp('검색 결과 '+ccount+'건'));
  await page.locator('#research-category').selectOption('');
  await page.locator('#research-sort').selectOption('oldest');const oldest=await page.locator('#research-results h3').first().textContent();
  await page.locator('#research-sort').selectOption('newest');assert.notEqual(await page.locator('#research-results h3').first().textContent(),oldest);
  const original=await page.locator('#research-results h3 a').first().getAttribute('href');assert.ok(snapshot.reports.some(r=>r.url===original));
  assert.equal(await page.locator('#research-results img,#research-results iframe').count(),0);
  assert.equal(await page.request.get(base+'/data/reports_archive.json').then(r=>r.status()),404);
  await page.evaluate(()=>{document.activeElement?.blur();scrollTo(0,0);});
  await page.screenshot({path:screenshots+'/research-desktop.png',fullPage:true});
  await page.locator('#page-research [data-goto="sources"]').click();await page.locator('#page-about').waitFor({state:'visible'});
  // Existing Newsroom and its pagination remain independent from Research.
  await page.locator('[data-nav="news"]').click();await page.waitForFunction(()=>!newsLoading);
  const newsCount=await page.evaluate(()=>NEWS.length);assert.ok(newsCount>0);
  assert.equal(await page.locator('#news-items .news-item').count(),Math.min(10,newsCount));
  await page.locator('#news-page-size').selectOption('20');assert.equal(await page.locator('#news-items .news-item').count(),Math.min(20,newsCount));
  await openResearch(page);assert.equal(await page.locator('#research-page-size').inputValue(),'10');
  // Failed Research refresh preserves the current valid report list.
  await page.route('**/data/reports.json?*',r=>r.fulfill({status:503,body:'test outage'}));
  await page.evaluate(()=>ResearchLibrary.load());assert.equal(await page.locator('#research-count').textContent(),String(count));
  assert.match(await page.locator('#research-status').textContent(),/기존 목록을 유지/);await page.unroute('**/data/reports.json?*');await page.evaluate(()=>ResearchLibrary.load());
  const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true});mobile.on('pageerror',e=>errors.push(e.message));
  await mobile.goto(base);await mobile.waitForFunction(()=>window.ResearchLibrary?.database.reports.length>0);await openResearch(mobile);
  assert.equal(await mobile.locator('#research-results .research-card').count(),10);
  assert.ok(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Mobile must not horizontally overflow');
  await mobile.locator('#research-page-size').selectOption('20');assert.equal(await mobile.locator('#research-results .research-card').count(),20);
  await mobile.locator('#research-page-size').selectOption('10');await mobile.evaluate(()=>{document.activeElement?.blur();scrollTo(0,0);});await mobile.screenshot({path:screenshots+'/research-mobile.png',fullPage:true});
  assert.deepEqual(errors,[]);
  console.log(`PASS: ${count} real reports; full-DB search, combined filters, 10/20 pagination/reset, sort, original links, no images/bodies, preservation, Newsroom pagination, PC/mobile layout`);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
