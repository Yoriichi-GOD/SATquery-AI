'use strict';
const $=s=>document.querySelector(s);
const element=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e};
function metric(parent,label,value){const e=element('div');e.append(element('strong',value),element('p',label));parent.append(e)}
function table(headers,rows){const t=element('table'),h=element('tr');headers.forEach(x=>h.append(element('th',x)));t.append(h);for(const row of rows){const r=element('tr');row.forEach(x=>r.append(element('td',String(x))));t.append(r)}return t}
function tab(evidence){$('#lab').hidden=evidence;$('#evaluation').hidden=!evidence;$('.intro').hidden=evidence;$('#lab-tab').classList.toggle('active',!evidence);$('#eval-tab').classList.toggle('active',evidence)}
$('#lab-tab').onclick=()=>tab(false);$('#eval-tab').onclick=()=>tab(true);
function evidenceTab(detail){$('#eval-content').hidden=!detail;$('#evidence-overview').hidden=detail;$('#overview-tab').classList.toggle('active',!detail);$('#rigorous-tab').classList.toggle('active',detail)}
$('#overview-tab').onclick=()=>evidenceTab(false);$('#rigorous-tab').onclick=()=>evidenceTab(true);
$('#theme').onclick=()=>{document.documentElement.dataset.theme=document.documentElement.dataset.theme==='dark'?'light':'dark'};
if(location.hash==='#evidence')tab(true);

const byId=id=>document.getElementById(id);let layers=[],selected,opticalViews={},answerRequest=0;
const add=(tag,text,parent)=>{const e=document.createElement(tag);e.textContent=text;parent.appendChild(e);return e};
async function read(url){const r=await fetch(url);if(!r.ok)throw Error(`Evidence request failed (${r.status})`);return r.json()}
function draw(){const svg=byId('map');svg.replaceChildren();const points=[];function flatten(c){if(typeof c[0]==='number')points.push(c);else c.forEach(flatten)}layers.forEach(f=>flatten(f.geometry.coordinates));if(!points.length)return;let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;for(const p of points){x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);}const cos=Math.cos((y0+y1)/2*Math.PI/180),scale=Math.min(640/Math.max((x1-x0)*cos,1e-8),290/Math.max(y1-y0,1e-8));const xy=p=>[30+(p[0]-x0)*cos*scale,320-(p[1]-y0)*scale];const visible=new Set([...document.querySelectorAll('#toggles input:checked')].map(e=>e.value));for(const f of layers){const kind=f.properties.kind;if(!visible.has(kind)&&!(kind==='road'&&visible.has('bridge')))continue;const geom=f.geometry;let paths=geom.type==='Polygon'?[geom.coordinates]:geom.type==='MultiPolygon'?geom.coordinates:geom.type==='LineString'?[[geom.coordinates]]:[];for(const polygon of paths){const e=document.createElementNS('http://www.w3.org/2000/svg','path');e.setAttribute('d',polygon.map(ring=>ring.map((p,i)=>(i?'L':'M')+xy(p).join(',')).join(' ')+(geom.type.includes('Polygon')?' Z':'')).join(' '));e.setAttribute('fill',kind==='debris-candidate'?'#bd7f52':kind==='new-water-candidate'?'var(--gold)' :kind==='building'?'var(--text)' :'none');e.setAttribute('fill-opacity',(kind==='new-water-candidate'||kind==='debris-candidate')?'0.35':'1');e.setAttribute('stroke',kind==='new-water-candidate'?'var(--gold)' :'var(--muted)' );e.setAttribute('stroke-width',kind==='bridge'||kind==='road'?'4':'1');const title=document.createElementNS('http://www.w3.org/2000/svg','title');title.textContent=f.id;e.append(title);svg.append(e)}}}
async function show(){answerRequest++;byId('analysis-result').hidden=true;try{selected=byId('run').value;const base='/runs/'+encodeURIComponent(selected)+'/';const [r,m,a,l,frozen]=await Promise.all(['result.json','manifest.json','connectivity.json','layers.geojson','freeze.json'].map(f=>read(base+f)));byId('kind').textContent=r.synthetic?'Synthetic software verification':'Real observations · unvalidated baseline';document.querySelector('.visual-note').textContent=r.synthetic?'Synthetic calculation fixture, not a real event.':`Sentinel-1 · ${m.pre.datetime.slice(0,10)} / ${m.post.datetime.slice(0,10)} · OSM ${m.osm_snapshot.slice(0,10)}. Gold marks water candidates, not confirmed flood damage.`;byId('name').textContent=r.event_name;byId('dates').textContent=`Before: ${m.pre.datetime} · After: ${m.post.datetime}`;const s=r.summary;byId('stats').replaceChildren();for(const [name,value] of [['Candidate area',s.new_water_m2+' m²'],['Intersected buildings',s.exposed_buildings],['Intersected roads',s.exposed_road_m+' m'],['Potentially cut off',s.connectivity_assessed===false?'Not assessed':s.potentially_cut_off]]){const d=add('div','',byId('stats'));add('div',value,d).className='value';add('small',name,d)}byId('coverage').textContent=`Valid coverage: ${s.valid_pixels} / ${s.total_pixels} pixels. ${s.water_in_both_pixels} pixels marked as water in both dates.`;byId('access').replaceChildren();for(const row of a){const tr=add('tr','',byId('access'));add('td',row.name||row.id,tr);add('td',row.status.replaceAll('_',' '),tr);add('td',`${row.distance_before_m??'N/A'} m / ${row.distance_after_m??'N/A'} m`,tr)}byId('limits').replaceChildren();r.limitations.forEach(t=>add('li',t,byId('limits')));byId('downloads').replaceChildren();for(const [f,label] of [['prediction.tif','GeoTIFF'],['layers.geojson','GeoJSON'],['exposure.csv','Feature table'],['connectivity.json','Access results'],['sensitivity.json','Sensitivity'],['result.json','Calculations'],['freeze.json','Evidence hashes'],['report-en.html','English report'],['report-ne.html','नेपाली प्रतिवेदन']]){const e=add('a',label,byId('downloads'));e.href=base+f;e.target='_blank'}if(s.debris_candidate_m2!==undefined){const d=add('div','',byId('stats'));add('div',s.debris_candidate_m2+' m²',d).className='value';add('small','Debris candidates · unvalidated',d);for(const [f,label] of [['debris-candidates.tif','Debris candidate GeoTIFF'],['debris-exposure.csv','Debris intersections'],['topology-audit.json','Historical road audit']]){const e=add('a',label,byId('downloads'));e.href=base+f;e.target='_blank'}}await presentRecord(m,r,frozen);layers=l.features;const hasOpticalPreview=!!(opticalViews['optical-pre']?.url||opticalViews['optical-post']?.url);byId('view').disabled=!frozen.files['pre.png']&&!hasOpticalPreview;if(byId('view').disabled)byId('view').value='map';draw();updateView();byId('error').textContent=''}catch(e){byId('error').hidden=false;byId('error').textContent=e.message}}
byId('run').addEventListener('change',show);byId('toggles').addEventListener('change',draw);read('/api/runs').then(r=>{r.sort((a,b)=>Number(a.synthetic)-Number(b.synthetic)||b.run_id.localeCompare(a.run_id)).forEach(x=>{const o=add('option',x.run_id,byId('run'));o.value=x.run_id});if(r.length)show();else byId('name').textContent='No completed evidence runs'}).catch(e=>{byId('error').hidden=false;byId('error').textContent=e.message});



function updateView(){const mode=byId('view').value;byId('map').style.display=mode==='map'?'':'none';byId('sar-preview').hidden=mode==='map';const optical=opticalViews[mode];byId('optical-note').textContent=optical?optical.date+' · '+optical.description+(opticalViews.sharedGridMatch?' Preview linked by exact before/after Sentinel-1 file hashes.':''):'';if(mode!=='map'){byId('sar-preview').src=optical?optical.url:'/runs/'+encodeURIComponent(selected)+'/'+mode+'.png';byId('sar-preview').alt=optical?'Sentinel-2 RGB observation '+optical.date:'SAR VV observation';}}
async function presentRecord(m,r,frozen){
 opticalViews={};try{const index=await read('/assets/observations/index.json');const exactPair=[m.pre.sha256,m.post.sha256].join(':');const matched=Object.values(index).find(entry=>entry.sar_pair_sha256===exactPair&&entry['optical-pre']&&entry['optical-post']);const chosen=index[r.run_id]||matched||{};const sharedGridMatch=!!chosen.shared_grid_match||(!index[r.run_id]&&!!matched);opticalViews=Object.fromEntries(Object.entries(chosen).filter(([key])=>key.startsWith('optical-')));opticalViews.sharedGridMatch=sharedGridMatch;}catch(error){}
 for(const period of ['pre','post']){const mode='optical-'+period;const option=byId('view').querySelector('option[value="'+mode+'"]');option.disabled=!opticalViews[mode];option.textContent=(period==='pre'?'Before':'After')+' · optical RGB'+(opticalViews[mode]?' · '+opticalViews[mode].date:' · unavailable');}
 if(byId('view').selectedOptions[0].disabled)byId('view').value='map';
 const steps=[`Inputs: Sentinel-1 ${m.pre.datetime.slice(0,10)} / ${m.post.datetime.slice(0,10)}; relative orbit ${m.pre.relative_orbit}.`,`Preparation: aligned VV/VH dB observations; ${r.summary.valid_pixels.toLocaleString()} paired valid pixels.`,`Water candidates: post-event VV < ${r.analysis.water_db} dB and decrease ≥ ${r.analysis.drop_db} dB.`,m.debris?`Debris proxy: optical ${m.debris.pre_date} / ${m.debris.post_date}; vegetation loss and SAR change. Unvalidated.`:'Debris: not assessed in this run.',`Infrastructure: historical OSM snapshot ${m.osm_snapshot.slice(0,10)}; geometry intersections.`,frozen.files['topology-audit.json']?'Access: historical-node graph comparison; missing coverage and boundary uncertainty retained.':'Access: no historical topology audit for this run.',`Evidence: ${Object.keys(frozen.files).length} files recorded in the frozen hash manifest.`];
 byId('processing-steps').replaceChildren();steps.forEach(step=>add('li',step,byId('processing-steps')));
}
byId('view').addEventListener('change',updateView);

const answerFields={new_water_m2:['New-water candidate area','m²'],new_water_pixels:['Candidate pixels',''],exposed_buildings:['Intersected buildings',''],exposed_road_m:['Intersected roads / bridges','m'],exposed_bridge_features:['Bridge features',''],potentially_cut_off:['Potentially cut-off settlements','']};
function focusAnswer(){const panel=byId('analysis-result');panel.scrollIntoView({block:'nearest',behavior:'auto'});panel.focus({preventScroll:true});}
byId('copilot-form').addEventListener('submit',async e=>{
 e.preventDefault();const button=e.target.querySelector('button'),request=++answerRequest,runId=selected;button.disabled=true;
 byId('analysis-result').hidden=false;byId('answer-heading').textContent='Reading saved evidence…';byId('answer-run').textContent='Run: '+runId;byId('copilot-answer').textContent='';byId('copilot-sources').replaceChildren();byId('answer-metrics').replaceChildren();focusAnswer();
 try{
 const r=await fetch('/api/copilot',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_id:runId,question:byId('copilot-question').value,language:byId('copilot-language').value,topic:byId('copilot-topic').value})});const d=await r.json();if(request!==answerRequest)return;if(!r.ok)throw Error(d.detail||'Answer unavailable');
 byId('answer-heading').textContent=({water:'New-water candidates',buildings:'Building exposure',roads:'Road and bridge exposure',connectivity:'Settlement access',summary:'Flood impact summary',limitations:'What this run can establish'})[d.intent]||'Analysis result';byId('copilot-answer').textContent=d.answer;
 for(const c of d.citations){const key=c.pointer.split('/').pop(),field=answerFields[key];if(!field)continue;const card=add('div','',byId('answer-metrics'));card.className='answer-metric';const number=typeof c.value==='number'?c.value.toLocaleString(undefined,{maximumFractionDigits:key==='exposed_road_m'?2:0}):String(c.value);add('strong',number+(field[1]?' '+field[1]:''),card);add('span',field[0],card);}
 add('p','Selected topic: '+d.intent+'. Check or change the topic if the question was misunderstood.',byId('copilot-sources'));
 for(const c of d.citations){const a=add('a','Source: '+(answerFields[c.pointer.split('/').pop()]?.[0]||c.pointer),byId('copilot-sources'));a.href='/runs/'+encodeURIComponent(runId)+'/'+c.file;a.target='_blank';}
 focusAnswer();
 }catch(err){if(request===answerRequest){byId('answer-heading').textContent='Answer unavailable';byId('copilot-answer').textContent=err.message;}}
 finally{button.disabled=false;}
});

let eventTimer=null,eventStartedAt=null;
function updateElapsed(){if(!eventStartedAt)return;const seconds=Math.max(0,Math.floor((Date.now()-eventStartedAt)/1000));byId('event-elapsed').textContent=seconds<60?seconds+' s':Math.floor(seconds/60)+' min '+String(seconds%60).padStart(2,'0')+' s';}
function renderEventProgress(d){
 const card=byId('event-progress');card.hidden=false;card.dataset.state=d.state;
 byId('event-status').textContent=d.message;
 byId('event-progress-title').textContent=({queued:'Waiting to begin flood analysis',running:'Flood event analysis in progress',complete:'Flood analysis complete',failed:'Flood analysis stopped',interrupted:'Flood analysis interrupted'})[d.state]||'Flood event analysis';
 const parsed=Date.parse(d.created_at||'');if(Number.isFinite(parsed))eventStartedAt=parsed;
 updateElapsed();if(eventTimer)clearInterval(eventTimer);eventTimer=['queued','running'].includes(d.state)?setInterval(updateElapsed,1000):null;
 const events=Array.isArray(d.events)&&d.events.length?d.events:[{state:d.state,message:d.message,at:d.updated_at}];const list=byId('event-steps');list.replaceChildren();
 events.forEach((item,index)=>{const row=add('li','',list);row.dataset.state=index<events.length-1&&item.state==='running'?'complete':(item.state||'running');if(index===events.length-1)row.classList.add('current');add('span',item.message,row).className='event-step-message';if(item.at){const time=Date.parse(item.at);if(Number.isFinite(time))add('time',new Date(time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'}),row);}});
}
async function watchEvent(job){
 const button=byId('event-form').querySelector('button');button.disabled=true;byId('event-progress').hidden=false;
 try{
  const d=await read('/api/event-jobs/'+encodeURIComponent(job));renderEventProgress(d);
  if(['queued','running'].includes(d.state)){setTimeout(()=>watchEvent(job),2500);return;}
  localStorage.removeItem('flood-active-job');button.disabled=false;
  if(d.state==='complete'){
   if(![...byId('run').options].some(o=>o.value===d.run_id)){const o=add('option',d.run_id,byId('run'));o.value=d.run_id;}
   byId('run').value=d.run_id;await show();
  }
 }catch(error){byId('event-status').textContent='Unable to check progress. Reload to reconnect. '+error.message;button.disabled=false;}
}
byId('event-form').addEventListener('submit',async event=>{
 event.preventDefault();const button=event.target.querySelector('button');button.disabled=true;
 try{
  const parts=byId('event-bbox').value.split(',').map(x=>x.trim());const bbox=parts.map(Number);
  if(parts.length!==4||parts.some(x=>!x)||!bbox.every(Number.isFinite))throw Error('Enter four coordinates separated by commas.');
  const r=await fetch('/api/event-jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bbox,event_date:byId('event-date').value})});const d=await r.json();
  if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:'Check the area bounds and event date.');
  localStorage.setItem('flood-active-job',d.job_id);renderEventProgress(d);watchEvent(d.job_id);
 }catch(error){byId('event-status').textContent=error.message;button.disabled=false;}
});
const pendingJob=localStorage.getItem('flood-active-job');if(pendingJob)watchEvent(pendingJob);


// Full-screen inspection for the map and the selected SAR/optical preview.
(()=>{
 const dialog=byId('image-viewer'),stage=byId('viewer-stage'),level=byId('viewer-zoom-level');
 let scale=1,offset={x:0,y:0},drag=null,returnFocus=null;
 const clamp=value=>Math.min(8,Math.max(.25,value));
 function paint(){const image=stage.querySelector('#viewer-image');if(image)image.style.transform=`translate(${offset.x}px,${offset.y}px) scale(${scale})`;level.value=`${Math.round(scale*100)}%`;level.textContent=level.value;}
 function zoom(next,anchor={x:0,y:0}){const target=clamp(next),ratio=target/scale;offset={x:anchor.x-(anchor.x-offset.x)*ratio,y:anchor.y-(anchor.y-offset.y)*ratio};scale=target;paint();}
 function fit(){scale=1;offset={x:0,y:0};paint();}
 function open(source,label){
  returnFocus=source;stage.replaceChildren();const image=source.cloneNode(true);image.id='viewer-image';image.removeAttribute('hidden');image.removeAttribute('tabindex');image.removeAttribute('role');
  if(image.tagName.toLowerCase()==='svg'){image.setAttribute('role','img');image.setAttribute('aria-label',label);image.setAttribute('preserveAspectRatio','xMidYMid meet');}
  else{image.alt=label;}
  image.style.transform='';stage.append(image);dialog.setAttribute('aria-label',label);fit();dialog.showModal();byId('viewer-fit').focus();
 }
 const map=byId('map'),preview=byId('sar-preview');
 function bind(source,getLabel){source.addEventListener('click',()=>open(source,getLabel()));source.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();open(source,getLabel());}});}
 bind(map,()=>byId('name').textContent+' flood impact map');bind(preview,()=>preview.alt||'Satellite image');
 byId('viewer-fit').addEventListener('click',fit);
 byId('viewer-zoom-in').addEventListener('click',()=>zoom(scale*1.25));
 byId('viewer-zoom-out').addEventListener('click',()=>zoom(scale/1.25));
 byId('viewer-close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('close',()=>{stage.replaceChildren();if(returnFocus?.isConnected)returnFocus.focus();returnFocus=null;});
 dialog.addEventListener('keydown',event=>{if(event.key==='+'||event.key==='='){event.preventDefault();zoom(scale*1.25);}else if(event.key==='-'){event.preventDefault();zoom(scale/1.25);}else if(event.key==='0'){event.preventDefault();fit();}});
 stage.addEventListener('wheel',event=>{event.preventDefault();const rect=stage.getBoundingClientRect();zoom(scale*(event.deltaY<0?1.2:1/1.2),{x:event.clientX-rect.left-rect.width/2,y:event.clientY-rect.top-rect.height/2});},{passive:false});
 stage.addEventListener('pointerdown',event=>{if(event.target.closest('#viewer-image')){drag={id:event.pointerId,x:event.clientX,y:event.clientY,offset:{...offset}};stage.setPointerCapture(event.pointerId);}});
 stage.addEventListener('pointermove',event=>{if(drag?.id===event.pointerId){offset={x:drag.offset.x+event.clientX-drag.x,y:drag.offset.y+event.clientY-drag.y};paint();}});
 const stop=event=>{if(drag?.id===event.pointerId)drag=null;};stage.addEventListener('pointerup',stop);stage.addEventListener('pointercancel',stop);
})();
