/* One native workspace for terrain, saved water observations and questions. */
(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const node = (tag, text, className) => {
    const value = document.createElement(tag);
    if (text !== undefined) value.textContent = text;
    if (className) value.className = className;
    return value;
  };
  const number = (value, digits = 1) => typeof value === 'number' && Number.isFinite(value)
    ? value.toLocaleString(undefined, {maximumFractionDigits: digits}) : 'Unavailable';
  const date = value => value ? new Date(value).toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'}) : 'Date unavailable';
  const safeJSON = value => JSON.stringify(value, null, 2);
  const terminal = new Set(['complete','abstained','failed','cancelled','interrupted']);
  const state = {
    booted:false, contextLoading:true, runs:[], scenes:[], run:null, scene:null, exposure:null, coverage:null,
    view:'terrain', colour:'elevation', height:1, water:true, fallback:false,
    selection:0, requests:null, plotVersion:0, plotPromise:Promise.resolve(), library:null,
    job:null, activeJob:null, submitting:false, sourcesLoaded:false, plotReady:false, poll:0, picking:false, points:[], profile:null,
  };

  const tab = node('button', 'Terrain & flood'); tab.id = 'earth-tab';
  $('header nav').append(tab);
  const panel = node('section', undefined, 'earth-workspace'); panel.id = 'earth'; panel.hidden = true;
  panel.innerHTML = `
    <div class="intro earth-intro">
      <div><span class="eyebrow">CONNECTED EARTH OBSERVATIONS</span><h1>Terrain & flood.</h1></div>
      <p>See the context. Ask the question. Inspect the evidence.</p>
    </div>
    <div class="earth-layout">
      <div class="earth-visual">
        <div class="earth-view-header"><div><span class="earth-kicker" id="earth-view-kicker">COPERNICUS DSM</span><h2 id="earth-view-title">Terrain context</h2></div><button class="earth-text-button" id="earth-ask-focus">Ask about this view ↗</button></div>
        <div class="earth-view-tabs" role="group" aria-label="Observation view">
          <button data-view="terrain" aria-pressed="true">3D terrain</button>
          <button data-view="pre">Before SAR</button><button data-view="post">After SAR</button><button data-view="water">Water map</button>
        </div>
        <div class="earth-viewer" id="earth-viewer">
          <div id="earth-surface" aria-label="Interactive measured terrain surface"></div>
          <canvas id="earth-fallback" width="128" height="128" aria-label="Numeric terrain grid fallback" hidden></canvas>
          <img id="earth-image" alt="Selected saved satellite observation" hidden draggable="false">
          <div class="earth-empty" id="earth-empty" hidden><img src="/art/empty-planet.png" alt=""><p id="earth-empty-text">Choose available observations to inspect this area.</p></div>
        </div>
        <div class="earth-view-toolbar" id="earth-terrain-controls">
          <label class="earth-compact-label" for="earth-colour">Colour<select id="earth-colour"><option value="elevation">Elevation</option><option value="slope">Slope</option></select></label>
          <label class="earth-compact-label" for="earth-height">Height<select id="earth-height"><option value="1">1×</option><option value="2">2×</option><option value="4">4×</option></select></label>
          <button id="earth-water-toggle" aria-pressed="true" disabled>Water candidates</button>
          <button id="earth-reset" title="Reset terrain camera">Reset view</button>
          <details class="earth-view-options"><summary>More</summary><div><button id="earth-2d">Use 2D fallback</button><button id="earth-pick">Pick cross-section points</button></div></details>
        </div>
        <div class="earth-view-toolbar" id="earth-image-controls" hidden><button id="earth-image-less" aria-label="Zoom out">−</button><button id="earth-image-more" aria-label="Zoom in">+</button><button id="earth-image-reset">Reset view</button><span>Drag to pan</span></div>
        <p class="earth-view-note" id="earth-view-note">Drag to rotate · Scroll to zoom · 90 m source</p>
        <div class="earth-key-metrics" id="earth-key-metrics"></div>
        <div class="earth-layer-state" id="earth-layer-state" role="status" aria-live="polite">Loading recorded observations…</div>
        <details class="earth-disclosure earth-profile"><summary>Cross-section <span id="earth-profile-summary">Choose two terrain points</span></summary><div class="earth-disclosure-body"><p>Pick two points on the terrain, or enter coordinates in its projected metre CRS.</p><div class="earth-profile-fields"><label>Start easting<input id="earth-x1" type="number" step="0.1"></label><label>Start northing<input id="earth-y1" type="number" step="0.1"></label><label>End easting<input id="earth-x2" type="number" step="0.1"></label><label>End northing<input id="earth-y2" type="number" step="0.1"></label></div><div class="earth-button-row"><button id="earth-profile-pick">Pick on terrain</button><button id="earth-profile-calculate">Calculate profile</button></div><p id="earth-profile-state" role="status">Missing-data gaps remain visible.</p><div id="earth-profile-chart" hidden></div></div></details>
      </div>
      <aside class="earth-sidebar">
        <span class="eyebrow">THIS AREA · CONNECTED ANALYSIS</span><h2>Ask in context.</h2>
        <label for="earth-run">Saved flood observation</label><div class="earth-selection-row"><select id="earth-run"><option value="">Checking available runs…</option></select><button id="earth-refresh" aria-label="Refresh available observations" title="Refresh available observations">↻</button></div>
        <p id="earth-dates" class="earth-muted">Saved source dates will appear here.</p>
        <div class="earth-context-chips" id="earth-context-chips"></div>
        <form id="earth-question-form">
          <label for="earth-question">Your question</label><textarea id="earth-question" rows="3" maxlength="1200" placeholder="Which roads need inspection near the water, and how steep is the terrain?"></textarea>
          <div class="earth-prompts" role="group" aria-label="Question suggestions"><button type="button" data-prompt="overview">Summarize this area</button><button type="button" data-prompt="assets">Roads & buildings</button><button type="button" data-prompt="slope">Explain the slope</button></div>
          <div class="earth-submit-row"><button class="primary" id="earth-run-question" type="submit" disabled>↗ Analyze this area</button><button type="button" id="earth-stop" hidden>Stop</button></div>
        </form>
        <p class="earth-feedback" id="earth-question-state" role="status" aria-live="polite" hidden></p>
        <section id="earth-answer" class="earth-answer" aria-label="Analysis result" tabindex="-1" hidden><span class="eyebrow">ANALYSIS RESULT</span><p id="earth-answer-text"></p><div class="earth-answer-metrics" id="earth-answer-metrics"></div><details class="earth-disclosure"><summary>Answer evidence & tool trace</summary><div class="earth-disclosure-body"><p id="earth-answer-selection" class="earth-muted"></p><div id="earth-answer-sources"></div><div id="earth-answer-trace"></div><a id="earth-job-download">Download recorded analysis ↓</a></div></details><details class="earth-disclosure"><summary>What this answer can establish</summary><div id="earth-answer-limits" class="earth-disclosure-body"></div></details></section>
        <details class="earth-disclosure" id="earth-intersections"><summary>Mapped intersections <span id="earth-intersection-count">Not loaded</span></summary><div class="earth-disclosure-body"><p>Candidate overlap is a cue for inspection. It does not establish damage or closure.</p><div class="earth-table-scroll" id="earth-intersection-table"></div></div></details>
        <details class="earth-disclosure" id="earth-sources"><summary>Sources, dates & downloads</summary><div class="earth-disclosure-body"><label for="earth-scene">Cached terrain</label><select id="earth-scene"><option value="">Checking terrain…</option></select><div id="earth-source-content"></div><details><summary>Alignment checks</summary><p id="earth-alignment-note">No grid mapping calculated.</p><pre id="earth-alignment-json"></pre></details><div id="earth-downloads" class="earth-downloads"></div><details><summary>Obtain the public terrain sample</summary><p>One public GLO-90 tile, capped at 16 MiB. No paid API.</p><label class="earth-consent"><input type="checkbox" id="earth-acquire-consent"> I approve this public download.</label><button id="earth-acquire">Obtain terrain</button><p id="earth-acquire-state" role="status"></p></details></div></details>
        <details class="earth-disclosure"><summary>Methods & interpretation limits</summary><div class="earth-disclosure-body"><p>Saved water candidates use Flood Lab's fixed SAR thresholds. Copernicus is a historical 90 m surface model, including vegetation and structures.</p><p>Grid reprojection is checked. Physical co-registration needs independent validation. Candidate markers follow interpolated DSM heights with a 2 m visibility offset; they do not estimate water depth.</p><p>Questions use a deterministic local tool workflow, with no AI model invocation. It reads selected saved evidence. Unsupported depth, safety and forecast requests are refused.</p><ul id="earth-run-limits"></ul></div></details>
      </aside>
    </div>`;
  $('main').append(panel);
  // Baseline boot replaces its image-mode selects with snapshot pickers. New
  // evidence selectors stay native so later source refreshes remain accurate.
  const originalPicker=window.customPicker;
  if(typeof originalPicker==='function')window.customPicker=function(select){if(select.closest('#earth'))return;return originalPicker(select);};

  async function api(path, options = {}) {
    const response = await fetch(path, {cache:'no-store', ...options});
    let data;
    try { data = await response.json(); } catch { throw Error('The local service returned an unreadable response.'); }
    if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : 'Request rejected ('+response.status+').');
    return data;
  }
  const post = (path, data) => api(path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  function message(text) { $('#earth-layer-state').textContent = text; }
  function feedback(text) { $('#earth-question-state').hidden = !text; $('#earth-question-state').textContent = text; }
  function isCurrent(token) { return token === state.selection; }
  function field(label, value) { const row=node('div',undefined,'earth-source-row');row.append(node('span',label),node('p',value ?? 'Not recorded'));return row; }
  function table(headers, rows) {
    const t=node('table'),head=node('thead'),hr=node('tr'),body=node('tbody');
    headers.forEach(h=>hr.append(node('th',h)));head.append(hr);t.append(head);
    rows.forEach(values=>{const tr=node('tr');values.forEach(value=>tr.append(node('td',String(value))));body.append(tr);});t.append(body);return t;
  }
  function metric(target, label, value) {const item=node('div');item.append(node('strong',value),node('span',label));target.append(item);}

  function open() {
    $('#lab').hidden=true;$('#evaluation').hidden=true;panel.hidden=false;$('main > .intro').hidden=true;
    $('#lab-tab').classList.remove('active');$('#eval-tab').classList.remove('active');tab.classList.add('active');
    history.replaceState(null,'',location.pathname+location.search+'#terrain');
    if (!state.booted) { state.booted=true;refresh(); }
    else if (state.view==='terrain' && window.Plotly && !state.fallback) Plotly.Plots.resize($('#earth-surface'));
  }
  tab.onclick=open;
  ['lab-tab','eval-tab'].forEach(id=>$('#'+id).addEventListener('click',()=>{panel.hidden=true;tab.classList.remove('active');$('main > .intro').hidden=false;history.replaceState(null,'',location.pathname+location.search+(id==='eval-tab'?'#evidence':''));}));

  async function refresh() {
    if(state.activeJob||state.submitting)return;
    state.contextLoading=true;setBusy(false);
    $('#earth-refresh').disabled=true;
    const results=await Promise.allSettled([api('/api/flood/runs'),api('/api/terrain/status')]);
    const selectedRun=state.sourcesLoaded?$('#earth-run').value:(localStorage.getItem('earth-run')??localStorage.getItem('jai-last-flood-run'));
    const selectedScene=state.sourcesLoaded?$('#earth-scene').value:localStorage.getItem('earth-scene');
    state.runs=results[0].status==='fulfilled'?results[0].value.runs.filter(r=>r.population==='FROZEN_REAL_OBSERVATION'):[];
    state.scenes=results[1].status==='fulfilled'?results[1].value.scenes:[];
    const runSelect=$('#earth-run');runSelect.replaceChildren(node('option',state.runs.length?'Terrain only · no flood observation':'No saved flood observation'));runSelect.options[0].value='';
    const names=new Map();state.runs.forEach(r=>names.set(r.event_name,(names.get(r.event_name)||0)+1));
    state.runs.forEach(r=>{const option=node('option',r.event_name+(names.get(r.event_name)>1?' · '+r.id.slice(-6):''));option.value=r.id;runSelect.append(option);});
    runSelect.value=selectedRun===''?'':state.runs.some(r=>r.id===selectedRun)?selectedRun:state.runs.find(r=>r.id==='event-fe47db331390')?.id || state.runs[0]?.id || '';
    const sceneSelect=$('#earth-scene');sceneSelect.replaceChildren(node('option','No terrain selected'));sceneSelect.options[0].value='';
    state.scenes.forEach((s,i)=>{const option=node('option','Copernicus 90 m · saved area '+(i+1));option.value=s.id;sceneSelect.append(option);});
    sceneSelect.value=selectedScene===''?'':state.scenes.some(s=>s.id===selectedScene)?selectedScene:state.scenes[0]?.id || '';
    state.sourcesLoaded=true;
    await selectContext();
    if(results[0].status==='rejected')message('Terrain remains available. Flood Lab is unavailable; refresh after starting the local service.');
    if(results[1].status==='rejected')message('Terrain service unavailable. Saved flood observations can still be inspected.');
    setBusy(Boolean(state.activeJob||state.submitting));
  }

  async function selectContext() {
    if(state.activeJob||state.submitting)return;
    state.contextLoading=true;setBusy(false);
    const token=++state.selection;state.requests?.abort();state.requests=new AbortController();const signal=state.requests.signal;
    state.run=null;state.scene=null;state.coverage=null;state.exposure=null;state.profile=null;state.points=[];state.picking=false;
    ++state.plotVersion;$('#earth-key-metrics').replaceChildren();$('#earth-context-chips').replaceChildren();$('#earth-dates').textContent='Checking the selected source dates…';showEmpty('Loading the selected area…');
    $('#earth-pick').textContent='Pick cross-section points';$('#earth-profile-pick').textContent='Pick on terrain';
    $('#earth-profile-chart').hidden=true;$('#earth-profile-summary').textContent='Choose two terrain points';$('#earth-profile-state').textContent='Missing-data gaps remain visible.';
    $('#earth-answer').hidden=true;feedback('');$('#earth-water-toggle').disabled=true;
    $('#earth-image').hidden=true;$('#earth-image').removeAttribute('src');++imageVersion;
    $('#earth-source-content').replaceChildren();$('#earth-downloads').replaceChildren();$('#earth-intersection-table').replaceChildren();$('#earth-run-limits').replaceChildren();$('#earth-intersection-count').textContent='Not loaded';
    $('#earth-alignment-json').textContent='';$('#earth-alignment-note').textContent='No grid mapping calculated.';
    message('Loading the selected observations…');
    const runID=$('#earth-run').value,sceneID=$('#earth-scene').value;
    localStorage.setItem('earth-run',runID);localStorage.setItem('earth-scene',sceneID);
    if(runID)localStorage.setItem('jai-last-flood-run',runID);
    const [runResult,sceneResult]=await Promise.allSettled([
      runID?api('/api/flood/runs/'+encodeURIComponent(runID),{signal}):Promise.resolve(null),
      sceneID?api('/api/terrain/scenes/'+encodeURIComponent(sceneID),{signal}):Promise.resolve(null),
    ]);
    if(!isCurrent(token))return;
    state.run=runResult.status==='fulfilled'?runResult.value:null;state.scene=sceneResult.status==='fulfilled'?sceneResult.value:null;
    updateContext();drawView();
    const tasks=[];
    if(state.run)tasks.push(api('/api/flood/runs/'+encodeURIComponent(runID)+'/exposure',{signal}).then(value=>{if(isCurrent(token)){state.exposure=value;showIntersections();}}).catch(error=>{if(isCurrent(token)&&error.name!=='AbortError')$('#earth-intersection-count').textContent='Unavailable';}));
    if(state.run&&state.scene)tasks.push(api('/api/context/coverage?run_id='+encodeURIComponent(runID)+'&scene_id='+encodeURIComponent(sceneID),{signal}).then(value=>{
      if(!isCurrent(token))return;state.coverage=value;$('#earth-water-toggle').disabled=state.fallback;
      $('#earth-alignment-note').textContent=value.common_valid_dem_cells+' / '+value.terrain_valid_cells+' valid terrain cell centres share observed support. Physical co-registration is not independently validated.';
      const evidence={...value};delete evidence.candidate_points;delete evidence.classes_on_mesh;delete evidence.candidate_fraction_on_mesh;$('#earth-alignment-json').textContent=safeJSON(evidence);
      message('Terrain + saved water observations connected · '+value.candidate_points.length+' candidate locations on valid DSM support');updateChips();if(state.view==='terrain')drawSurface();
    }).catch(error=>{if(isCurrent(token)&&error.name!=='AbortError'){message('Terrain and flood are available separately. '+error.message);$('#earth-alignment-note').textContent=error.message;}}));
    if(!state.run||!state.scene)message(state.scene?'Terrain ready · select a saved flood observation to add water context.':state.run?'Saved flood observation ready · no cached terrain selected.':'No observations available. Open Sources to check terrain or refresh the saved runs.');
    if(runResult.status==='rejected')message(runResult.reason.message);
    if(sceneResult.status==='rejected')message(sceneResult.reason.message);
    await Promise.allSettled(tasks);
    if(!isCurrent(token))return;
    const previous=localStorage.getItem('earth-last-job');
    if(previous&&!state.job){try{const saved=await api('/api/investigations/'+previous);if(isCurrent(token)&&saved.selection.run_id===(state.run?.id||null)&&saved.selection.scene_id===(state.scene?.id||null)){state.job=saved;$('#earth-question').value=saved.selection.question;renderJob(saved);if(!terminal.has(saved.state))pollJob(saved.id);}}catch{/* Old records never block the current selection. */}}
    if(isCurrent(token)){state.contextLoading=false;setBusy(Boolean(state.activeJob||state.submitting));}
  }

  function updateContext() {
    const dates=state.run?.provenance.inputs||[];
    $('#earth-dates').textContent=state.run?date(dates[0]?.datetime)+' → '+date(dates[1]?.datetime)+' · saved SAR pair':state.scene?'Cached Copernicus surface model · terrain context':'No recorded observations selected';
    updateChips();showMetrics();showSources();
    const enabled=Boolean(state.run||state.scene);$('#earth-run-question').disabled=!enabled||state.contextLoading||Boolean(state.activeJob||state.submitting);
    document.querySelectorAll('[data-view]').forEach(button=>button.disabled=button.dataset.view==='terrain'?!state.scene:!state.run);
    if(state.view==='terrain'&&!state.scene&&state.run)state.view='post';
    else if(state.view!=='terrain'&&!state.run&&state.scene)state.view='terrain';
    if(state.scene){const m=state.scene.mesh,r=Math.floor(m.z_m.length/2),good=m.z_m[r].map((v,i)=>v!==null?i:null).filter(v=>v!==null);if(good.length>3){$('#earth-x1').value=m.x_m[good[1]].toFixed(3);$('#earth-y1').value=m.y_m[r].toFixed(3);$('#earth-x2').value=m.x_m[good.at(-2)].toFixed(3);$('#earth-y2').value=m.y_m[r].toFixed(3);}}
  }
  function updateChips() {
    const chips=$('#earth-context-chips');chips.replaceChildren();
    if(state.scene)chips.append(node('span','Terrain · 90 m DSM'));
    if(state.run)chips.append(node('span','Flood · saved observation'));
    if(state.coverage)chips.append(node('span','Grid mapped','earth-connected'));
  }
  function showMetrics() {
    const target=$('#earth-key-metrics');target.replaceChildren();
    if(state.scene){metric(target,'DSM elevation',number(state.scene.statistics.elevation_min_m,0)+'–'+number(state.scene.statistics.elevation_max_m,0)+' m');metric(target,'Median slope',number(state.scene.statistics.slope_median_deg)+'°');}
    if(state.run){const s=state.run.summary;metric(target,'Water candidates',s.new_water_m2==null?'Unavailable':number(s.new_water_m2/10000,2)+' ha');metric(target,'Building intersections',number(s.exposed_buildings,0));}
  }
  function showSources() {
    const content=$('#earth-source-content'),downloads=$('#earth-downloads');
    content.replaceChildren();downloads.replaceChildren();
    if(state.run){content.append(field('Saved run',state.run.id),field('Population',state.run.population),field('Event UTC',state.run.provenance.event_time),field('Historical OSM UTC',state.run.provenance.osm_snapshot));
      state.run.provenance.inputs.forEach((input,i)=>{const details=node('details');details.append(node('summary',(i?'After':'Before')+' SAR source'),node('pre',safeJSON(input)));content.append(details);});
      state.run.artifacts.forEach(a=>{const link=node('a',a.name+' ↓');link.href=a.url;link.download=a.name;link.title='Saved SHA-256 '+a.sha256;downloads.append(link);});
      state.run.limitations.forEach(text=>$('#earth-run-limits').append(node('li',text)));
    }
    if(state.scene){content.append(field('Terrain source',state.scene.provenance.dataset),field('Source resolution',state.scene.provenance.nominal_source_resolution_m+' m nominal'),field('Terrain time basis',state.scene.provenance.release));
      const details=node('details');details.append(node('summary','Terrain provenance & hashes'),node('pre',safeJSON({id:state.scene.id,...state.scene.provenance,hashes:state.scene.hashes})));content.append(details);
      const link=node('a','Metric terrain GeoTIFF ↓');link.href='/api/terrain/scenes/'+state.scene.id+'/raster';link.download='copernicus90-metric.tif';downloads.append(link);
    }
  }
  function showIntersections(rows=state.exposure?.rows) {
    const target=$('#earth-intersection-table');target.replaceChildren();if(!rows)return;
    const selected=rows.filter(r=>r.status==='exposed'||r.status==='unknown').sort((a,b)=>(a.status!=='exposed')-(b.status!=='exposed')||b.exposed-a.exposed);
    $('#earth-intersection-count').textContent=selected.length+' review records';
    target.append(table(['Feature','Kind','Intersection','Coverage status'],selected.slice(0,40).map(r=>[r.id,r.kind,number(r.exposed)+' '+r.unit,r.status])));
    target.append(node('p','Showing '+Math.min(selected.length,40)+' of '+selected.length+' exposed/unknown records. The source CSV retains the complete table.','earth-muted'));
  }

  async function plotly() {
    if(window.Plotly)return;
    if(!state.library)state.library=new Promise((resolve,reject)=>{const script=node('script');script.src='/jai/assets/vendor/plotly-4.1.1.min.js';script.onload=resolve;script.onerror=()=>{state.library=null;reject(Error('3D unavailable. Showing the numeric 2D terrain.'));};document.head.append(script);});
    await state.library;
  }
  const elevationScale=[[0,'#262626'],[.25,'#555451'],[.5,'#8b8982'],[.75,'#bbb6a9'],[1,'#eee6cf']];
  const slopeScale=[[0,'#292929'],[.5,'#8a7753'],[1,'#e0bb6d']];
  function palette() {const style=getComputedStyle(document.documentElement);return {text:style.getPropertyValue('--text').trim(),muted:style.getPropertyValue('--muted').trim(),line:style.getPropertyValue('--line').trim()};}
  const plotConfig={responsive:true,displaylogo:false,displayModeBar:false};
  function drawSurface() {
    const version=++state.plotVersion,selection=state.selection;
    state.plotPromise=state.plotPromise.catch(()=>{}).then(async()=>{
      if(version!==state.plotVersion||state.view!=='terrain'||!state.scene)return;
      if(state.fallback){drawFallback();return;}
      try {
        await plotly();if(version!==state.plotVersion||selection!==state.selection)return;
        const m=state.scene.mesh,s=state.scene.statistics,p=palette();
        const xr=Math.abs(m.x_m.at(-1)-m.x_m[0]),yr=Math.abs(m.y_m.at(-1)-m.y_m[0]),span=Math.max(xr,yr),zr=Math.max(1,s.elevation_max_m-s.elevation_min_m);
        const traces=[{type:'surface',x:m.x_m,y:m.y_m,z:m.z_m,surfacecolor:state.colour==='slope'?m.slope_deg:m.z_m.map(row=>row.slice()),colorscale:state.colour==='slope'?slopeScale:elevationScale,connectgaps:false,colorbar:{title:{text:state.colour==='slope'?'Slope °':'Height m'},thickness:9,len:.66,x:.99},hovertemplate:'Easting %{x:.0f} m<br>Northing %{y:.0f} m<br>DSM height %{z:.1f} m<extra></extra>'}];
        if(state.coverage&&state.water){const points=state.coverage.candidate_points;traces.push({type:'scatter3d',name:'Water candidates',mode:'markers',showlegend:false,x:points.map(p=>p.x_m),y:points.map(p=>p.y_m),z:points.map(p=>p.height_m+2),customdata:points.map(p=>p.height_m),marker:{size:3,color:'#d6b66a',opacity:.9},hovertemplate:'Satellite water candidate<br>Easting %{x:.0f} m<br>Northing %{y:.0f} m<br>DSM context %{customdata:.1f} m<extra>Not water depth</extra>'});}
        $('#earth-surface').hidden=false;$('#earth-fallback').hidden=true;$('#earth-water-toggle').disabled=!state.coverage;$('#earth-water-toggle').setAttribute('aria-pressed',String(state.water));$('#earth-2d').textContent='Use 2D fallback';
        await Plotly.react($('#earth-surface'),traces,{autosize:true,paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{color:p.muted,size:10},margin:{l:8,r:34,t:8,b:6},scene:{bgcolor:'rgba(0,0,0,0)',xaxis:{title:{text:'Easting m'},gridcolor:p.line,zeroline:false,showspikes:false},yaxis:{title:{text:'Northing m'},gridcolor:p.line,zeroline:false,showspikes:false},zaxis:{title:{text:'DSM m'},gridcolor:p.line,zeroline:false,showspikes:false},aspectmode:'manual',aspectratio:{x:xr/span,y:yr/span,z:zr/span*state.height},camera:{eye:{x:1.35,y:1.35,z:1.05}}},uirevision:state.scene.id},plotConfig);
        state.plotReady=true;bindPicking();viewNote();
      } catch(error) { if(selection===state.selection){state.fallback=true;drawFallback();message(error.message);} }
    });
    return state.plotPromise;
  }
  function drawFallback() {
    if(!state.scene)return;$('#earth-surface').hidden=true;const canvas=$('#earth-fallback');canvas.hidden=false;
    $('#earth-water-toggle').disabled=true;$('#earth-water-toggle').setAttribute('aria-pressed','false');
    const z=state.colour==='slope'?state.scene.mesh.slope_deg:state.scene.mesh.z_m,values=z.flat().filter(v=>v!==null),lo=Math.min(...values),hi=Math.max(...values);
    canvas.width=z[0].length;canvas.height=z.length;const ctx=canvas.getContext('2d'),image=ctx.createImageData(canvas.width,canvas.height);
    for(let r=0;r<z.length;r++)for(let c=0;c<z[0].length;c++){const v=z[r][c],q=v===null?0:(v-lo)/(hi-lo||1),shade=Math.round(38+q*190);image.data.set(v===null?[20,20,20,255]:[shade,shade,Math.round(shade*.94),255],(r*canvas.width+c)*4);}
    ctx.putImageData(image,0,0);viewNote();$('#earth-2d').textContent='Return to 3D';
  }
  function viewNote() {
    const label=state.view==='pre'?'Before SAR':state.view==='post'?'After SAR':'Saved water map';
    $('#earth-view-note').textContent=state.view!=='terrain'?(state.view==='water'?'Blue: water at both dates · Gold: new-water candidate · Gray: invalid':label+' · recorded radar preview · drag to pan'):
      state.fallback?'2D numeric terrain · water markers hidden · gray/black cells may be unavailable':
      'Drag to rotate · '+state.height+'× height · 90 m source'+(state.coverage&&state.water?' · Gold: water candidates (not depth)':'');
  }
  let imageVersion=0,zoom=1,offset=[0,0],drag=null;
  function drawView() {
    document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===state.view)));
    const terrain=state.view==='terrain';$('#earth-terrain-controls').hidden=!terrain;$('#earth-image-controls').hidden=terrain;
    $('#earth-empty').hidden=true;$('#earth-image').hidden=true;$('#earth-surface').hidden=!terrain;$('#earth-fallback').hidden=true;
    $('#earth-view-kicker').textContent=terrain?'COPERNICUS · 90 M DSM':'SENTINEL-1 · SAVED OBSERVATION';
    $('#earth-view-title').textContent=terrain?'Terrain & water context':state.view==='pre'?'Before the event':state.view==='post'?'After the event':'Water candidates';
    viewNote();
    if(terrain&&state.scene){drawSurface();return;}
    ++state.plotVersion;
    if(!terrain&&state.run){const version=++imageVersion,selection=state.selection,img=$('#earth-image');resetImage();img.onload=()=>{if(version===imageVersion&&selection===state.selection&&state.view!=='terrain')img.hidden=false;};img.onerror=()=>{if(version===imageVersion){img.hidden=true;showEmpty('This saved image is unavailable or failed its evidence check.');}};img.alt=state.view==='water'?'Verified categorical water candidate map':(state.view==='pre'?'Before':'After')+' Sentinel-1 radar preview';img.src='/api/flood/runs/'+state.run.id+(state.view==='water'?'/candidate.png':'/artifact/'+(state.view==='pre'?'pre.png':'post.png'));return;}
    showEmpty(terrain?'No cached terrain is selected. Open Sources to choose or obtain a sample.':'Select an available saved flood observation to see its imagery.');
  }
  function showEmpty(text){$('#earth-surface').hidden=true;$('#earth-fallback').hidden=true;$('#earth-empty').hidden=false;$('#earth-empty-text').textContent=text;}
  function resetImage(){zoom=1;offset=[0,0];transformImage();}
  function transformImage(){$('#earth-image').style.transform=`translate(${offset[0]}px,${offset[1]}px) scale(${zoom})`;}
  document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>{state.view=button.dataset.view;drawView();});
  $('#earth-colour').onchange=()=>{state.colour=$('#earth-colour').value;drawSurface();};
  $('#earth-height').onchange=()=>{state.height=Number($('#earth-height').value);drawSurface();};
  $('#earth-water-toggle').onclick=()=>{state.water=!state.water;$('#earth-water-toggle').setAttribute('aria-pressed',String(state.water));drawSurface();};
  $('#earth-reset').onclick=()=>{if(window.Plotly&&state.scene&&!state.fallback)Plotly.relayout($('#earth-surface'),{'scene.camera':{up:{x:0,y:0,z:1},center:{x:0,y:0,z:0},eye:{x:1.35,y:1.35,z:1.05}}});};
  $('#earth-2d').onclick=()=>{state.fallback=!state.fallback;$('#earth-2d').textContent=state.fallback?'Return to 3D':'Use 2D fallback';drawSurface();};
  $('#earth-image-more').onclick=()=>{zoom=Math.min(8,zoom*1.3);transformImage();};$('#earth-image-less').onclick=()=>{zoom=Math.max(1,zoom/1.3);transformImage();};$('#earth-image-reset').onclick=resetImage;
  $('#earth-viewer').onpointerdown=e=>{if(state.view==='terrain'||!state.run)return;drag=[e.clientX-offset[0],e.clientY-offset[1]];e.currentTarget.setPointerCapture(e.pointerId);};
  $('#earth-viewer').onpointermove=e=>{if(drag){offset=[e.clientX-drag[0],e.clientY-drag[1]];transformImage();}};$('#earth-viewer').onpointerup=$('#earth-viewer').onpointercancel=()=>drag=null;
  new MutationObserver(()=>{if(state.scene&&state.view==='terrain'&&!panel.hidden)drawSurface();if(state.profile)drawProfile();}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
  new ResizeObserver(()=>{if(state.plotReady&&window.Plotly&&!panel.hidden&&!$('#earth-surface').hidden&&!state.fallback&&state.view==='terrain')Plotly.Plots.resize($('#earth-surface'));}).observe($('#earth-viewer'));

  function profilePayload(){const ids=['earth-x1','earth-y1','earth-x2','earth-y2'],values=ids.map(id=>Number($('#'+id).value));if(ids.some(id=>$('#'+id).value==='')||values.some(v=>!Number.isFinite(v)))throw Error('Choose two terrain points or enter four finite metric coordinates.');return {start:values.slice(0,2),end:values.slice(2),samples:128};}
  function pickPoints(){if(!state.scene)return;state.view='terrain';state.fallback=false;state.picking=!state.picking;state.points=[];$('#earth-pick').textContent=state.picking?'Cancel point picking':'Pick cross-section points';$('#earth-profile-pick').textContent=state.picking?'Cancel picking':'Pick on terrain';$('#earth-profile-state').textContent=state.picking?'Click a start point and an end point on the terrain surface.':'Point picking cancelled.';message(state.picking?'Select two terrain points for a cross-section.':'Terrain ready.');drawView();}
  $('#earth-pick').onclick=$('#earth-profile-pick').onclick=pickPoints;
  function bindPicking(){const plot=$('#earth-surface');if(!plot.on||plot.dataset.pickingBound)return;plot.dataset.pickingBound='true';plot.on('plotly_click',event=>{if(!state.picking||!event.points?.length)return;const p=event.points[0];if(!Number.isFinite(p.x)||!Number.isFinite(p.y))return;state.points.push([p.x,p.y]);const i=state.points.length;$('#earth-x'+i).value=p.x.toFixed(3);$('#earth-y'+i).value=p.y.toFixed(3);if(i===1){message('Start selected. Select the end point.');return;}state.picking=false;$('#earth-pick').textContent='Pick cross-section points';$('#earth-profile-pick').textContent='Pick on terrain';document.querySelector('.earth-profile').open=true;calculateProfile();});}
  async function calculateProfile(){const token=state.selection;try{if(!state.scene)throw Error('Select cached terrain first.');$('#earth-profile-state').textContent='Calculating the cross-section…';const value=await post('/api/terrain/scenes/'+state.scene.id+'/transect',profilePayload());if(!isCurrent(token))return;state.profile=value;$('#earth-profile-summary').textContent=number(value.length_m,0)+' m';$('#earth-profile-state').textContent=number(value.length_m)+' m · '+value.valid_samples+'/'+value.samples+' valid samples · 90 m nominal source. Sample density does not improve the DEM resolution.';drawProfile();message('Cross-section ready. Ask about the profile in this workspace.');}catch(error){if(isCurrent(token))$('#earth-profile-state').textContent=error.message;}}
  $('#earth-profile-calculate').onclick=calculateProfile;
  async function drawProfile(){if(!state.profile)return;const target=$('#earth-profile-chart');target.hidden=false;try{await plotly();const p=palette();await Plotly.react(target,[{type:'scatter',mode:'lines',x:state.profile.distance_m,y:state.profile.height_m,connectgaps:false,line:{color:'#d6b66a'}}],{height:215,paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{color:p.muted,size:10},margin:{l:50,r:15,t:10,b:40},xaxis:{title:{text:'Distance m'},gridcolor:p.line},yaxis:{title:{text:'DSM m'},gridcolor:p.line}},plotConfig);}catch{target.textContent=safeJSON(state.profile);}}

  function setBusy(busy){$('#earth-run-question').disabled=busy||state.contextLoading||!(state.run||state.scene);$('#earth-stop').hidden=!busy;$('#earth-stop').disabled=false;$('#earth-run').disabled=busy;$('#earth-scene').disabled=busy;$('#earth-refresh').disabled=busy||state.contextLoading;}
  function claimValue(result,field){return (result.claims||[]).find(c=>c.field===field)?.value;}
  function answerSummary(result){
    if(result.state!=='complete')return result.answer;
    const text=[],water=claimValue(result,'/summary/new_water_m2'),buildings=claimValue(result,'/summary/exposed_buildings'),roads=claimValue(result,'/summary/exposed_road_m');
    if(water!=null)text.push(number(water/10000,2)+' ha of new-water candidates in the saved run.');
    if(buildings!=null&&roads!=null)text.push(number(buildings,0)+' mapped '+(buildings===1?'building':'buildings')+' and '+number(roads)+' m of roads intersect those candidates.');
    const slope=claimValue(result,'/statistics/slope_median_deg');if(slope!=null)text.push('Median terrain slope is '+number(slope)+'°.');
    const length=claimValue(result,'/length_m');if(length!=null)text.push('The selected cross-section spans '+number(length)+' m.');
    return text.join(' ')||'Measured evidence is ready for inspection.';
  }
  function renderJob(job){
    state.job=job;const busy=!terminal.has(job.state);state.activeJob=busy?job.id:null;setBusy(busy);if(job.state==='cancelling')$('#earth-stop').disabled=true;
    const stages={queued:'Preparing the selected analysis…',running:'Checking observations and running the required tools…',cancelling:'Stopping. Any current source read has a bounded timeout.',cancelled:'Analysis stopped. No completed answer was produced.',failed:job.message,interrupted:job.message,abstained:'This question needs evidence or a method we do not have.',complete:'Analysis complete · '+job.trace.length+' '+(job.trace.length===1?'tool':'tools')+' · saved evidence'};
    feedback(stages[job.state]||job.message);
    const answer=$('#earth-answer'),result=job.result;answer.hidden=!result;if(!result)return;
    $('#earth-answer-text').textContent=answerSummary(result);const metrics=$('#earth-answer-metrics');metrics.replaceChildren();
    const featured=['/summary/exposed_buildings','/summary/exposed_road_m','/statistics/elevation_min_m','/statistics/elevation_max_m','/common_valid_dem_cells','/length_m'];
    const labels={'/summary/exposed_buildings':'Building intersections','/summary/exposed_road_m':'Road intersections','/statistics/elevation_min_m':'Minimum DSM','/statistics/elevation_max_m':'Maximum DSM','/common_valid_dem_cells':'Shared DEM centres','/length_m':'Profile length'};
    (result.claims||[]).filter(c=>featured.includes(c.field)).slice(0,4).forEach(c=>metric(metrics,labels[c.field],number(c.value,1)+' '+c.unit));
    $('#earth-answer-selection').textContent='Saved analysis: '+job.selection.run_id+' · '+job.selection.scene_id+' · '+job.selection.question;
    const sources=$('#earth-answer-sources');sources.replaceChildren();
    (result.sources||[]).forEach(s=>{const row=node('div',undefined,'earth-evidence-row');if(s.url?.startsWith('/api/')){const a=node('a',s.label+' ↗');a.href=s.url;a.target='_blank';a.rel='noopener';row.append(a);}row.append(node('small','SHA-256 '+s.sha256));sources.append(row);});
    const trace=$('#earth-answer-trace');trace.replaceChildren();job.trace.forEach(item=>{const d=node('details');d.append(node('summary',item.tool+' · '+number(item.seconds*1000)+' ms'),node('pre',safeJSON(item)));trace.append(d);});
    const limits=$('#earth-answer-limits');limits.replaceChildren(node('p',result.answer));
    if(claimValue(result,'/summary/connectivity_assessed')==='NOT_ASSESSED')limits.append(node('p','Settlement access: not assessed.'));
    const a=$('#earth-job-download');a.href='/api/investigations/'+job.id+'/download';a.download=job.id+'.json';
  }
  async function pollJob(id){const token=++state.poll;state.activeJob=id;setBusy(true);try{for(let i=0;i<120&&token===state.poll;i++){const value=await api('/api/investigations/'+id);if(token!==state.poll)return;renderJob(value);if(terminal.has(value.state)){if(!panel.hidden)$('#earth-answer').focus({preventScroll:true});return;}await new Promise(resolve=>setTimeout(resolve,500));}if(token===state.poll)feedback('Checking paused. Refresh or reload to restore the saved job status.');}catch(error){if(token===state.poll){state.activeJob=null;setBusy(false);feedback(error.message);}}}
  $('#earth-question-form').onsubmit=async event=>{event.preventDefault();if(state.activeJob||state.submitting||state.contextLoading||!(state.run||state.scene))return;state.submitting=true;try{const question=$('#earth-question').value.trim();if(question.length<3)throw Error('Enter a question about this area.');setBusy(true);$('#earth-answer').hidden=true;feedback('Preparing this area…');const payload={question,run_id:state.run?.id||null,scene_id:state.scene?.id||null};if(/transect|cross.section|profile/i.test(question))payload.profile=profilePayload();const job=await post('/api/investigations',payload);localStorage.setItem('earth-last-job',job.id);renderJob(job);pollJob(job.id);}catch(error){state.activeJob=null;setBusy(false);feedback(error.message);}finally{state.submitting=false;}};
  $('#earth-stop').onclick=async()=>{if(!state.activeJob)return;try{$('#earth-stop').disabled=true;renderJob(await post('/api/investigations/'+state.activeJob+'/cancel',{}));}catch(error){feedback(error.message);}};
  $('#earth-ask-focus').onclick=()=>{$('#earth-question').focus();$('#earth-question').scrollIntoView({block:'nearest',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});};
  document.querySelectorAll('[data-prompt]').forEach(button=>button.onclick=()=>{const prompts={overview:state.run&&state.scene?'Summarize the saved water candidates and terrain in this area.':state.scene?'Summarize the terrain elevation and slope.':'Summarize the saved water candidates.',assets:'Which roads and buildings near the water candidates need inspection?',slope:'What are the terrain elevation and slope?'};$('#earth-question').value=prompts[button.dataset.prompt];$('#earth-question').focus();});
  $('#earth-run').onchange=$('#earth-scene').onchange=selectContext;$('#earth-refresh').onclick=refresh;
  $('#earth-acquire').onclick=async()=>{if(!$('#earth-acquire-consent').checked){$('#earth-acquire-state').textContent='Approve this bounded public download first.';return;}$('#earth-acquire').disabled=true;$('#earth-acquire-state').textContent='Obtaining and measuring the public terrain…';try{const value=await post('/api/terrain/obtain',{confirmed:true});localStorage.setItem('earth-scene',value.id);$('#earth-acquire-state').textContent='Real terrain is available.';await refresh();}catch(error){$('#earth-acquire-state').textContent=error.message;}finally{$('#earth-acquire').disabled=false;}};
  if(['#terrain','#flood','#investigate'].includes(location.hash))open();
  else if(location.hash==='#evidence')$('#eval-tab').click();
})();
