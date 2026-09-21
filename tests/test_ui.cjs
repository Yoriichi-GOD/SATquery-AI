// DOM wiring tests with explicit test doubles, not a browser or visual validation.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const elements=new Map();
class Element {
 constructor(tag='div',id=''){this.tagName=tag;this.id=id;this.children=[];this.dataset={};this.style={};this.value='';this.hidden=false;this.checked=true;this.textContent='';this.classList={add(){},remove(){},toggle(){}};this.parentElement=this;}
 append(...children){this.children.push(...children);for(const c of children){c.parentElement=this;if(c.id)elements.set(c.id,c)}}
 before(child){this.parentElement.append(child)}
 replaceChildren(...children){this.children=[];this.append(...children)}
 setAttribute(k,v){this[k]=v}
 set innerHTML(html){for(const m of html.matchAll(/<(\w+)\b[^>]*\bid="([^"]+)"[^>]*>/g)){const e=new Element(m[1],m[2]);e.hidden=/\bhidden\b/.test(m[0]);e.value=/\bvalue="([^"]*)"/.exec(m[0])?.[1]||'';elements.set(e.id,e);this.append(e)}}
 focus(){}
 click(){}
}
const html=fs.readFileSync('web/index.html','utf8');new Element().innerHTML=html;
const byId=id=>{assert(elements.has(id),`Missing element #${id}`);return elements.get(id)};
byId('mode').value='baseline';
const development=JSON.parse(fs.readFileSync('results/overnight-development-rescore.json','utf8'));
const run=JSON.parse(fs.readFileSync('results/ndvi-integration.json','utf8'));
// Reused analytical evidence is only a fixture here; no fresh computation claimed.
run.routing={reason:'TEST FIXTURE: calibrated coverage dispatch'};
run.processing_stages=Object.fromEntries(['rgb','false-colour','evidence','mask'].map(n=>[n,`/api/runs/${run.id}/${n}`]));
const calls=[];
const context=vm.createContext({document:{getElementById:byId,createElement:t=>new Element(t),querySelectorAll:()=>[],documentElement:{dataset:{}}},localStorage:{getItem(){return 'dark'},setItem(){}},matchMedia:()=>({matches:true}),setInterval:()=>1,clearInterval(){},setTimeout,Date,FormData,URL,Blob,console,
 fetch:async(url,options)=>{calls.push({url,options});let data={};
 if(url==='/api/status')data={state:'idle'};
 else if(url==='/api/development')data=development;
 else if(url==='/api/images')data=run.image;
 else if(url==='/api/analyze'){
   if(options.body.get('question').includes('last year'))return {ok:false,json:async()=>({detail:{tool:'refuse',reason:'Temporal analysis is not implemented.'}})};
   data={id:run.id};
 }else if(url===`/api/runs/${run.id}`)data=run;
 else throw Error(`Unexpected test request: ${url}`);
 return {ok:true,json:async()=>data};
 }});
vm.runInContext(fs.readFileSync('web/app.js','utf8'),context);
(async()=>{
 await vm.runInContext('loadDevelopment()',context);
 assert.equal(byId('base-score').textContent,'38.3%');assert.equal(byId('adapter-score').textContent,'78.3%');
 assert.equal(byId('regressions').children.length,2);assert.equal(byId('dev-rows').children.length,4);
 assert.equal(byId('scene-sample').parentElement.id,'empty');
 await vm.runInContext("upload(new Blob(['test'],{type:'image/tiff'}))",context);
 assert.equal(byId('filename').textContent,'corrected.tif');assert.equal(byId('scene-sample').hidden,true);
 byId('question').value='Calculate NDVI';
 await byId('question-form').onsubmit({preventDefault(){}});
 assert.equal(calls.filter(c=>c.url==='/api/analyze').length,1);
 assert.equal(calls.some(c=>c.url==='/api/ndvi'),false);
 assert.equal(byId('stage-grid').children.length,4);
 assert.equal(byId('processing-stages').hidden,false);
 assert.match(byId('stage-context').textContent,/corrected.tif.*0.50/);
 byId('question').value='Compare this to last year';
 await byId('question-form').onsubmit({preventDefault(){}});
 assert.match(byId('feedback').textContent,/Temporal/);assert.equal(byId('answer-state').hidden,true);
 assert.equal(byId('processing-stages').hidden,true);assert.equal(byId('ndvi-overlay').hidden,true);
 assert.equal(byId('analyze').disabled,false);
 assert(!html.includes('value="ndvi"'));
 console.log('PASS: development comparison, regressions, sample empty state, loaded filename, automatic dispatch, four run artifact views, refusal clearing, restored controls. DOM doubles only; no visual QA.');
})().catch(e=>{console.error(e);process.exitCode=1});
