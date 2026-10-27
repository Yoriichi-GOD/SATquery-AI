// DOM behavior checks, not a browser rendering test. Uses isolated jsdom install.
const fs=require('node:fs');
const assert=require('node:assert/strict');
const {JSDOM}=require('../.runtime/ui-check/node_modules/jsdom');
const html=fs.readFileSync('paired_lab/web/index.html','utf8');
const dom=new JSDOM(html,{url:'http://localhost:8877',runScripts:'outside-only'});
const w=dom.window;
const questions=JSON.parse(fs.readFileSync('paired_lab/cdvqa-questions.json','utf8')).supported_questions;
w.fetch=async url=>({ok:true,json:async()=>url==='/api/status'?{state:'ready'}:url==='/api/samples'?[]:url==='/api/cdvqa-questions'?questions:{}});
w.HTMLElement.prototype.scrollIntoView=function(){};
require('node:vm').runInContext(fs.readFileSync('paired_lab/web/app.js','utf8'),dom.getInternalVMContext());
require('node:vm').runInContext(fs.readFileSync('paired_lab/web/upload_preview.js','utf8'),dom.getInternalVMContext());
const el=id=>w.document.getElementById(id);
(async()=>{
 await new Promise(resolve=>setImmediate(resolve));
 el('pair-mode').click();
 el('pair-specialist').value='cdvqa';await el('pair-specialist').onchange();
 assert.equal(el('pair-specialist').hidden,false);
 assert.equal(el('cdvqa-template').hidden,false);
 assert.equal(el('cdvqa-controls').hidden,false);
 assert.equal(el('cdvqa-template').options.length,questions.length+1);
 el('cdvqa-template').value=questions[0];el('cdvqa-template').onchange();
 assert.equal(el('question').value,questions[0]);
 for(const id of ['file-a','file-b']){
  el('cdvqa-aligned').checked=true;el(id).dispatchEvent(new w.Event('change'));
  assert.equal(el('cdvqa-aligned').checked,false);
 }
 el('cdvqa-aligned').checked=true;
 el('pair-specialist').value='auto';await el('pair-specialist').onchange();
 assert.equal(el('cdvqa-aligned').checked,false);
 assert.equal(el('cdvqa-controls').hidden,true);
 assert.equal(el('file-a').accept,'.tif,.tiff');
 el('mode-b').value='sar';el('mode-b').dispatchEvent(new w.Event('change'));
 assert.match(el('mode-b').nextElementSibling.textContent,/SAR/);
 el('pair-specialist').value='cdvqa';await el('pair-specialist').onchange();
 assert.equal(el('mode-b').value,'optical');
 assert.match(el('mode-b').nextElementSibling.querySelector('button').textContent,/Optical/);
 assert.equal(el('cdvqa-template').options.length,questions.length+1);
 const saved=JSON.parse(fs.readFileSync('.runtime/repro-20261019/cdvqa-http/verification.json','utf8'));
 w.showResult(saved.state.result);
 assert.equal(el('answer').textContent,saved.state.result.answer);
 assert.equal(el('scores').querySelectorAll('tr').length,20);
 assert.match(el('download').href,/evidence\.zip$/);
 assert.equal(el('views').querySelectorAll('.stage-strip button').length,2);
 assert.match(el('limits').textContent,/not general-purpose VQA/);
 console.log('PASS: dynamic templates, question selection, mode switching, alignment reset, modality label sync, real-result DOM, 19 scores, input views and evidence link. DOM-only; no rendered layout claim.');
 dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1});
