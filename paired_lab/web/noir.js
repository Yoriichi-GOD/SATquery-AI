/* Scientific Noir presentation. Uses existing APIs; never supplies scientific values. */
(() => {
  'use strict';
  const $ = s => document.querySelector(s), D = window.SQEvidence;
  if (!D || !$('#lab')) return;
  const make = (tag, text, cls) => {const n = document.createElement(tag); if (text != null) n.textContent = text; if (cls) n.className = cls; return n;};
  const A = '/assets/noir/';
  const css = make('link'); css.rel = 'stylesheet'; css.href = '/assets/noir.css?v=ea1e7f030eb6'; document.head.append(css);
  const brand = $('.brand'); brand.setAttribute('aria-label', 'SATquery AI · Workspace');
  brand.replaceChildren();
  const fullLogo = make('img'); fullLogo.src = A + 'saturn-brand-logo.png'; fullLogo.alt = 'SATquery AI — See a higher perspective'; fullLogo.className = 'sq-brand-full';
  const icon = make('img'); icon.src = A + 'saturn-brand-icon-only.png'; icon.alt = 'SATquery AI'; icon.className = 'sq-brand-icon';
  brand.append(fullLogo, icon);
  const galaxy = $('#empty img'); galaxy.src = A + 'floating-galaxy.png'; galaxy.alt = ''; galaxy.setAttribute('aria-hidden','true'); galaxy.className = 'sq-float';
  $('#loading-art').src = A + 'satellite-earth-execution.png'; $('#loading-art').alt = '';
  const skip = make('a','Skip to workspace','sq-skip'); skip.href='#main-content'; document.body.prepend(skip); $('main').id='main-content'; $('main').tabIndex=-1;
  $('header nav').setAttribute('aria-label','Main navigation');
  $('#theme').title = 'Switch light / Scientific Noir theme';
  const footer = $('footer'); footer.className = 'sq-footer'; footer.replaceChildren();
  const footerFields = {};
  for (const [key,label] of [['sources','Data sources'],['aoi','AOI bounds · WGS84'],['dates','Time basis'],['resolution','Resolution']]) {
    const item = make('div'), value = make('span'); item.append(make('small',label), value); footer.append(item); footerFields[key]=value;
  }
  const footerID = make('small', 'No run selected','sq-footer-id'); footer.append(footerID);
  let workspaceRecord = null, workspaceViews = [], earthMetadata = null, datasetMetadata = null, evidence = null, loading = false;
  const gridCache=new Map();
  let earthContextKey="";
  const jobs = new Map();
  const terminal = new Set(['complete','completed','failed','cancelled','abstained','interrupted','error','idle']);
  function route() {return $('#earth') && !$('#earth').hidden ? 'terrain' : $('#external') && !$('#external').hidden ? 'datasets' : !$('#evaluation').hidden ? 'evidence' : 'workspace';}
  function footerUpdate() {
    const current = route();
    const data = current === 'evidence' ? evidence?.footer : current === 'terrain' ? earthMetadata : current === 'workspace' ? workspaceRecord?.footer : datasetMetadata;
    for (const key of Object.keys(footerFields)) footerFields[key].textContent = data?.[key] || ({sources:'No source selected',aoi:'No AOI selected',dates:'—',resolution:'—'}[key]);
    footerID.textContent = data?.id || 'No run selected';
    footer.title = data?.id ? 'Selected source: ' + data.id : 'Choose an observation to populate metadata';
  }
  function execution(owner, value) {
    const old = jobs.get(owner), running = value && !terminal.has(value.state) && value.running !== false;
    let target = owner === 'terrain' ? $('#earth-question-form') : owner === 'datasets' ? $('#ext-state') : $('#execution');
    let scene = document.getElementById('sq-execution-' + owner);
    if (owner === 'workspace') { $('#loading-art').hidden = !running; }
    else if (running && target) {
      if (!scene) {
        scene=make('section',null,'sq-execution'); scene.id='sq-execution-'+owner; scene.setAttribute('role','status'); scene.setAttribute('aria-live','polite');
        const img=make('img'); img.src=A+'satellite-earth-execution.png';img.alt='';img.className='sq-float';scene.append(img,make('div'));target.after(scene);
      }
      const body=scene.lastElementChild;body.replaceChildren(make('span','EXECUTION EVENTS','eyebrow'),make('p',value.message || 'Analysis running'),make('small',value.id || 'Waiting for run identifier'));
      if (value.trace?.length) {const list=make('ol');for(const e of value.trace) list.append(make('li',e.tool || e.stage || e.state));body.append(list);}
      scene.hidden=false;
    } else if (scene) {scene.remove();}
    if (running) jobs.set(owner,value); else jobs.delete(owner);
    document.body.classList.toggle('sq-working',jobs.size>0);
    if (old?.id !== value?.id || old?.state !== value?.state) footerUpdate();
  }
  window.SQNoir = {
    views(items) {workspaceViews=items;},
    result(result) {workspaceRecord=D.workspace(result,workspaceViews);footerUpdate(); if(!$('#evaluation').hidden) refreshCatalog();},
    execution,
    context(run, scene, view='terrain', debris=null) {
      const contextKey=[run?.id,scene?.id,view].join(':');earthContextKey=contextKey;
      if(view==='terrain'&&scene){earthMetadata=D.terrain(scene).footer;footerUpdate();return;}
      const update=grid=>{
        earthMetadata=run?D.flood(run,grid).footer:scene?D.terrain(scene).footer:null;
        if(run&&['debris','both'].includes(view)&&debris?.debris_available){
          const p=debris.provenance||{};
          earthMetadata.sources=view==='both'?'Water candidates + debris proxy':'Saved debris / surface-change proxy';
          earthMetadata.dates=(view==='both'?'SAR '+earthMetadata.dates+' / Debris ':'')+[p.pre_date,p.post_date].map(D.date).join(' to ');
        }
        footerUpdate();
      };
      if(!run){update(null);return;}
      const id=run.id,cached=gridCache.get(id);update(cached||debris?.grid);
      if(!cached&&!gridCache.has(id)){
        gridCache.set(id,null);
        fetch('/api/flood/runs/'+encodeURIComponent(id)+'/grid',{cache:'no-store'}).then(r=>r.ok?r.json():null).then(grid=>{
          if(grid)gridCache.set(id,grid);
          if(earthContextKey===contextKey&&earthMetadata?.id===id&&grid)update(grid);
        }).catch(()=>{});
      }
    },
    dataset(dataset, files, lastJob) {
      datasetMetadata=dataset?{id:lastJob||dataset.id,sources:dataset.name||dataset.id,aoi:'See inspected input metadata',dates:'Not declared',resolution:'See input grid metadata'}:null;footerUpdate();
    },
    clearWorkspace() {workspaceRecord=null;footerUpdate();}
  };
  footerUpdate();

  // Keep the real saved benchmark presentation, below a new live-source inspector.
  const historical = $('#evaluation .evidence-card');
  historical.querySelector('.evaluation-art')?.remove();
  const archive = make('details', null, 'sq-archive'); archive.append(make('summary','Saved benchmark evaluations · methods, denominators & controls'),historical);
  const root = make('section',null,'sq-evidence'); root.id='sq-evidence';
  root.innerHTML = `<div class="intro sq-evidence-intro"><div><span class="eyebrow">02 / SOURCE → PRODUCT → INTERPRETATION</span><h1>Follow the evidence.</h1></div><p>Inspect the observation.<br>Keep the limits in view.</p></div>
    <div class="sq-evidence-grid"><aside class="sq-catalog"><span class="eyebrow">OBSERVATION CATALOGUE</span><h2>Selected sources.</h2><label for="sq-source-filter">Filter sources</label><input id="sq-source-filter" type="search" placeholder="Run, scene or population"><label for="sq-source">Run / scene</label><select id="sq-source"><option value="">No source selected</option></select><button id="sq-refresh">Refresh catalogue ↻</button><p id="sq-catalog-state" role="status">Open Evidence to load saved observations.</p><div id="sq-layer-controls"></div><p class="sq-muted">Only available products are listed. RGB, NDVI and confidence are absent when a run does not provide them.</p></aside>
    <section class="sq-stage-panel"><div class="sq-stage-heading"><div><span class="eyebrow">LAYER INVESTIGATION</span><h2 id="sq-stage-title">No layer selected</h2></div><button id="sq-fit">Fit view</button></div><div class="sq-stage-tools" role="group" aria-label="Evidence view"><button id="sq-single" aria-pressed="true">Inspect layer</button><button id="sq-compare" aria-pressed="false" disabled>Compare SAR dates</button><button id="sq-minus" aria-label="Zoom evidence out">−</button><button id="sq-plus" aria-label="Zoom evidence in">+</button></div><div id="sq-stage" class="sq-stage"><p>Choose a saved run, cached terrain, or a completed Workspace result.</p></div><p id="sq-legend" class="sq-legend">No observation selected. No illustrative satellite layers are displayed.</p><div id="sq-stack" class="sq-stack" aria-label="Available source layers"></div></section>
    <aside class="sq-inspector"><span class="eyebrow">EVALUATION / PROVENANCE</span><h2>Source record.</h2><div id="sq-inspector-content"><p>Select a layer to inspect its source, units, grid and limits.</p></div></aside></div><section id="sq-measures" class="sq-measures" aria-label="Selected source measurements"></section>`;
  $('#evaluation').replaceChildren(root, archive);
  const originalPicker=window.customPicker;
  if(typeof originalPicker==='function')window.customPicker=function(select){if(select.closest('#sq-evidence'))return;return originalPicker(select);};
  let catalog=[], selected='', layerIndex=0, visible=new Set(), opacities=new Map(), compare=false, zoom=1, offset=[0,0], drag=null, selectionVersion=0, abort=null;
  const api=async(path,signal)=>{const r=await fetch(path,{cache:'no-store',signal});if(!r.ok)throw Error('Source unavailable ('+r.status+'). Refresh after checking the local service.');return r.json();};
  const status=text=>{$('#sq-catalog-state').textContent=text;};
  function fillCatalog(){
    const query=$('#sq-source-filter').value.toLowerCase(), picker=$('#sq-source');
    picker.replaceChildren(new Option('No source selected',''));
    for (const item of catalog.filter(i=>(i.label+' '+i.id+' '+i.population).toLowerCase().includes(query))) picker.append(new Option(item.label+' · '+item.id, item.key));
    // Filtering must never silently change the source behind visible evidence.
    if(selected&&!Array.from(picker.options).some(o=>o.value===selected)) {const item=catalog.find(i=>i.key===selected);if(item)picker.append(new Option('Selected · '+item.id,item.key));}
    picker.value=selected;
  }
  async function refreshCatalog(){
    if(loading)return;loading=true;status('Reading source catalogue…');$('#sq-refresh').disabled=true;
    const results=await Promise.allSettled([api('/api/flood/runs'),api('/api/terrain/status')]);
    catalog=[];
    if(workspaceRecord)catalog.push({key:'workspace',id:workspaceRecord.id,label:'Current Workspace result',population:workspaceRecord.population});
    if(results[0].status==='fulfilled')for(const run of results[0].value.runs||[])catalog.push({key:'flood:'+run.id,id:run.id,label:run.event_name,population:run.population});
    if(results[1].status==='fulfilled')for(const scene of results[1].value.scenes||[])catalog.push({key:'terrain:'+scene.id,id:scene.id,label:scene.source,population:scene.population});
    if(selected&&!catalog.some(i=>i.key===selected)){selected='';await selectSource();}
    fillCatalog();status(catalog.length+' available records'+(results.some(r=>r.status==='rejected')?' · Some source services unavailable.':''));
    loading=false;$('#sq-refresh').disabled=false;
  }
  async function selectSource(){
    const version=++selectionVersion;abort?.abort();abort=new AbortController();const signal=abort.signal;
    evidence=null;layerIndex=0;compare=false;zoom=1;offset=[0,0];visible.clear();opacities.clear();
    $('#sq-layer-controls').replaceChildren();$('#sq-stack').replaceChildren();$('#sq-inspector-content').replaceChildren();$('#sq-measures').replaceChildren();
    $('#sq-stage-title').textContent=selected?'Loading selected source…':'No source selected';$('#sq-stage').replaceChildren(make('p',selected?'Verifying the selected record…':'Choose a source to inspect its real outputs.'));
    $('#sq-legend').textContent='No product loaded.';$('#sq-compare').disabled=true;footerUpdate();
    if(!selected)return;
    try{
      const [kind,...parts]=selected.split(':'),id=parts.join(':');
      if(kind==='workspace')evidence=workspaceRecord;
      else if(kind==='flood'){
        const prefix='/api/flood/runs/'+encodeURIComponent(id);
        const [run,grid,debris]=await Promise.all([api(prefix,signal),api(prefix+'/grid',signal),api(prefix+'/debris',signal).catch(()=>null)]);
        if(version!==selectionVersion)return;evidence=D.flood(run,grid,debris);
      }else {const scene=await api('/api/terrain/scenes/'+encodeURIComponent(id),signal);if(version!==selectionVersion)return;evidence=D.terrain(scene);}
      if(version!==selectionVersion||!evidence)return;
      evidence.layers.forEach(l=>visible.add(l.key));status(evidence.population+' · '+evidence.id);
      renderLayers();renderMeasures();draw();footerUpdate();
    }catch(error){if(version!==selectionVersion||error.name==='AbortError')return;evidence=null;status(error.message);$('#sq-stage-title').textContent='Source unavailable';$('#sq-stage').replaceChildren(make('p',error.message));footerUpdate();}
  }
  function renderLayers(){
    const controls=$('#sq-layer-controls'),stack=$('#sq-stack');controls.replaceChildren();stack.replaceChildren();
    evidence.layers.forEach((layer,i)=>{
      const row=make('div',null,'sq-layer-row'),label=make('label'),check=make('input');check.type='checkbox';check.checked=visible.has(layer.key);check.setAttribute('aria-label','Show '+layer.label);
      check.onchange=()=>{check.checked?visible.add(layer.key):visible.delete(layer.key);if(!visible.has(evidence.layers[layerIndex]?.key))layerIndex=evidence.layers.findIndex(l=>visible.has(l.key));draw();renderLayers();};label.append(check,make('span',layer.label));
      const inspect=make('button','↗');inspect.setAttribute('aria-label','Inspect '+layer.label);inspect.onclick=()=>pick(i);
      const up=make('button','↑');up.disabled=i===0;up.setAttribute('aria-label','Move '+layer.label+' up');up.onclick=()=>{const active=evidence.layers[layerIndex];[evidence.layers[i-1],evidence.layers[i]]=[evidence.layers[i],evidence.layers[i-1]];layerIndex=evidence.layers.indexOf(active);renderLayers();};
      row.append(label,inspect,up);controls.append(row);
      if(!visible.has(layer.key))return;
      const card=make('button',null,'sq-layer-card');card.setAttribute('aria-label','Select '+layer.label);card.setAttribute('aria-pressed',String(i===layerIndex));
      if(layer.url){const img=make('img');img.src=layer.url;img.alt='';img.loading='lazy';card.append(img);}else card.append(make('span','DSM','sq-dem-tile'));
      const text=make('span');text.append(make('strong',layer.label),make('small',layer.kind),make('small',layer.date));card.append(text);card.onclick=()=>pick(i);stack.append(card);
    });
  }
  function pick(index){layerIndex=index;compare=false;zoom=1;offset=[0,0];visible.add(evidence.layers[index].key);renderLayers();draw();}
  function sourceField(root,label,value){const d=make('div',null,'sq-field');d.append(make('small',label),make('p',value||'Not recorded'));root.append(d);}
  function inspect(layer){
    const target=$('#sq-inspector-content');target.replaceChildren();
    for(const [label,value] of [['Product',layer.kind],['Source',layer.source],['Time basis',layer.date],['Units',layer.units],['CRS',layer.grid?.crs],['SHA-256',layer.sha256]])sourceField(target,label,value);
    if(layer.download||layer.url){const a=make('a','Open original product ↗');a.href=layer.download||layer.url;a.target='_blank';a.rel='noopener';target.append(a);}
    const opacityLabel=make('label','Display opacity'),range=make('input');range.type='range';range.min='20';range.max='100';range.value=String(opacities.get(layer.key)||100);range.setAttribute('aria-label','Layer display opacity');
    range.oninput=()=>{opacities.set(layer.key,Number(range.value));$('#sq-stage').querySelectorAll('img,canvas').forEach(n=>n.style.opacity=range.value/100);};opacityLabel.append(range);target.append(opacityLabel);
    const provenance=make('details');provenance.append(make('summary','Full source record & grid'),make('pre',JSON.stringify({source:layer.sourceRecord,grid:layer.grid},null,2)));target.append(provenance);
    const limits=make('details');limits.open=true;limits.append(make('summary','Interpretation limits'));const list=make('ul');layer.limitations.forEach(t=>list.append(make('li',t)));limits.append(list);target.append(limits);
    if(selected==='workspace'){const a=make('a','Run JSON · complete trace ↗');a.href='/api/runs/'+encodeURIComponent(evidence.id)+'/result.json';a.target='_blank';a.rel='noopener';target.append(a);}
  }
  function transform(){const content=$('#sq-stage .sq-pan');if(content)content.style.transform=`translate(${offset[0]}px,${offset[1]}px) scale(${zoom})`;}
  function raster(layer){
    if(layer.url){const img=make('img');img.src=layer.url;img.alt=layer.label;img.draggable=false;img.style.opacity=(opacities.get(layer.key)||100)/100;img.onerror=()=>{img.replaceWith(make('p','Product preview unavailable. The original product link remains in Source record.'));};return img;}
    const canvas=make('canvas'),m=layer.mesh;
    if(!m?.z_m?.length)return make('p','No terrain grid available.');
    const values=m.z_m.flat().filter(D.finite),lo=Math.min(...values),hi=Math.max(...values);
    canvas.width=m.z_m[0].length;canvas.height=m.z_m.length;canvas.setAttribute('aria-label',layer.legend);canvas.setAttribute('role','img');
    const ctx=canvas.getContext('2d'),pixels=ctx.createImageData(canvas.width,canvas.height);
    // mesh y may ascend or descend: canvas top is north, never silently flip the grid.
    const rows=m.y_m?.[0]<m.y_m?.at(-1)?[...m.z_m].reverse():m.z_m;
    rows.forEach((row,r)=>row.forEach((v,c)=>{const grey=D.finite(v)?Math.round(30+225*(v-lo)/(hi-lo||1)):0;pixels.data.set([grey,grey,grey,D.finite(v)?255:0],(r*canvas.width+c)*4);}));
    ctx.putImageData(pixels,0,0);canvas.style.opacity=(opacities.get(layer.key)||100)/100;return canvas;
  }
  function draw(){
    const stage=$('#sq-stage'),layer=evidence?.layers[layerIndex];stage.replaceChildren();
    const pair=evidence?.layers.filter(l=>l.key==='pre'||l.key==='post')||[];
    const canCompare=pair.length===2&&pair.every(l=>visible.has(l.key));if(!canCompare)compare=false;$('#sq-compare').disabled=!canCompare;$('#sq-single').setAttribute('aria-pressed',String(!compare));$('#sq-compare').setAttribute('aria-pressed',String(compare));
    if(!layer||!visible.has(layer.key)){stage.append(make('p','All layers are hidden. Enable a source layer to inspect it.'));$('#sq-stage-title').textContent='No visible layer';$('#sq-legend').textContent='No layer displayed.';$('#sq-inspector-content').replaceChildren(make('p','Enable a layer to inspect its record.'));return;}
    const pan=make('div',null,'sq-pan');stage.append(pan);
    if(compare&&pair.length===2){pan.classList.add('sq-compare-grid');pair.forEach(l=>{const f=make('figure');f.append(raster(l),make('figcaption',l.label+' · '+l.date));pan.append(f);});}
    else pan.append(raster(layer));
    $('#sq-stage-title').textContent=compare?'SAR · dated comparison':layer.label;
    $('#sq-legend').textContent=compare?'Dated source displays shown separately. Grid: '+(layer.grid?.crs||'not recorded')+'. Physical co-registration is not independently validated.':layer.legend;
    inspect(layer);transform();
  }
  function renderMeasures(){
    const target=$('#sq-measures');target.replaceChildren();
    for(const [label,value,unit] of evidence.measures){const card=make('div',null,'sq-measure');card.append(make('small',label),make('strong',D.number(value)+' '+unit));target.append(card);}
    const distributions=evidence.distributions||[];
    if(distributions.length)for(const d of distributions){
      const chart=make('section',null,'sq-distribution');chart.append(make('h3',d.label),make('p','Candidate classes; not accuracy or confidence. Denominator: '+D.number(d.denominator,0)+' valid pixels. Water and debris populations are not pooled.'));
      d.classes.forEach(([label,value])=>{const row=make('div'),bar=make('meter');bar.min=0;bar.max=d.denominator;bar.value=value;bar.setAttribute('aria-label',label+': '+value+' pixels');row.append(make('span',label),bar,make('span',D.number(value,0)+' px'));chart.append(row);});target.append(chart);
    }else target.append(make('p','No compatible class distribution or time series is recorded for this source.','sq-muted'));
  }
  $('#sq-source-filter').oninput=fillCatalog;$('#sq-source').onchange=()=>{selected=$('#sq-source').value;selectSource();};$('#sq-refresh').onclick=refreshCatalog;
  $('#sq-compare').onclick=()=>{layerIndex=evidence.layers.findIndex(l=>l.key==='pre');compare=true;zoom=1;offset=[0,0];renderLayers();draw();};$('#sq-single').onclick=()=>{compare=false;draw();};
  $('#sq-fit').onclick=()=>{zoom=1;offset=[0,0];transform();};$('#sq-plus').onclick=()=>{zoom=Math.min(8,zoom*1.3);transform();};$('#sq-minus').onclick=()=>{zoom=Math.max(1,zoom/1.3);transform();};
  const stage=$('#sq-stage');stage.onpointerdown=e=>{if(!evidence)return;drag=[e.clientX-offset[0],e.clientY-offset[1]];stage.setPointerCapture(e.pointerId);};stage.onpointermove=e=>{if(drag){offset=[e.clientX-drag[0],e.clientY-drag[1]];transform();}};stage.onpointerup=stage.onpointercancel=()=>drag=null;

  function navigate(){
    const current=route();document.body.dataset.sqRoute=current;
    $('header nav').querySelectorAll('button').forEach(b=>{const active=b.classList.contains('active');if(active)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
    footerUpdate();if(current==='evidence'&&!catalog.length&&!loading)refreshCatalog();
  }
  const routeObserver=new MutationObserver(navigate);
  routeObserver.observe($('main'),{subtree:true,attributes:true,attributeFilter:['hidden']});
  $('header nav').addEventListener('click',()=>queueMicrotask(navigate));
  window.addEventListener('hashchange',()=>{const id={'#workspace':'lab-tab','#evidence':'eval-tab','#terrain':'earth-tab','#flood':'earth-tab','#investigate':'earth-tab','#datasets':'external-tab'}[location.hash];if(id)$('#'+id)?.click();});
  // The baseline buttons use replaceState; preserve actual Back/Forward entries here.
  $('header nav').addEventListener('click',event=>{event.sqPrevious=location.href;},true);
  $('header nav').addEventListener('click',event=>{const id=event.target.closest('button')?.id;const hash={'lab-tab':'#workspace','eval-tab':'#evidence','earth-tab':'#terrain','external-tab':'#datasets'}[id];if(hash&&event.sqPrevious&&new URL(event.sqPrevious).hash!==hash){history.replaceState(null,'',event.sqPrevious);history.pushState(null,'',hash);}});
  brand.addEventListener('click',e=>{e.preventDefault();$('#lab-tab').click();});
  document.addEventListener('visibilitychange',()=>document.body.classList.toggle('sq-page-hidden',document.hidden));
  if(navigator.connection?.saveData)document.body.classList.add('sq-save-data');
  const observed=new IntersectionObserver(entries=>entries.forEach(e=>e.target.classList.toggle('sq-offscreen',!e.isIntersecting)));observed.observe(galaxy);observed.observe($('#loading-art'));
  new MutationObserver(entries=>entries.forEach(e=>e.addedNodes.forEach(n=>{if(n.nodeType===1)n.querySelectorAll?.('.sq-float').forEach(img=>observed.observe(img));}))).observe($('main'),{childList:true,subtree:true});
  $('#question').addEventListener('input',()=>document.body.classList.toggle('sq-has-query',Boolean($('#question').value.trim())));
  for(const id of ['sample','single-file','file-a','file-b'])$('#'+id).addEventListener('change',()=>window.SQNoir.clearWorkspace());
  // Remove completed metadata whenever the existing controller invalidates its result.
  new MutationObserver(()=>{if($('#result').hidden&&workspaceRecord)window.SQNoir.clearWorkspace();}).observe($('#result'),{attributes:true,attributeFilter:['hidden']});
  navigate();
})();
