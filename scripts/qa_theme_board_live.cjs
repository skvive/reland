// Public, read-only visual smoke for RE:LAND 9 theme boards.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const out='qa-screens';
fs.mkdirSync(out,{recursive:true});
const base=process.env.QA_URL||'https://reland.lexid.site';
(async()=>{
  const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  const errors=[];const results={base,checks:[],errors};
  try {
    const desktop=await browser.newContext({viewport:{width:1440,height:900},deviceScaleFactor:1});
    const page=await desktop.newPage();
    page.on('pageerror',e=>errors.push('community: '+e.message));
    const resp=await page.goto(base+'/community',{waitUntil:'domcontentloaded',timeout:60000});
    assert.equal(resp.status(),200);
    await page.locator('.theme-board-card').first().waitFor({timeout:45000});
    assert.equal(await page.locator('.theme-board-card').count(),9);
    results.checks.push('Desktop: nine themed cards rendered');
    const titles=await page.locator('.theme-board-card h3').allTextContents();
    assert.equal(new Set(titles).size,9);
    const covers=await page.locator('.theme-board-cover').evaluateAll(nodes=>nodes.map(n=>getComputedStyle(n).backgroundImage));
    assert.equal(new Set(covers).size,9);
    assert(covers.every(c=>c.includes('cover-')));
    results.checks.push('Nine distinct AI background images resolved in style');
    await page.screenshot({path:out+'/01-community-desktop.png',fullPage:true});
    const [boardPage]=await Promise.all([desktop.waitForEvent('page',{timeout:20000}),page.locator('.theme-board-card a').first().click()]);
    await boardPage.waitForLoadState('domcontentloaded');
    assert.match(boardPage.url(),/\/board\/neighborhood/);
    await boardPage.locator('.main-panel').waitFor({timeout:45000});
    assert.equal(await boardPage.locator('.side-nav a').count(),9);
    const local=await boardPage.locator('.member-card').count();
    assert(local>=1, 'first themed board must list existing local community');
    results.checks.push('Parent board opens in new tab; nine sidebar channels + local rooms visible');
    await boardPage.screenshot({path:out+'/02-board-desktop.png',fullPage:true});
    const mobile=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
    const m=await mobile.newPage();
    m.on('pageerror',e=>errors.push('mobile community: '+e.message));
    await m.goto(base+'/community',{waitUntil:'domcontentloaded',timeout:60000});
    await m.locator('.theme-board-card').first().waitFor({timeout:45000});
    assert.equal(await m.locator('.theme-board-card').count(),9);
    const dims=await m.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:document.documentElement.clientWidth}));
    assert(dims.scroll<=dims.width+4,'Mobile theme landing horizontal overflow '+JSON.stringify(dims));
    await m.screenshot({path:out+'/03-community-mobile.png',fullPage:true});
    await m.goto(base+'/board/seoul',{waitUntil:'domcontentloaded',timeout:60000});
    await m.locator('.main-panel').waitFor({timeout:45000});
    const dims2=await m.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:document.documentElement.clientWidth}));
    assert(dims2.scroll<=dims2.width+4,'Mobile board horizontal overflow '+JSON.stringify(dims2));
    await m.screenshot({path:out+'/04-board-mobile.png',fullPage:true});
    results.checks.push('Mobile 390px: all nine categories render, no horizontal overflow');
    assert.equal(errors.length,0,errors.join(' | '));
    results.status='PASS';
  }catch(e){results.status='FAIL';results.failure=String(e.stack||e);throw e}
  finally {fs.writeFileSync(out+'/report.json',JSON.stringify(results,null,2));await browser.close();console.log(JSON.stringify(results))}
})().catch(e=>{console.error(e);process.exit(1)});
