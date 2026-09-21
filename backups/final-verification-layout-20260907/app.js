const $=id=>document.getElementById(id);
let image=null,busy=false,currentRun=null,scale=1,offset={x:0,y:0},pointer=null;
let theme=localStorage.getItem('satquery-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
function setTheme(){document.documentElement.dataset.theme=theme;$('theme').textContent=theme==='dark'?'☀':'☾';$('theme').setAttribute('aria-label',`Switch to ${theme==='dark'?'light':'dark'} mode`);localStorage.setItem('satquery-theme',theme)}setTheme();$('theme').onclick=()=>{theme=theme==='dark'?'light':'dark';setTheme()};
async function api(url,options){const r=await fetch(url,options);const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:d.detail?.reason||'The request could not be completed.');return d}
function feedback(message=''){$('feedback').textContent=message;$('feedback').hidden=!message}
function controls(){if($('scene-sample')){$('scene-sample').disabled=busy;$('scene-sample').hidden=!!image;}if($('ndvi-threshold'))$('ndvi-threshold').disabled=busy;$('analyze').disabled=busy||!image||!$('question').value.trim();$('replace').disabled=busy;$('choose').disabled=busy;$('sample').disabled=busy;$('question').disabled=busy;$('mode').disabled=busy;document.querySelectorAll('.suggestion').forEach(b=>b.disabled=busy)}
async function status(){try{const s=await api('/api/status');$('status').textContent=`Local model · ${s.state==='processing'?'Processing':s.state==='ready'?'Ready':'Loads on first run'}`}catch{$('status').textContent='Local server · Offline'}}status();setInterval(status,5000);
$('question').oninput=()=>{$('counter').textContent=`${$('question').value.length}/500`;controls()};
for(const id of ['choose','replace'])$(id).onclick=()=>$('file').click();$('file').onchange=()=>{if($('file').files[0])upload($('file').files[0]);$('file').value=''};
async function upload(file){if(busy)return;if(file.size>20*1024*1024)return feedback('Please choose an image smaller than 20 MB.');busy=true;controls();feedback();try{const form=new FormData();form.append('file',file);const next=await api('/api/images',{method:'POST',body:form});image=next;clearEvidence();$('geo-info').textContent=next.geo ? [next.geo.crs||'No CRS',next.geo.resolution.join(' × ')+' CRS units/pixel',next.geo.acquired||'Date unavailable','Bands: '+Object.keys(next.geo.bands).join(', ')].join(' · ') : 'RGB image: spectral measurements unavailable';$('satellite').src=next.preview;$('satellite').hidden=false;$('empty').hidden=true;$('image-tools').hidden=false;$('zoom-label').hidden=false;$('replace').hidden=false;$('filename').textContent=next.name;$('fileinfo').textContent=`${next.width} × ${next.height} px · ${(next.bytes/1024/1024).toFixed(2)} MB`;$('idle-state').hidden=false;$('answer-state').hidden=true;currentRun=null;$('details').open=false;$('trace').replaceChildren();reset()}catch(e){feedback(e.message)}finally{busy=false;controls()}}
$('sample').onclick=async()=>{try{const r=await fetch('/api/sample');if(!r.ok)throw Error('Sample image is unavailable.');await upload(new File([await r.blob()],'sample-baseball-fields.png',{type:'image/png'}))}catch(e){feedback(e.message)}};
const viewport=$('viewport');viewport.ondragover=e=>{e.preventDefault();if(!busy)viewport.classList.add('dragover')};viewport.ondragleave=()=>viewport.classList.remove('dragover');viewport.ondrop=e=>{e.preventDefault();viewport.classList.remove('dragover');if(e.dataTransfer.files[0])upload(e.dataTransfer.files[0])};
function transform(){if($('ndvi-overlay'))$('ndvi-overlay').style.transform=`translate(${offset.x}px,${offset.y}px) scale(${scale})`;$('satellite').style.transform=`translate(${offset.x}px,${offset.y}px) scale(${scale})`;$('zoom-label').textContent=`${Math.round(scale*100)}%`}
function reset(){scale=1;offset={x:0,y:0};transform()}$('reset').onclick=reset;$('zoom-in').onclick=()=>{scale=Math.min(5,scale+.25);transform()};$('zoom-out').onclick=()=>{scale=Math.max(1,scale-.25);if(scale===1)offset={x:0,y:0};transform()};
$('satellite').onpointerdown=e=>{pointer={x:e.clientX-offset.x,y:e.clientY-offset.y};e.target.setPointerCapture(e.pointerId)};$('satellite').onpointermove=e=>{if(pointer&&scale>1){offset={x:e.clientX-pointer.x,y:e.clientY-pointer.y};transform()}};$('satellite').onpointerup=$('satellite').onpointercancel=()=>pointer=null;
document.querySelectorAll('.suggestion').forEach(b=>b.onclick=()=>{$('question').value=b.dataset.question;$('question').oninput();$('question').focus()});
function showTrace(run){if(run.statistics){$('trace').replaceChildren();for(const [key,value]of Object.entries(run.statistics)){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=key.replaceAll('_',' ');dd.textContent=typeof value==='object'?JSON.stringify(value):value;$('trace').append(dt,dd)}return;}const items=[['Task',run.route],['Model',run.model],['Revision',run.revision],['Adapter',run.adapter||'None — baseline'],['Image hash',run.image.sha256],['Generation',`${run.generation_seconds??'—'} s`],['GPU allocated',`${run.peak_allocated_GiB??'—'} GiB`],['Run ID',run.id]];$('trace').replaceChildren();for(const [key,value]of items){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=key;dd.textContent=typeof value==='object'?JSON.stringify(value):value;$('trace').append(dt,dd)}}
$('question-form').onsubmit=async e=>{e.preventDefault();if(busy||!image)return;busy=true;currentRun=null;controls();feedback();$('idle-state').hidden=true;$('answer-state').hidden=true;$('loading').hidden=false;$('stage').textContent='Preparing image';$('elapsed').textContent='Elapsed: 0 s';$('status').textContent='Local model · Processing';$('trace').replaceChildren();const start=Date.now();const timer=setInterval(()=>$('elapsed').textContent=`Elapsed: ${Math.floor((Date.now()-start)/1000)} s`,250);try{const form=new FormData();form.append('image_id',image.id);form.append('question',$('question').value.trim());form.append('mode',$('mode').value);form.append('threshold',$('ndvi-threshold').value);clearEvidence();const job=await api('/api/analyze',{method:'POST',body:form});for(;;){const run=await api(`/api/runs/${job.id}`);$('stage').textContent=run.stage;if(run.state==='error')throw Error(run.error);if(run.state==='complete'){currentRun=run;showStages(run);$('route-reason').textContent=run.routing?.reason||run.route;if(run.overlay){$('ndvi-overlay').src=run.overlay;$('ndvi-overlay').hidden=false;$('evidence-controls').hidden=false;$('raster-download').href=run.raster;}showAnswer(run);$('answer-time').textContent=`${run.seconds.toFixed(2)} s total · ${run.statistics?'Measured NDVI · CPU':run.adapter?'Experimental adapter':'Original model'}`;$('answer-state').hidden=false;showTrace(run);break}await new Promise(r=>setTimeout(r,450))}}catch(e){feedback(e.message);$('idle-state').hidden=false}finally{clearInterval(timer);$('loading').hidden=true;busy=false;controls();status()}};
$('download').onclick=()=>{if(!currentRun)return;const url=URL.createObjectURL(new Blob([JSON.stringify(currentRun,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`satquery-run-${currentRun.id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
document.querySelectorAll('.nav').forEach(b=>b.onclick=()=>{document.querySelectorAll('.nav').forEach(n=>n.classList.toggle('active',n===b));$('explore').hidden=b.dataset.view!=='explore';$('evaluation').hidden=b.dataset.view!=='evaluation';if(b.dataset.view==='evaluation'){loadEvaluation();loadDevelopment()}});
async function loadEvaluation(){try{const s=await api('/api/evaluation');$('diagnostic-score').textContent=`Original: ${s.correct}/${s.total} (${(100*s.correct/s.total).toFixed(1)}%). Adapter: not evaluated on this run.`;}catch(e){$('diagnostic-score').textContent=e.message}}
function cell(value,tag='td'){const el=document.createElement(tag);el.textContent=value;return el}
async function loadDevelopment(){try{const d=await api('/api/development');
$('dev-context').textContent=`${d.questions} questions | ${d.images} images | ${d.source_scenes} development source scene | ${d.run}`;
const b=d.baseline_dev,a=d.adapted_dev;
$('base-score').textContent=`${(100*b.correct/b.total).toFixed(1)}%`;
$('adapter-score').textContent=`${(100*a.correct/a.total).toFixed(1)}%`;
$('base-count').textContent=`${b.correct}/${b.total} correct`;$('adapter-count').textContent=`${a.correct}/${a.total} correct`;
$('dev-score').textContent=`+${(100*(a.correct/a.total-b.correct/b.total)).toFixed(1)} percentage points | ${d.gains} gains | ${d.regressions.length} regressions`;
$('dev-rows').replaceChildren();
for(const [key,label] of [['rural_urban','Rural / urban'],['presence','Presence'],['comp','Comparison']]){const tr=document.createElement('tr');tr.append(cell(label,'th'));for(const m of [b,a]){const v=m.per_category[key];tr.append(cell(`${v.correct}/${v.total} | ${(100*v.correct/v.total).toFixed(1)}%`))}$('dev-rows').append(tr)}
const format=document.createElement('tr');format.append(cell('Format failures (lower is better)','th'),cell(b.invalid_format),cell(a.invalid_format));$('dev-rows').append(format);
$('majority').textContent=`Category-majority reference: ${d.majority_correct}/${d.questions} (${(100*d.majority_correct/d.questions).toFixed(1)}%). Labels are imbalanced; scores include answer-format compliance.`;
$('regressions').replaceChildren();for(const r of d.regressions){const tr=document.createElement('tr');tr.append(cell(r.question),cell(r.reference),cell(r.original),cell(r.adapter));$('regressions').append(tr)}
$('protocol').textContent=`Both models: ${d.protocol.visual_tokens} visual tokens, ${d.protocol.max_new_tokens} output tokens, deterministic decoding. ${d.protocol.scoring}`;
$('evidence-links').replaceChildren();for(const [key,v] of Object.entries(d.evidence)){const a=document.createElement('a');a.href=v.url;a.textContent=key.replaceAll('-',' ');a.title=`SHA-256: ${v.sha256}`;$('evidence-links').append(a)}
}catch(e){$('dev-score').textContent=e.message;for(const id of ['base-score','adapter-score','base-count','adapter-count'])$(id).textContent='Unavailable';$('dev-rows').replaceChildren();$('regressions').replaceChildren();$('evidence-links').replaceChildren();}}
function showStages(run){$('processing-stages').hidden=!run.statistics;$('stage-error').textContent=run.processing_stages_error||'';$('stage-grid').replaceChildren();for(const [key,label] of [['rgb','RGB'],['false-colour','False colour - NIR / Red / Green'],['evidence','NDVI evidence overlay'],['mask','Binary mask']]){if(!run.processing_stages?.[key])continue;const fig=document.createElement('figure'),a=document.createElement('a'),img=document.createElement('img'),caption=document.createElement('figcaption');a.href=run.processing_stages[key];a.target='_blank';a.rel='noopener';a.onclick=e=>{e.preventDefault();openImage(a.href,label)};img.src=a.href;img.alt=label;img.onerror=()=>{$('stage-error').textContent='A processing view failed to load. Check the saved analytical exports.'};caption.textContent=label;a.append(img);fig.append(a,caption);$('stage-grid').append(fig)}$('stage-context').textContent=run.statistics?`${run.image.name} | NDVI >= ${run.threshold.toFixed(2)} | white = selected, black = unselected, transparent = invalid. False colour uses a display-only stretch.`:''}

// Multispectral controls use the same image geometry and pan/zoom transform.
const geoInfo=document.createElement('p');geoInfo.id='geo-info';geoInfo.className='geo-info';$('viewport').parentElement.append(geoInfo);
const overlay=document.createElement('img');overlay.id='ndvi-overlay';overlay.alt='Pixels meeting the selected NDVI threshold';overlay.hidden=true;$('viewport').append(overlay);
const geoTools=document.createElement('div');geoTools.className='geo-tools';
geoTools.innerHTML='<button type="button" id="scene-sample">Load Dehradun multispectral sample</button><label>NDVI threshold <input id="ndvi-threshold" type="number" min="-1" max="1" step="0.05" value="0.5"></label><div id="evidence-controls" hidden><label><input type="checkbox" id="overlay-toggle" checked> Show NDVI evidence</label><a id="raster-download">Download NDVI GeoTIFF</a></div>';
$('question-form').before(geoTools);$('empty').append($('scene-sample'));$('scene-sample').className='text-button';
$('overlay-toggle').onchange=()=>{$('ndvi-overlay').hidden=!$('overlay-toggle').checked};
function clearEvidence(){$('processing-stages').hidden=true;$('stage-grid').replaceChildren();$('stage-error').textContent='';$('ndvi-overlay').hidden=true;$('evidence-controls').hidden=true;$('overlay-toggle').checked=true}
$('scene-sample').onclick=async()=>{if(busy)return;try{const r=await fetch('/api/scene-sample');if(!r.ok)throw Error('Multispectral sample unavailable');await upload(new File([await r.blob()],'dehradun-sentinel2-20211125.tif',{type:'image/tiff'}));if(image?.geo?.ndvi_supported){$('mode').value='baseline';$('question').value='Calculate NDVI coverage at the selected threshold.';$('question').oninput()}}catch(e){feedback(e.message)}};

// Present measured quantities from the run; never ask the VLM to invent a calculation.
function showAnswer(run){
 const box=$('measurement-summary'),a=$('answer'),s=run.statistics;
 box.replaceChildren();box.hidden=!s;a.hidden=!!s;
 a.textContent=run.answer||'The model returned no answer.';
 if(!s)return;
 const fmt=(n,d=0)=>Number.isFinite(n)?n.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d}):'Unavailable';
 const add=(parent,tag,text,cls)=>{const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;parent.append(e);return e};
 add(box,'h3','Vegetation threshold coverage');
 const cards=add(box,'div','','measurement-cards');
 for(const [label,value] of [
  ['Coverage of valid pixels',fmt(s.selected_percent_of_valid,2)+'%'],
  ['Selected grid area',Number.isFinite(s.selected_area_m2)?fmt(s.selected_area_m2/10000,2)+' ha':'Unavailable'],
  ['Valid data coverage',fmt(s.valid_coverage_percent,2)+'%']]){
  const card=add(cards,'div','','measurement-card');add(card,'span',label);add(card,'strong',value);
 }
 add(box,'p',`Pixels meeting NDVI ≥ ${fmt(s.threshold,2)}. Threshold-based coverage, not a vegetation-health assessment.`,'measurement-note');
 const calc=add(box,'details','','measurement-calculation');add(calc,'summary','How this was calculated');
 const list=add(calc,'dl','','calculation-list');
 const row=(label,value)=>{add(list,'dt',label);add(list,'dd',value)};
 row('Per-pixel NDVI','(NIR − Red) ÷ (NIR + Red), using calibrated reflectance');
 row('Selection',`NDVI ≥ ${fmt(s.threshold,2)} among valid pixels → ${fmt(s.selected_pixels)} selected pixels`);
 row('Coverage of valid pixels',s.valid_pixels>0?`${fmt(s.selected_pixels)} ÷ ${fmt(s.valid_pixels)} × 100 = ${fmt(s.selected_percent_of_valid,2)}%`:'Unavailable: no valid pixels');
 row('Coverage of whole crop',`${fmt(s.selected_pixels)} ÷ ${fmt(s.total_pixels)} × 100 = ${fmt(s.selected_percent_of_crop,2)}%`);
 row('Valid data coverage',`${fmt(s.valid_pixels)} ÷ ${fmt(s.total_pixels)} × 100 = ${fmt(s.valid_coverage_percent,2)}%`);
 const t=run.image?.geo?.transform;
 const pixelArea=Number.isFinite(s.selected_area_m2)&&t?.length>=6?Math.abs(t[0]*t[4]-t[1]*t[3]):null;
 if(Number.isFinite(pixelArea)){
  row('Pixel grid area',`|a × e − b × d| from the affine transform = ${fmt(pixelArea,4)} m² per pixel`);
  row('Selected projected area',`${fmt(s.selected_pixels)} × ${fmt(pixelArea,4)} m² ÷ 10,000 = ${fmt(s.selected_area_m2/10000,2)} ha`);
 }else row('Selected projected area','Unavailable: a supported projected metre-based grid is required.');
 add(calc,'p',s.area_method||'Projected grid area, not terrain surface area.','measurement-note');
 const source=add(box,'details','','measurement-source');add(source,'summary','Source and limitations');
 const info=add(source,'dl','','calculation-list');
 for(const [label,value] of [['File',run.image?.name],['Acquired',run.image?.geo?.acquired||'Date unavailable'],['CRS',run.image?.geo?.crs||'Unavailable'],['Calibration',s.calibration_version],['Excluded pixels',fmt(s.excluded_pixels)],['Quality mask',s.quality_mask_available?s.quality_rule:'No quality mask available; cloud-free coverage is not established.']]){add(info,'dt',label);add(info,'dd',value||'Unavailable')}
 for(const [key,value] of Object.entries(s.exclusion_counts||{})){add(info,'dt',key.replaceAll('_',' '));add(info,'dd',fmt(value))}
 add(source,'p','Valid pixels passed the configured filters; this does not prove that all clouds or other artifacts were removed. '+(s.interpretation||''),'measurement-note');
}

function openImage(src,label){$('full-image').src=src;$('full-image').alt=label;$('image-viewer').showModal()}
$('close-viewer').onclick=()=>$('image-viewer').close();
const fullButton=document.createElement('button');fullButton.type='button';fullButton.textContent='⛶';fullButton.setAttribute('aria-label','Open image full screen');fullButton.onclick=()=>{if(image)openImage(currentRun?.processing_stages?.evidence&&!$('ndvi-overlay').hidden?currentRun.processing_stages.evidence:image.preview,image.name)};$('image-tools').append(fullButton);
let clickStart=null;
$('satellite').addEventListener('pointerdown',e=>{clickStart={x:e.clientX,y:e.clientY}});
$('satellite').addEventListener('click',e=>{if(image&&clickStart&&Math.hypot(e.clientX-clickStart.x,e.clientY-clickStart.y)<5)fullButton.click()});
