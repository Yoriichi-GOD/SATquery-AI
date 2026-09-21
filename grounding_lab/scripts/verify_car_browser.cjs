const { chromium } = require('C:/Users/nrgen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
(async()=>{
 const out='C:/Users/nrgen/.codex/scratch/SATquery AI/grounding_lab/evidence/browser-car';fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://localhost:8766/');await page.waitForLoadState('networkidle');
 await page.screenshot({path:out+'/desktop-empty.png'});
 await page.getByRole('button',{name:'Try car',exact:true}).click();await page.locator('#run').waitFor({state:'visible'});
 await page.waitForFunction(()=>!document.getElementById('run').disabled);
 // Wait for independent HTTP tests to release the local worker.
 await page.waitForFunction(async()=>!(await(await fetch('/api/status')).json()).busy,{},{timeout:180000});
 await page.locator('#run').click();await page.locator('#result').waitFor({state:'visible',timeout:180000});
 await page.screenshot({path:out+'/desktop-result.png'});
 const objectCount=await page.locator('#metrics').innerText();
 const before=await page.locator('.image-panel').boundingBox();await page.locator('.controls').evaluate(e=>e.scrollTop=e.scrollHeight);const after=await page.locator('.image-panel').boundingBox();
 if(JSON.stringify(before)!==JSON.stringify(after))throw Error('Image panel moved while controls scrolled');
 await page.locator('#stages .stage').nth(2).click();await page.locator('#dialog').waitFor({state:'visible'});await page.screenshot({path:out+'/full-outline.png'});await page.getByRole('button',{name:'Close ×'}).click();
 await page.getByRole('button',{name:'Switch theme'}).click();await page.locator('.controls').evaluate(e=>e.scrollTop=0);await page.screenshot({path:out+'/desktop-light.png'});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:out+'/mobile.png',fullPage:true});const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);if(overflow)throw Error('Mobile horizontal overflow');
 fs.writeFileSync(out+'/verification.json',JSON.stringify({errors,objectCount,imagePanelFixed:JSON.stringify(before)===JSON.stringify(after),mobileOverflow:overflow,viewportDesktop:[1440,1000],viewportMobile:[390,844]},null,2));
 await page.locator('#category').selectOption('stadium'); if(await page.locator('#result').isVisible())throw Error('Old results remain after changing category'); if(errors.length)throw Error(errors.join(';'));console.log('Browser checks passed',objectCount);await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});


