// Behavioural tests with DOM doubles. These do not render CSS or replace browser checks.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const defaultSource=[__dirname+'/../paired_lab/web/workspace-shell.js',__dirname+'/../web/workspace-shell.js',__dirname+'/workspace-shell.js'].find(file=>fs.existsSync(file));
const source=fs.readFileSync(process.argv[2]||defaultSource,'utf8');
function setup({missingHeader=false,reduce=false,noAnimation=false}={}){
  let height=96;const values=new Map(),docEvents={},headerEvents={},windowEvents={},frames=[],animations=[];
  const root={dataset:{},style:{getPropertyValue:key=>values.get(key),setProperty:(key,value)=>values.set(key,value)}};
  const section={hidden:false,animate:noAnimation?undefined:(keyframes,options)=>{
    const item={keyframes,options,cancelled:false,cancel(){this.cancelled=true;}};animations.push(item);return item;
  }};
  const header={getBoundingClientRect:()=>({height}),addEventListener:(name,fn)=>headerEvents[name]=fn};
  const media={matches:reduce,addEventListener:(name,fn)=>media.changed=fn};
  let resize;
  const document={documentElement:root,querySelector:()=>missingHeader?null:header,querySelectorAll:()=>[{hidden:true},section],
    addEventListener:(name,fn)=>docEvents[name]=fn,fonts:{ready:Promise.resolve()}};
  vm.runInNewContext(source,{document,window:{addEventListener:(name,fn)=>windowEvents[name]=fn},
    matchMedia:()=>media,ResizeObserver:class{constructor(fn){resize=fn;}observe(){}},requestAnimationFrame:fn=>frames.push(fn)});
  return {root,values,animations,section,media,resize,windowEvents,docEvents,frames,
    setHeight:value=>height=value,
    click:(detail=1,isNav=true)=>headerEvents.click({detail,target:{closest:()=>isNav?{}:null}}),
    flush:()=>{while(frames.length)frames.shift()();}};
}
test('header space follows wrapping navigation, zero height never collapses the offset',()=>{
  const c=setup();assert.equal(c.values.get('--sq-header-h'),'96px');
  c.setHeight(147.2);c.resize();assert.equal(c.values.get('--sq-header-h'),'148px');
  c.setHeight(0);c.windowEvents.resize();assert.equal(c.values.get('--sq-header-h'),'148px');
});
test('font completion remeasures header height',async()=>{
  const c=setup();c.setHeight(130);await Promise.resolve();assert.equal(c.values.get('--sq-header-h'),'130px');
});
test('pointer navigation gives short feedback on the visible section only',()=>{
  const c=setup();c.docEvents.pointerdown();c.click();c.flush();
  assert.equal(c.root.dataset.sqInput,'pointer');assert.equal(c.animations.length,1);
  assert.equal(c.animations[0].options.duration,180);assert.equal(c.animations[0].keyframes.at(-1).opacity,1);
});
test('keyboard cancels active motion and never starts an entrance',()=>{
  const c=setup();c.click();c.flush();c.docEvents.keydown();c.click(0);c.flush();
  assert.equal(c.root.dataset.sqInput,'keyboard');assert.equal(c.animations.length,1);assert(c.animations[0].cancelled);
});
test('rapid navigation abandons stale queued motion',()=>{
  const c=setup();c.click();c.click();c.flush();assert.equal(c.animations.length,1);
});
test('reduced motion starts instantly and cancels existing motion if preference changes',()=>{
  const a=setup({reduce:true});a.click();a.flush();assert.equal(a.animations.length,0);
  const b=setup();b.click();b.flush();b.media.matches=true;b.media.changed();assert(b.animations[0].cancelled);
});
test('theme and other header controls do not animate the evidence',()=>{
  const c=setup();c.click(1,false);c.flush();assert.equal(c.animations.length,0);
});
test('missing header or unavailable animation API leaves content usable',()=>{
  assert.doesNotThrow(()=>setup({missingHeader:true}));const c=setup({noAnimation:true});c.click();assert.doesNotThrow(c.flush);
});
