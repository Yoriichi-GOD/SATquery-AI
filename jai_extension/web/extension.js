/* Native panels added to the approved prior SATQuery page; no iframe. */
(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const make = (tag, text, cls) => {const el = document.createElement(tag); if(text !== undefined) el.textContent = text; if(cls) el.className = cls; return el;};
  const main = $('main'), nav = $('header nav');
  if(!main || !nav) return;
  const floodTab = make('button', 'Flood Intelligence'); floodTab.id = 'jai-flood-tab'; nav.append(floodTab);
  const panel = make('section', undefined, 'jai-panel'); panel.id = 'jai-flood'; panel.hidden = true;
  panel.innerHTML = `<div class="jai-heading"><div><span class="eyebrow">EARTH INVESTIGATION · SAVED OBSERVATIONS</span><h1>Flood Intelligence</h1><p>Inspect recorded satellite water candidates and their source evidence.</p></div><span class="jai-badge">SAVED EVIDENCE</span></div>
  <p id="jai-message" role="status" aria-live="polite">Checking the local Flood Lab…</p>
  <div class="jai-layout"><aside class="jai-card jai-runs"><div class="jai-row"><h2>Saved analyses</h2><button id="jai-refresh" type="button">Refresh</button></div><p class="muted">Recorded results, with acquisition dates. Select a run to verify its summary.</p><div id="jai-run-list"></div></aside>
  <div class="jai-center"><div class="jai-card"><div class="jai-row"><h2 id="jai-run-title">Select a saved analysis</h2><span id="jai-population" class="jai-badge">NO RUN SELECTED</span></div><div id="jai-metrics" class="jai-metrics"></div><div class="jai-row jai-image-controls" role="group" aria-label="Recorded image view"><button data-jai-image="pre.png">Before SAR</button><button data-jai-image="post.png">After SAR</button><button data-jai-image="candidate">Water candidates</button><button id="jai-minus" aria-label="Zoom out">−</button><button id="jai-plus" aria-label="Zoom in">+</button><button id="jai-reset">Reset view</button></div><div id="jai-image-frame" class="jai-image-frame"><img id="jai-image" alt="Select a run to inspect recorded evidence" hidden draggable="false"></div><p id="jai-image-note" class="muted">Radar previews show recorded processing, not optical photographs.</p><p class="jai-legend"><span>■ Water at both dates</span><span>■ New-water candidate</span><span>■ Invalid / outside valid data</span></p></div>
  <div class="jai-card"><h2>Recorded feature intersections</h2><p>Overlap is a review cue. It does not establish damage or road closure.</p><div id="jai-exposure" class="jai-table-wrap"></div></div></div>
  <aside class="jai-card jai-evidence"><h2>Source & uncertainty</h2><div id="jai-provenance"></div><h3>Evidence downloads</h3><div id="jai-downloads"></div><h3>Interpretation limits</h3><ul id="jai-limits"></ul></aside></div>`;
  main.append(panel);
  let run = null, epoch = 0, controller = null, zoom = 1, offset = [0,0], drag = null, loaded = false;
  const message = text => {$('#jai-message').textContent = text;};
  function hideOriginal(){ $('#lab').hidden = true; $('#evaluation').hidden = true; $('main > .intro').hidden = true; $('#lab-tab').classList.remove('active'); $('#eval-tab').classList.remove('active'); }
  floodTab.onclick = () => {hideOriginal(); panel.hidden = false; floodTab.classList.add('active'); if(!loaded) refresh();};
  for(const id of ['lab-tab','eval-tab']) $('#'+id).addEventListener('click', () => {panel.hidden = true; floodTab.classList.remove('active'); $('main > .intro').hidden = false;});
  async function api(path, signal){const response = await fetch('/api/flood'+path, {signal, cache:'no-store'}); let data; try{data = await response.json();}catch{throw Error('The service returned an unreadable response.');}if(!response.ok)throw Error(data.detail || 'Saved evidence unavailable ('+response.status+').');return data;}
  function clear(){run = null; $('#jai-run-title').textContent = 'Select a saved analysis'; $('#jai-population').textContent = 'NO RUN SELECTED'; for(const id of ['jai-metrics','jai-exposure','jai-provenance','jai-downloads','jai-limits']) $('#'+id).replaceChildren(); $('#jai-image').hidden = true; $('#jai-image').removeAttribute('src');}
  async function refresh(){
    controller?.abort(); controller = new AbortController(); const token = ++epoch; clear(); loaded = true; $('#jai-run-list').replaceChildren(); message('Connecting to Flood Lab on this computer…');
    try{const listing = await api('/runs',controller.signal); if(token !== epoch)return;
      if(!listing.runs.length){message('No saved analyses are available. Prepare a run in Flood Lab, then refresh.'); return;}
      for(const item of listing.runs){const b = make('button',undefined,'jai-run'); b.dataset.runId = item.id; b.append(make('strong',item.event_name),make('small',item.id),make('small',item.population.replaceAll('_',' '))); b.onclick=()=>select(item.id); $('#jai-run-list').append(b);}
      message(listing.runs.length+' saved analyses available'+(listing.rejected_metadata ? '; '+listing.rejected_metadata+' invalid records withheld.' : '.'));
      const preferred=localStorage.getItem('jai-last-flood-run');const first=listing.runs.find(x=>x.id===preferred)||listing.runs.find(x=>x.id==='event-fe47db331390')||listing.runs.find(x=>x.population==='FROZEN_REAL_OBSERVATION')||listing.runs[0]; await select(first.id);
    }catch(e){if(e.name!=='AbortError')message(e.message);}
  }
  async function select(id){
    controller?.abort(); controller = new AbortController(); const token=++epoch; clear(); message('Verifying the saved summary and loading evidence…');
    document.querySelectorAll('.jai-run').forEach(b=>b.classList.toggle('active',b.dataset.runId===id));
    try{
      const [detail, exposure, grid] = await Promise.all([api('/runs/'+id,controller.signal),api('/runs/'+id+'/exposure',controller.signal),api('/runs/'+id+'/grid',controller.signal)]);
      if(token!==epoch)return; run=detail;localStorage.setItem('jai-last-flood-run',id);window.dispatchEvent(new CustomEvent('jai:flood-selected',{detail:{id}}));$('#jai-run-title').textContent=detail.event_name;$('#jai-population').textContent=detail.population.replaceAll('_',' ');
      const s=detail.summary;const fmt=(v,d=0)=>v==null?'Not available':Number(v).toLocaleString(undefined,{maximumFractionDigits:d});
      for(const [label,value] of [['Candidate area',fmt(s.new_water_m2/10000,2)+' ha'],['Intersected buildings',fmt(s.exposed_buildings)],['Intersected roads',fmt(s.exposed_road_m,1)+' m'],['Valid paired pixels',fmt(s.valid_pixels)],['Settlement access',s.connectivity_status.replaceAll('_',' ')]]){const box=make('div');box.append(make('small',label),make('strong',value));$('#jai-metrics').append(box);}
      const p=detail.provenance;for(const [label,value] of [['Event UTC',p.event_time],['SAR before UTC',p.inputs[0].datetime],['SAR after UTC',p.inputs[1].datetime],['Historical OSM UTC',p.osm_snapshot],['Raster grid',grid.width+' × '+grid.height],['CRS',grid.crs],['Grid pixel size',grid.pixel_size.join(' × ')+' CRS units'],['Method',p.method],['Thresholds',JSON.stringify(p.analysis)],['Integrity',detail.integrity],['Freeze SHA-256',detail.freeze_sha256],['Trust boundary',detail.integrity_basis]]){const el=make('div',undefined,'jai-source');el.append(make('small',label),make('p',value||'Not recorded'));$('#jai-provenance').append(el);}
      for(const input of p.inputs){const info=make('details');info.append(make('summary',input.source+' source acquisition'),make('pre',JSON.stringify(input,null,2)));$('#jai-provenance').append(info);}
      for(const item of detail.artifacts){const a=make('a',item.name);a.href=item.url;a.title='Verified against saved SHA-256 on download: '+item.sha256;a.download=item.name;$('#jai-downloads').append(a);}
      for(const text of detail.limitations)$('#jai-limits').append(make('li',text));
      const rows=exposure.rows.filter(x=>x.status==='exposed'||x.status==='unknown').sort((a,b)=>b.exposed-a.exposed);const table=make('table'),thead=make('thead'),tr=make('tr');for(const h of ['Feature','Kind','Intersected','Observed / total','Status'])tr.append(make('th',h));thead.append(tr);table.append(thead);const body=make('tbody');for(const row of rows.slice(0,60)){const r=make('tr');for(const val of [row.id,row.kind,fmt(row.exposed,1)+' '+row.unit,fmt(row.observed,1)+' / '+fmt(row.total,1)+' '+row.unit,row.status])r.append(make('td',val));body.append(r);}table.append(body);$('#jai-exposure').append(make('p',rows.length+' exposed/unknown rows from '+exposure.rows.length+' recorded features; showing first '+Math.min(60,rows.length)+'. Download CSV for the complete table.'),table);
      showImage('candidate'); message('SAVED · Summary and manifest verified. Each download is checked against the freeze map. This is a historical observation, not a new acquisition.');
    }catch(e){if(token!==epoch)return;clear();if(e.name!=='AbortError')message(e.message);}
  }
  function transform(){ $('#jai-image').style.transform=`translate(${offset[0]}px,${offset[1]}px) scale(${zoom})`; }
  function reset(){zoom=1;offset=[0,0];transform();}
  function showImage(name){if(!run)return;reset();const id=run.id;const img=$('#jai-image');img.hidden=true;img.onload=()=>{if(run?.id===id)img.hidden=false;};img.onerror=()=>{img.hidden=true;message('This evidence image is unavailable or failed its integrity check.');};img.src='/api/flood/runs/'+id+(name==='candidate'?'/candidate.png':'/artifact/'+name);img.alt=name==='candidate'?'Saved categorical water candidate map':'Recorded '+(name==='pre.png'?'before':'after')+' Sentinel-1 radar preview';$('#jai-image-note').textContent=name==='candidate'?'Derived display of verified prediction.tif. Blue: water at both dates; gold: new-water candidate; gray: invalid; dark: no candidate under this heuristic. No spatial alignment with an independent reference is claimed.':'Recorded '+(name==='pre.png'?'before':'after')+' SAR preview. Drag to pan; use + / − to zoom. Preview scaling is inherited from Flood Lab.';document.querySelectorAll('[data-jai-image]').forEach(b=>b.classList.toggle('active',b.dataset.jaiImage===name));}
  document.querySelectorAll('[data-jai-image]').forEach(b=>b.onclick=()=>showImage(b.dataset.jaiImage));
  $('#jai-refresh').onclick=refresh;$('#jai-plus').onclick=()=>{zoom=Math.min(8,zoom*1.3);transform();};$('#jai-minus').onclick=()=>{zoom=Math.max(1,zoom/1.3);transform();};$('#jai-reset').onclick=reset;
  const frame=$('#jai-image-frame');frame.onpointerdown=e=>{if(!run)return;drag=[e.clientX-offset[0],e.clientY-offset[1]];frame.setPointerCapture(e.pointerId);};frame.onpointermove=e=>{if(drag){offset=[e.clientX-drag[0],e.clientY-drag[1]];transform();}};frame.onpointerup=frame.onpointercancel=()=>drag=null;
  if(location.hash==='#flood')floodTab.click();
})();
