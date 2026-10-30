// Presentation regression; synthetic news is browser-local and never written to DB.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const base=process.env.TOURISM_TEST_URL||'http://127.0.0.1:8010';
 const dir=process.env.UI2_OUTPUT||'/tmp/currentourism-ui2';fs.mkdirSync(dir,{recursive:true});
 const errors=[];
 try{
  for(const width of [1440,768,390,320]){
   const page=await browser.newPage({viewport:{width,height:1000},reducedMotion:"reduce"});page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base);await page.waitForFunction(()=>!newsLoading&&window.ResearchLibrary?.database&&window.MacroMonitor?.database);
   assert.deepEqual(await page.locator('.primary-navigation a').allTextContents(),['오늘의 관광 날씨는?','뉴스','데일리 브리핑','리서치','관광지표','소개']);
   assert.equal(await page.locator('.primary-navigation small').count(),0);
   for(const selector of ['#brand-logo','.footer-logo']){
    const r=await page.locator(selector).evaluate(e=>({loaded:e.complete&&e.naturalWidth>0,ratio:e.width/e.height,native:e.naturalWidth/e.naturalHeight,src:e.getAttribute('src')}));
    assert.ok(r.loaded);assert.equal(r.native,2);assert.ok(Math.abs(r.ratio-r.native)<.02);assert.match(r.src,/currentourism-new-airplane-logo\.png\?v=7f92affea61c5719/);
   }
   await page.screenshot({path:`${dir}/overview-${width}.png`,fullPage:true});
   await page.locator('#kakao-channel-cta').click();assert.ok(await page.locator('#kakao-layer').evaluate(e=>e.classList.contains('open')));await page.locator('#kakao-dialog-close').click();
   await page.locator('#kakao-banner-close').click();assert.equal(await page.locator('#kakao-banner').isVisible(),false);
   await page.reload();await page.waitForFunction(()=>!newsLoading);assert.equal(await page.locator('#kakao-banner').isVisible(),false);
   await page.evaluate(()=>navigate('weather'));
   const colors=new Set();
   for(const [input,tone,score] of [[-30,'rain',11],[0,'cloudy',50],[15,'partly',70],[35,'sunny',96]]){
    await page.evaluate(v=>{for(const id of ['s-arrivals','s-spend','s-air'])document.getElementById(id).value=v;weather();},input);
    assert.equal(await page.locator('#weather-score').textContent(),String(score));
    for(const card of ['.weather-result','.weather-panel'])assert.equal(await page.locator(card).getAttribute('data-weather'),tone);
    assert.equal(await page.locator('#home-weather-score').textContent(),String(score));
    colors.add(await page.locator('.weather-result').evaluate(e=>getComputedStyle(e).backgroundColor));
    if(width===1440)await page.screenshot({path:`${dir}/weather-${tone}.png`,fullPage:true});
   }
   assert.equal(colors.size,4);await page.locator('#reset-weather').click();assert.equal(await page.locator('#weather-score').textContent(),'68');
   await page.evaluate(()=>navigate('about'));
   assert.equal(await page.locator('.sources-table tbody tr').count(),7);
   assert.match(await page.locator('.sources-table').textContent(),/승인 대기 · 수치 미게시/);
   assert.equal(await page.locator('#page-about').getByText('Research Library 탐색 →').count(),0);
   for(const id of ['news-source-details','research-source-details']){
    const details=page.locator('#'+id),summary=details.locator('summary');
    assert.equal(await details.evaluate(e=>e.open),false,'Source details default collapsed');
    assert.ok(await page.locator('.sources-table').isVisible());
    await summary.focus();await page.keyboard.press('Enter');
    assert.equal(await details.evaluate(e=>e.open),true);
    assert.ok(await details.locator('.source-status-grid').isVisible());
    assert.ok(await details.locator('a[href]').count()>0,'Keep actual official source links');
    await summary.click();assert.equal(await details.evaluate(e=>e.open),false);
   }
   await page.screenshot({path:`${dir}/about-${width}.png`,fullPage:true});
   for(const route of ['about','news','research','macro','weather','briefing']){
    await page.evaluate(r=>navigate(r),route);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${width}/${route} horizontal overflow`);
    assert.equal(await page.locator('.primary-navigation [aria-current="page"]').count(),1);
   }
   await page.evaluate(()=>{NEWS.splice(0,NEWS.length,...Array.from({length:25},(_,i)=>({id:'browser-only-'+i,title:'인공 UI 테스트 '+i,category:'여행산업',source:'브라우저 테스트',date:'2026',published_at:'2026-01-01',url:'https://example.com/'+i,keywords:[]})));state.query='';state.filter='전체';state.newsPage=1;state.newsPageSize=10;renderNews();navigate('news');});
   assert.equal(await page.locator('#news-items .news-item').count(),10);
   assert.equal(await page.locator('#news-page-buttons [aria-label="다음 페이지"]').textContent(),'>');
   await page.locator('#news-page-buttons [aria-label="다음 페이지"]').click();assert.equal(await page.locator('#news-page-buttons [aria-current="page"]').textContent(),'2');
   await page.locator('#news-page-size').selectOption('20');assert.equal(await page.locator('#news-items .news-item').count(),20);
   await page.evaluate(()=>navigate('research'));assert.equal(await page.locator('#research-page-buttons [aria-label="다음 페이지"]').textContent(),'>');
   await page.locator('#research-page-size').selectOption('20');assert.equal(await page.locator('#research-results .research-card').count(),20);
   await page.locator('.site-footer>a').click();assert.ok(await page.locator('#page-overview').isVisible());
   await page.close();
  }
  assert.deepEqual(errors,[]);console.log('PASS UI 2.0: four widths, 4 weather states, logos, banner persistence/dialog, sources table, both pagers, routes; no JS errors');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
