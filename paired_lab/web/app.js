'use strict';
const $=s=>document.querySelector(s);let samples=[],active=false;
const element=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n};
async function api(url,options){const r=await fetch(url,options);const j=await r.json();if(!r.ok){showSuggestions(j.detail?.suggested_queries||[]);throw Error(typeof j.detail==='string'?j.detail:j.detail?.message?[j.detail.message,...(j.detail.next_steps||[]).map(x=>'Next step: '+x)].join('\n\n'):Array.isArray(j.detail)?'Check the required input fields and try again.':JSON.stringify(j.detail||'Request failed'))}return j}
function feedback(text){$('#feedback').hidden=!text;$('#feedback').textContent=text}
function views(items){
 $('#empty').hidden=true;const root=$('#views');root.hidden=false;root.replaceChildren();
 const hero=element('button');hero.type='button';hero.className='hero-view';hero.setAttribute('aria-label','Open selected image full size');
 const image=element('img'),caption=element('p');hero.append(image);const strip=element('div');strip.className='stage-strip';strip.setAttribute('aria-label','Analysis images');
 const pick=(name,url,button)=>{image.src=url;image.alt=name;caption.textContent=name;strip.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===button)));hero.onclick=()=>{$('#full').src=url;$('#full').alt=name;$('#viewer').showModal()}};
 for(const [name,url] of items){const button=element('button');button.type='button';button.setAttribute('aria-label',name);const thumb=element('img');thumb.src=url;thumb.alt='';button.append(thumb,element('span',name));button.onclick=()=>pick(name,url,button);strip.append(button)}
 root.append(hero,caption,strip);if(items.length)pick(...items[0],strip.firstChild);
}
function metric(container,label,value){const card=element('div');card.className='metric-card';card.append(element('strong',value),element('span',label));container.append(card)}
function selectSample(){const s=samples.find(s=>s.id===$('#sample').value);const single=$('#sample').value==='single';const demo=$('#sample').value.startsWith('demo-');$('#single-fields').hidden=!single;$('#upload-fields').hidden=!!s||single||demo;$('#execution').hidden=true;if(single)$('#question').value='Describe this image.';if($('#sample').value==='')$('#question').value='What changed between these two dates, and where?';if(demo)$('#question').value={'demo-vqa':'Describe this image.','demo-ndvi':'Calculate NDVI','demo-grounding':'Outline the stadium'}[$('#sample').value];$('#result').hidden=true;feedback('');if(s){$('#question').value=s.kind==='temporal'?'What changed between these two dates, and where?':s.kind==='water_map'?'Map water using the optical and SAR images together.':'Use the optical and SAR images together to identify land-cover classes.';const files=s.kind==='temporal'?['before.png','after.png']:['optical.png','sar.png'];views(files.map((f,i)=>[s.kind==='temporal'?['Before','After'][i]:['Optical preview','SAR preview'][i],`/api/preview/${s.id}/${f}`]));$('#visual-note').textContent=s.source+' · '+s.benchmark}else{$('#views').hidden=true;$('#empty').hidden=false;$('#visual-note').textContent='Upload an optical image or compatible pair. Processing runs locally.'}}
function table(headers,rows){const t=element('table'),head=element('tr');headers.forEach(h=>head.append(element('th',h)));t.append(head);rows.forEach(row=>{const tr=element('tr');row.forEach(v=>tr.append(element('td',v)));t.append(tr)});return t}
function showResult(r){
 $('#result').hidden=false;$('#loading-art').hidden=true;$('#answer').textContent=r.answer;$('#metrics').replaceChildren();metric($('#metrics'),'Specialist execution',`${r.seconds.toFixed(2)} s`);metric($('#metrics'),'Compute',r.execution?.device||'Local');$('#scores').replaceChildren();
 const url=f=>`/api/runs/${r.id}/${f}`;
 if(r.task==='spectral_pair'){
  const items=[['Overview: before / after / change',url('comparison.png')]];
  for(const [key,label] of [['vegetation','Vegetation · NDVI'],['water','Water candidates · NDWI'],['built_up','Built-up expansion']]){
   const v=r.parameters[key];if(!v)continue;const card=element('section');card.className='parameter-result';card.append(element('h3',label));
   if(v.status!=='complete'){card.append(element('p','Unavailable: '+v.reason));$('#scores').append(card);continue}
   const metrics=element('div');metrics.className='metrics';metric(metrics,'Before → after selected pixels',v.before_pixels.toLocaleString()+' → '+v.after_pixels.toLocaleString());metric(metrics,'Net threshold coverage change',v.net_percentage_points.toFixed(2)+' pp');metric(metrics,'Gained / lost pixels',v.gain_pixels.toLocaleString()+' / '+v.loss_pixels.toLocaleString());metric(metrics,'Common valid pixels',v.valid_pixels.toLocaleString());card.append(metrics,element('p','Threshold ≥ '+v.threshold+'; index-based candidates, not verified land-cover conversion.'));
   const button=element('button','Compare '+label+' dates');button.type='button';button.className='parameter-view';button.onclick=()=>views([[label+' - before / after / change',url(key+'-comparison.png')],...items.filter(item=>item[1]!==url(key+'-comparison.png'))]);card.append(button);const detail=element('details');detail.append(element('summary','Calculation and parameters'),element('pre',JSON.stringify(v,null,2)));card.append(detail);$('#scores').append(card);items.push([label+' - before / after / change',url(key+'-comparison.png')]);items.push([label+' - change only',url(key+'-change.png')]);
  }
  for(const preview of r.source_previews||[])items.push([preview.label,url(preview.file)]);
  views(items);$('#scores').prepend(element('p',r.dates.join(' → ')));
 }else if(r.task==='temporal'){
  metric($('#metrics'),'Predicted changed pixels',r.changed_pixels.toLocaleString());metric($('#metrics'),'Analyzed pixels',r.denominator_pixels.toLocaleString());
  views([['Change overlay','overlay.png'],['Road change: cyan · building change: gold','change-mask.png'],['Before','before.png'],['After','after.png']].map(([n,f])=>[n,url(f)]));
  $('#scores').append(element('p','Caption: model interpretation. Pixel totals are calculated from the predicted masks.'),table(['Changed class','Pixels'],Object.entries(r.class_pixels||{})));
 }else if(r.task==='water_map'){
  views([['Water overlay','water-overlay.png'],['Joint water mask','all-water.png'],['SAR-only water','s1-water.png'],['Optical-only water','s2-water.png'],['Optical','optical.png'],['SAR display','sar.png']].map(([n,f])=>[n,url(f)]));
  metric($('#metrics'),'Joint water pixels',r.water_pixels.all.toLocaleString());metric($('#metrics'),'Joint valid-pixel coverage',(100*r.water_pixels.all/r.denominator_pixels).toFixed(2)+'%');$('#scores').append(table(['Inputs','Predicted water pixels','Valid-pixel coverage'],['s1','s2','all'].map(k=>[{s1:'SAR only',s2:'Optical only',all:'Joint'}[k],r.water_pixels[k].toLocaleString(),(100*r.water_pixels[k]/r.denominator_pixels).toFixed(2)+'%'])),element('p',`Denominator: ${r.denominator_pixels.toLocaleString()} common finite pixels of ${r.full_image_pixels.toLocaleString()} full-image pixels.`));
 }else if(r.task==='grounding'){
  views([...(r.mode==='both'?[['Predicted outlines','outlines.png'],['Predicted instances','masks.png']]:[]),['Proposed boxes','boxes.png'],['RGB source','source.png']].map(([n,f])=>[n,url(f)]));
  metric($('#metrics'),'Object proposals',String(r.detections.length));$('#scores').append(element('p','Experimental grounding: proposals are not verified objects.'),table(['Object','Detector score','SAM predicted IoU'],r.detections.map(d=>[d.id,d.detector_score.toFixed(3),d.sam_predicted_iou?.toFixed(3)||'Not requested'])));
  if(r.mode==='both')$('#scores').append(element('p',`${r.union_mask_pixels.toLocaleString()} predicted union-mask pixels (${r.union_mask_percent.toFixed(2)}%); not ground area.`));
 }else if(r.task==='sar_scene'){views([['SAR display (not true colour)',url('sar.png')]]);$('#scores').append(table(['Land cover','Uncalibrated model score'],Object.entries(r.scores).sort((a,b)=>b[1]-a[1]).map(([k,v])=>[k,(100*v).toFixed(1)+'%'])));
 }else if(r.task==='vqa'){views([['Uploaded image',url('input-preview.png')]])}
 else if(r.task==='ndvi'){
  views([['NDVI overlay','evidence.png'],['Threshold mask','mask.png'],['RGB','rgb.png'],['False colour','false-colour.png']].map(([n,f])=>[n,url(f)]));
  const s=r.statistics;metric($('#metrics'),'Selected valid pixels',s.selected_percent_of_valid.toFixed(2)+'%');metric($('#metrics'),'Selected grid area',s.selected_area_m2==null?'Unavailable':(s.selected_area_m2/10000).toFixed(2)+' ha');metric($('#metrics'),'Valid data',s.valid_coverage_percent.toFixed(2)+'%');metric($('#metrics'),'NDVI threshold','≥ '+s.threshold.toFixed(2));const details=element('details');details.append(element('summary','Calculation parameters'),element('pre',JSON.stringify(s,null,2)));$('#scores').append(details);
 }else{
  views([['Optical preview','optical.png'],['SAR preview','sar.png']].map(([n,f])=>[n,url(f)]));
  const names=Object.keys(r.scores.all).sort((a,b)=>r.scores.all[b]-r.scores.all[a]);$('#scores').append(element('p','Model scores — not measured accuracy'),table(['Land cover','SAR','Optical','Joint'],names.map(c=>[c,...['s1','s2','all'].map(k=>(r.scores[k][c]*100).toFixed(1)+'%')])));
 }
 $('#visual-note').textContent='Final output shown first. Select a thumbnail to inspect a processing image; click the large image to expand.';
 $('#download').href=url('evidence.zip');$('#json').href=url('result.json');$('#trace').textContent=JSON.stringify({controller:r.controller,checks:r.input_checks,confidence:r.confidence,tools:r.trace},null,2);$('#limits').replaceChildren(...r.limitations.map(x=>element('li',x)));
}
function showExecution(plan,stage,events=[]){
 $('#execution').hidden=false;$('#loading-art').hidden=!active||stage==='Complete'||stage.startsWith('Unable');$('#specialist').textContent=plan.specialist;
 $('#device').textContent=plan.device+(plan.maturity==='experimental'?' · EXPERIMENTAL':'');
 $('#route-reason').textContent=plan.reason;$('#current-stage').textContent=stage;
 $('#events').replaceChildren(...events.map(e=>element('li',e.stage)));
}
function lockForm(locked){document.querySelectorAll('.picker-toggle').forEach(n=>n.disabled=locked);$('#form').querySelectorAll('input,select,textarea,button').forEach(n=>n.disabled=locked)}
$('#form').onsubmit=async ev=>{
 ev.preventDefault();if(active)return;showSuggestions([]);active=true;lockForm(true);$('#result').hidden=true;$('#execution').hidden=true;
 const start=Date.now();let chosen;
 try{
  const payload={query:$('#question').value};const choice=$('#sample').value;
  if(choice==='single'||choice.startsWith('demo-')){
   let file=$('#single-file').files[0];
   if(choice.startsWith('demo-')){const response=await fetch('/api/single-sample/'+choice.slice(5));if(!response.ok)throw Error('Example unavailable');file=new File([await response.blob()],choice==='demo-ndvi'?'calibrated-scene.tif':'optical-example.png');}
   if(!file)throw Error('Choose an optical image.');
   const body=new FormData();body.append('file',file);body.append('modality',choice.startsWith('demo-')?'optical':$('#single-modality').value);feedback('Checking the image…');
   const image=await api('/api/single-images',{method:'POST',body});payload.images=[image.id];payload.threshold=Number($('#threshold').value);
   views([['Input preview',image.preview='/api/single-images/'+image.id]]);
  }else if(choice)payload.sample=choice;
  else{
   payload.images=[];payload.threshold=Number($('#pair-ndvi').value);payload.water_threshold=Number($('#pair-ndwi').value);
   for(const suffix of ['a','b']){
    const file=$(`#file-${suffix}`).files[0];if(!file)throw Error('Choose both TIFF files.');
    const body=new FormData();body.append('file',file);body.append('modality',$(`#mode-${suffix}`).value);body.append('date',$(`#date-${suffix}`).value);
    feedback('Checking uploaded image…');payload.images.push((await api('/api/images',{method:'POST',body})).id);
   }
  }
  feedback('Validating input compatibility and selecting the specialist…');
  const job=await api('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  chosen=job.plan;showExecution(chosen,'Input checks passed; starting specialist');
  while(Date.now()-start<900000){
   await new Promise(r=>setTimeout(r,400));const state=await api(`/api/jobs/${job.id}`);
   showExecution(state.plan||chosen,state.stage,state.events||[]);
   if(state.state==='complete'){showResult(state.result);feedback('Run complete. Evidence and original inputs are ready to download.');return;}
   if(state.state==='failed')throw Error(state.error);
   feedback(`${state.stage} · ${Math.round((Date.now()-start)/1000)} s`);
  }
  throw Error('Waiting timed out. The run may still be active; check the service before submitting again.');
 }catch(e){feedback(e.message);if(chosen)$('#current-stage').textContent='Unable to complete — '+e.message;}
 finally{active=false;lockForm(false);$('#loading-art').hidden=true;if(!$('#result').hidden)$('#result').scrollIntoView({behavior:'smooth',block:'nearest'})}
};
$('#sample').onchange=selectSample;$('#close').onclick=()=>$('#viewer').close();
function theme(t){document.documentElement.dataset.theme=t;localStorage.setItem('satquery-theme',t);$('#theme').textContent=t==='dark'?'☀':'☾'}
theme(localStorage.getItem('satquery-theme')||'dark');$('#theme').onclick=()=>theme(document.documentElement.dataset.theme==='dark'?'light':'dark');
function tab(evaluation){$('#lab').hidden=evaluation;$('#evaluation').hidden=!evaluation;$('#lab-tab').classList.toggle('active',!evaluation);$('#eval-tab').classList.toggle('active',evaluation)}$('#lab-tab').onclick=()=>tab(false);$('#eval-tab').onclick=()=>tab(true);
function aggregate(rows){const s=rows.reduce((a,m)=>({tp:a.tp+m.tp,fp:a.fp+m.fp,fn:a.fn+m.fn}),{tp:0,fp:0,fn:0});return {f1:2*s.tp/(2*s.tp+s.fp+s.fn),iou:s.tp/(s.tp+s.fp+s.fn)}}
async function boot(){try{const status=await api('/api/status');$('#status').textContent='Local workspace · '+status.state;samples=await api('/api/samples');for(const kind of ['temporal','optical_sar','water_map']){const group=element('optgroup');group.label=kind==='temporal'?'Temporal · paired optical examples':kind==='water_map'?'Water maps · Sen1Floods11':'Optical + SAR · BigEarthNet';for(const s of samples.filter(s=>s.kind===kind)){const o=element('option',s.name);o.value=s.id;group.append(o)}$('#sample').append(group)}$('#sample').value='single';selectSample();document.querySelectorAll('select').forEach(customPicker);const initial=new URLSearchParams(location.search).get('question');if(initial)$('#question').value=initial.slice(0,500);const e=await api('/api/evaluation'),container=$('#eval-content');container.append(element('p','Current cross-modal model: '+e.selected_model),...e.notes.map(n=>element('p',n)));const t=e.temporal.filter(r=>r.kind==='public-test-named-demo');const a=aggregate(t.map(r=>r.metrics));container.append(element('h3',`Archived ChangeFormer · ${t.length} development crops (not the active MCI model)`),element('p',`Pooled changed-pixel F1 ${(a.f1*100).toFixed(1)}%; IoU ${(a.iou*100).toFixed(1)}%. This measures these masks only.`),table(['Crop','Change IoU','F1','Seconds'],e.temporal.map(r=>[r.sample,r.kind==='same-image-control'?'N/A · '+r.metrics.fp+' false pixels':(r.metrics.iou*100).toFixed(1)+'%',r.kind==='same-image-control'?'N/A':(r.metrics.f1*100).toFixed(1)+'%',r.seconds.toFixed(2)])));container.append(element('h3','Optical–SAR · separate modalities versus joint model'),element('p','Fixed score threshold 0.5. Six validation and six test-labelled public fixtures, all from one Austrian scene. No geographic generalisation claim.'));const rows=[];for(const split of ['validation','test'])for(const kind of ['s1','s2','all']){const r=e.optical_sar.filter(r=>r.split===split);rows.push([split,{s1:'SAR only',s2:'Optical only',all:'Joint optical–SAR'}[kind],(aggregate(r.map(x=>x.metrics[kind])).f1*100).toFixed(1)+'%'])}container.append(table(['Public split','Model','Micro F1'],rows),element('p','The selected ResNet50 joint model beats its matching single-modality models on this small subset. This does not establish fusion superiority on new places or sensors. The earlier ResNet18 trial did not show a consistent joint advantage.'))}catch(e){feedback(e.message)}}boot();

async function resumedEvidence(){try{
 const e=await api('/api/resumed-evaluation'),c=$('#eval-content');
 c.prepend(element('h3','New evidence · temporal descriptions and water maps'));
 const block=element('div');const pct=x=>x==null?'N/A':(100*x).toFixed(2)+'%';
 if(e.water){block.append(element('h3','Water segmentation · same model, three input configurations'),element('p','Official 90-pair test and separate 15-pair Bolivia event holdout. Water F1 and IoU measure predicted pixels; they are not general VQA accuracy.'));
 const rows=[];for(const split of ['test','bolivia'])for(const mode of ['s1','s2','all']){const m=e.water[split].aggregate[mode];rows.push([split,{s1:'SAR only',s2:'Optical only',all:'Joint'}[mode],pct(m.water_f1),pct(m.water_iou)])}block.append(table(['Split','Inputs','Water F1','Water IoU'],rows),element('p','Fusion is not guaranteed to beat optical alone. All three results remain visible.'));}
 if(e.temporal){block.append(element('h3','Temporal · 100 labelled test pairs'),table(['Class','Pixel IoU'],[['Road change',pct(e.temporal.class_iou['1'])],['Building change',pct(e.temporal.class_iou['2'])]]),element('p',`Caption change/no-change agreement: ${e.temporal.caption_changeflag_agreement.correct}/100. This does not score every detail in a caption.`));}
 c.prepend(block);
}catch(e){feedback(e.message)}}resumedEvidence();

function customPicker(select){
 const wrapper=element('div');wrapper.className='picker';const toggle=element('button');toggle.type='button';toggle.className='picker-toggle';toggle.setAttribute('aria-haspopup','listbox');toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label',select.id==='sample'?'Example dataset':select.id==='single-modality'?'Input modality':select.id==='mode-a'?'First image modality':'Second image modality');const menu=element('div');menu.className='picker-menu';menu.id=select.id+'-choices';menu.setAttribute('role','listbox');menu.setAttribute('aria-label',toggle.getAttribute('aria-label'));menu.hidden=true;toggle.setAttribute('aria-controls',menu.id);
 const close=()=>{menu.hidden=true;toggle.setAttribute('aria-expanded','false')};
 const refresh=()=>{toggle.textContent=select.selectedOptions[0].textContent+' ▾';menu.querySelectorAll('button').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.value===select.value)))};
 for(const option of select.options){if(select.id==='sample'&&['','single'].includes(option.value))continue;const button=element('button',option.textContent);button.type='button';button.setAttribute('role','option');button.dataset.value=option.value;button.onclick=()=>{select.value=option.value;select.dispatchEvent(new Event('change'));refresh();close();toggle.focus()};menu.append(button)}
 toggle.onclick=()=>{menu.hidden=!menu.hidden;toggle.setAttribute('aria-expanded',String(!menu.hidden));if(!menu.hidden)menu.querySelector('[aria-selected=true]').focus()};wrapper.onkeydown=e=>{const options=[...menu.children];let i=options.indexOf(document.activeElement);if(e.key==='Escape'){close();toggle.focus()}if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)){e.preventDefault();menu.hidden=false;toggle.setAttribute('aria-expanded','true');i=e.key==='Home'?0:e.key==='End'?options.length-1:(i+(e.key==='ArrowDown'?1:-1)+options.length)%options.length;options[i].focus()}};
 document.addEventListener('click',e=>{if(!wrapper.contains(e.target))close()});select.hidden=true;select.after(wrapper);wrapper.append(toggle,menu);select.addEventListener('change',refresh);refresh();
}
function evidenceTab(detail){$('#eval-content').hidden=!detail;$('#evidence-overview').hidden=detail;$('#overview-tab').classList.toggle('active',!detail);$('#rigorous-tab').classList.toggle('active',detail)}
$('#overview-tab').onclick=()=>evidenceTab(false);$('#rigorous-tab').onclick=()=>evidenceTab(true);
async function highlights(){try{const e=await api('/api/resumed-evaluation'),c=$('#evidence-highlights');if(e.temporal){metric(c,'Temporal · labelled test pairs','100');metric(c,'Road change · pixel IoU',(100*e.temporal.class_iou['1']).toFixed(2)+'%');metric(c,'Building change · pixel IoU',(100*e.temporal.class_iou['2']).toFixed(2)+'%')}if(e.water){metric(c,'Water · official test pairs','90');metric(c,'Water · Bolivia holdout pairs','15');metric(c,'Joint water · test IoU',(100*e.water.test.aggregate.all.water_iou).toFixed(2)+'%')}}catch(e){$('#evidence-highlights').textContent='Evaluation evidence unavailable: '+e.message}}highlights();

async function singleEvidence(){
 const c=$('#eval-content'),cards=$('#evidence-highlights');
 try{const d=await api('/api/single-evaluation/development');const block=element('section');block.append(element('h3','VQA adaptation · development comparison'),element('p',`${d.questions} questions; ${d.images} images; ${d.source_scenes} development source scene. Not independent test accuracy.`));block.append(table(['Model','Correct','Format failures'],[['Original',d.baseline_dev.correct+'/'+d.baseline_dev.total,d.baseline_dev.invalid_format],['Adapted',d.adapted_dev.correct+'/'+d.adapted_dev.total,d.adapted_dev.invalid_format]]));block.append(table(['Category','Original','Adapted'],['rural_urban','presence','comp'].map(k=>[k,...[d.baseline_dev,d.adapted_dev].map(m=>m.per_category[k].correct+'/'+m.per_category[k].total)])));c.append(block);metric(cards,'VQA adapted · development only',d.adapted_dev.correct+'/'+d.adapted_dev.total);
 }catch(e){c.append(element('p','VQA development evidence unavailable: '+e.message))}
 try{const d=await api('/api/single-evaluation/reliability');const block=element('section');block.append(element('h3','Single-image verification · archived '+d.updated));for(const m of d.metrics){block.append(element('p',m.label+': '+m.value+' — '+m.note));if(m.label==='NDVI numerical checks')metric(cards,'NDVI numerical checks · archived',m.value)}block.append(table(['NDVI scene','Valid pixels','Selected %','Grid hectares'],d.ndvi_scenes.map(x=>[x.name,x.valid_pixels,x.percent.toFixed(2),x.hectares.toFixed(2)])),...d.notes.map(n=>element('p',n)),element('p','Archived routing checks apply to their recorded version; they do not certify the new unified controller. Grounding remains experimental; no broad grounding accuracy benchmark is established here.'));c.append(block)
 }catch(e){c.append(element('p','Archived single-image verification unavailable: '+e.message))}
}singleEvidence();

let ownInputMode='single',lastExample='demo-vqa';
function chooseSource(examples){
 if(active)return;
 if($('#own-controls').hidden)lastExample=$('#sample').value;
 $('#own-controls').hidden=examples;$('#example-controls').hidden=!examples;
 $('#own-mode').setAttribute('aria-pressed',String(!examples));$('#examples-mode').setAttribute('aria-pressed',String(examples));
 $('#sample').value=examples?lastExample:ownInputMode;$('#sample').dispatchEvent(new Event('change'));
}
$('#own-mode').onclick=()=>chooseSource(false);$('#examples-mode').onclick=()=>chooseSource(true);
for(const [id,value] of [['single-mode','single'],['pair-mode','']])$( '#'+id).onclick=()=>{if(active)return;ownInputMode=value;$('#single-mode').setAttribute('aria-pressed',String(value==='single'));$('#pair-mode').setAttribute('aria-pressed',String(value===''));chooseSource(false)};
