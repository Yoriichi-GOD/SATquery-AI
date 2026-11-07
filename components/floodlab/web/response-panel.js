/* Additive Flood Lab response view. Saved observations stay separate from repair hypotheses. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const make = (tag, text, parent, attrs = {}) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (parent) parent.append(node);
    return node;
  };
  const root = make('section', undefined, document.querySelector('main'), {id:'response-view','aria-labelledby':'response-title'});
  root.hidden = true;
  const header = make('div', undefined, root, {class:'response-heading'});
  const copy = make('div', undefined, header);
  make('span','THE ROAD HOME / RESPONSE',copy,{class:'response-kicker'});
  make('h1', 'Routes and repairs', copy, {id:'response-title'});
  make('p', 'Inspect a mapped route, test repairs, and see what remains unknown.', copy);
  const picker = make('div', undefined, header, {class:'response-picker'});
  make('label', 'Saved analysis', picker, {for:'response-run'});
  const runPicker = make('select', undefined, picker, {id:'response-run'});
  const loadButton = make('button', 'Load response evidence', picker, {id:'response-load',type:'button'});
  const status = make('p', 'Choose a saved analysis, then load its response evidence.', root, {id:'response-status',role:'status','aria-live':'polite'});
  const results = make('div', undefined, root, {id:'response-results'}); results.hidden = true;
  const boundary = make('p', undefined, results, {class:'response-boundary',id:'response-boundary'});
  const grid = make('div', undefined, results, {class:'response-grid'});
  const left = make('div', undefined, grid);
  const metricList = make('dl', undefined, left, {class:'response-counts'});
  const routeHeader = make('div', undefined, left, {class:'response-route-heading'});
  make('label', 'Route view', routeHeader, {for:'response-mode'});
  const mode = make('select', undefined, routeHeader, {id:'response-mode'});
  for (const [value, label] of [['before','Before · all mapped roads'],['optimistic','After · unknown roads assumed open'],['conservative','After · unknown roads excluded']]) {
    make('option', label, mode, {value});
  }
  const map = document.createElementNS('http://www.w3.org/2000/svg','svg');
  map.id = 'response-map'; map.setAttribute('viewBox','0 0 720 360'); map.setAttribute('role','img');
  map.setAttribute('aria-label','Mapped network route schematic; not a navigation map'); left.append(map);
  const mapNote = make('p', undefined, left, {id:'response-map-note',class:'muted'});
  const tableBox = make('div', undefined, left, {class:'response-table-scroll'});
  const table = make('table', undefined, tableBox);
  const head = make('thead', undefined, table); const hr = make('tr', undefined, head);
  for (const title of ['Settlement','Route evidence','Before / scenario']) make('th', title, hr, {scope:'col'});
  const body = make('tbody', undefined, table, {id:'response-settlements'});
  const right = make('div', undefined, grid, {class:'response-actions'});
  make('h2', 'Test a repair scenario', right);
  make('p', 'Reopen selected candidate road sections in the model. Unobserved sections remain unknown.', right);
  const repairList = make('div', undefined, right, {id:'response-repairs'});
  const manual = make('details',undefined,right,{class:'response-manual'});
  make('summary','Choose road sections manually',manual);
  make('label', 'Candidate roads · select one or several', manual, {for:'response-ways'});
  const ways = make('select', undefined, manual, {id:'response-ways',multiple:'',size:'5'});
  const applyButton = make('button', 'Test selected repairs', manual, {type:'button',id:'response-apply'});
  const resetButton = make('button', 'Reset to observed candidates', right, {type:'button',id:'response-reset',class:'response-secondary'});
  const exports = make('div', undefined, right, {id:'response-exports',class:'response-exports'});
  const details = make('details', undefined, results, {class:'response-evidence'});
  make('summary', 'Sources, assumptions and search limits', details);
  const evidence = make('div', undefined, details, {id:'response-evidence-content'});
  const nav = document.querySelector('header nav');
  const responseButton = make('button', 'Response', null, {id:'response-tab',type:'button'});
  nav.insertBefore(responseButton,$('eval-tab'));
  responseButton.addEventListener('click', () => {
    root.hidden = false; $('lab').hidden = true; $('evaluation').hidden = true;
    document.querySelector('.intro').hidden = true;
    $('lab-tab').classList.remove('active'); $('eval-tab').classList.remove('active'); responseButton.classList.add('active');
    history.replaceState(null,'','#response');
  });
  for (const id of ['lab-tab','eval-tab']) $(id).addEventListener('click',() => {
    root.hidden = true; responseButton.classList.remove('active'); history.replaceState(null,'',id==='eval-tab'?'#evidence':'#workspace');
  });
  const globalRun = $('run'); let value = null, routes = null, revision = 0, controller = null;
  function clear() {
    revision++; if (controller) controller.abort(); value = null; routes = null;
    results.hidden = true; map.replaceChildren(); exports.replaceChildren(); body.replaceChildren(); repairList.replaceChildren();
    loadButton.disabled = false; status.textContent = 'Load response evidence for '+(globalRun.value || 'the selected analysis')+'.';
  }
  function sync() {
    const selected = globalRun.value; runPicker.replaceChildren();
    for (const option of globalRun.options) make('option', option.textContent, runPicker, {value:option.value});
    runPicker.value = selected;
  }
  new MutationObserver(sync).observe(globalRun,{childList:true}); sync();
  globalRun.addEventListener('change',() => {sync(); clear();});
  runPicker.addEventListener('change',() => {globalRun.value = runPicker.value; globalRun.dispatchEvent(new Event('change',{bubbles:true}));});
  const distance = route => route ? (route.length_m/1000).toFixed(2)+' km' : 'No mapped route';
  const labels = {MAPPED_ROUTE_SUPPORTED:'Mapped route supported',UNKNOWN_UNOBSERVED_ROUTE:'Unknown observations on route',UNKNOWN_AOI_BOUNDARY:'Unknown beyond area boundary',NOT_ASSESSED_OFF_NETWORK:'Not assessed · off network',NOT_ASSESSED_NO_HUBS:'Not assessed · no service hubs',DISCONNECTED_IN_MAPPED_BASELINE:'No route in mapped baseline',NO_MAPPED_ROUTE_IN_CLOSURE_SCENARIO:'No mapped route in closure scenario'};
  async function request(repairs) {
    const selected = globalRun.value; if (!selected) return;
    const ticket = ++revision; if (controller) controller.abort(); controller = new AbortController();
    loadButton.disabled = true; results.hidden = true; status.textContent = 'Checking the frozen road network and repair scenarios…';
    try {
      const url = '/api/response/runs/'+encodeURIComponent(selected);
      const response = await fetch(repairs===null ? url : url+'/scenarios',repairs===null ? {signal:controller.signal} : {
        method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({restore_way_ids:repairs}),signal:controller.signal});
      if (!response.ok) {const error = await response.json(); throw Error(error.detail || 'Response calculation unavailable');}
      const data = await response.json();
      const artifact = data.artifacts.find(item => item.name==='routes.geojson');
      if (!artifact || !artifact.url.startsWith('/api/response/')) throw Error('Route evidence unavailable');
      const geometryResponse = await fetch(artifact.url,{signal:controller.signal});
      if (!geometryResponse.ok) throw Error('Verified route export unavailable');
      const geometry = await geometryResponse.json();
      if (ticket!==revision || data.source.run_id!==globalRun.value) return;
      value = data; routes = geometry;
      mode.value = data.restore_way_ids.length ? 'optimistic' : 'before';
      render(); status.textContent = data.restore_way_ids.length ? 'Repair scenario loaded · '+data.restore_way_ids.length+' road sections reopened in the model. Candidate observations remain unchanged.' : 'Saved network evidence loaded.';
    } catch (error) {
      if (ticket===revision && error.name!=='AbortError') {status.textContent = error.message+'. Try loading again.'; value = null; routes = null; results.hidden = true;}
    } finally {if (ticket===revision) loadButton.disabled = false;}
  }
  function render() {
    results.hidden = false; metricList.replaceChildren(); body.replaceChildren(); ways.replaceChildren(); repairList.replaceChildren(); exports.replaceChildren(); evidence.replaceChildren();
    const assessed = value.state==='COMPLETE_SCENARIO';
    boundary.textContent = assessed ? 'Network scenario only. Candidate intersections are assumed closures; these routes do not establish actual access or safety.' : 'Access not assessed: this saved graph has no usable service destinations. Missing evidence is not zero impact.';
    for (const [name,key] of [['Mapped routes without unknown sections','observation_supported_mapped_routes'],['Possible routes through unknown observations','possible_routes_through_unknown'],['Places with unknown boundary access','unknown_aoi_boundary'],['Places not assessed','not_assessed']]) {
      const pair = make('div', undefined, metricList); make('dt',name,pair); make('dd',assessed ? String(value.summary[key]) : 'Not assessed',pair);
    }
    for (const row of value.rows) {
      const tr = make('tr', undefined, body); make('td',row.name,tr); make('td',labels[row.status] || row.status,tr);
      make('td',row.connected_before===null ? 'Not assessed' : distance(row.routes?.before)+' / '+distance(row.routes?.[mode.value]),tr);
    }
    for (const id of value.candidate_way_ids) {const option=make('option',id,ways,{value:id}); option.selected=value.restore_way_ids.includes(id);}
    applyButton.disabled=!assessed || !value.candidate_way_ids.length;
    resetButton.disabled=!assessed;
    make('h3','Ranked scenarios tested',repairList);
    const search=value.repair_search;
    if (!search.rankings.length) make('p',search.state.startsWith('NOT_ASSESSED') ? 'Repair ranking is not assessed for this saved evidence.' : 'None of the tested repairs creates an additional mapped route. This is not a complete search of every possible repair combination.',repairList);
    for (const entry of search.rankings.slice(0,8)) {
      const row=make('div',undefined,repairList,{class:'response-repair'});
      make('p',entry.restore_way_ids.length+' road sections · '+entry.possible_gain+' newly possible mapped route(s), '+entry.supported_gain+' without unknown sections.',row);
      const button=make('button','Test '+entry.restore_way_ids.length+'-road scenario',row,{type:'button'});
      button.addEventListener('click',()=>request([...value.restore_way_ids,...entry.restore_way_ids]));
    }
    const labelsByName={'bundle.zip':'Download field kit','routes.geojson':'Route GeoJSON','fieldkit.kml':'Google Earth KML','alert-en.txt':'English alert draft','alert-ne.txt':'नेपाली alert draft','response.json':'Scenario calculations','evidence.json':'Source hashes','facts.json':'Facts ledger'};
    for (const item of value.artifacts) if (labelsByName[item.name] && item.url.startsWith('/api/response/')) {
      make('a',labelsByName[item.name],exports,{href:item.url,download:item.name});
    }
    make('p','Event: '+value.source.event_time+' · Historical infrastructure: '+value.source.infrastructure_snapshot,evidence);
    make('p',value.source.destination_basis,evidence); make('p',value.uncertainty_method,evidence);
    make('p','Tested '+(search.scenarios_evaluated??'no')+' scenario(s). '+(search.search_complete?'Declared search completed.':'Search is incomplete. ')+' '+(search.bundle_search || ''),evidence);
    make('p','Assumed repairs: '+(value.restore_way_ids.join(', ') || 'none')+'. Unknown observations are not cleared by a repair.',evidence);
    make('p','Clear means satellite-covered without a qualifying candidate intersection. It does not establish a physically open road.',evidence);
    make('p','Native Nepali wording and field suitability have not been independently reviewed.',evidence);
    for (const row of value.rows) {make('h3',row.name,evidence); const list=make('ul',undefined,evidence); for (const note of row.quality) make('li',note,list);}
    make('pre',JSON.stringify(value.source.files,null,2),evidence); draw();
  }
  function draw() {
    map.replaceChildren(); if (!value || !routes) return;
    const selected=routes.features.filter(f=>f.geometry && (f.properties.kind==='network-snap-point' || f.properties.mode===mode.value));
    const points=selected.flatMap(f=>f.geometry.type==='Point' ? [f.geometry.coordinates] : f.geometry.coordinates);
    if (!points.length) {mapNote.textContent='No georeferenced mapped route or snap point is available.'; return;}
    let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;
    for (const p of points) {x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1]);}
    const cosine=Math.cos((y0+y1)/2*Math.PI/180); const scale=Math.min(640/Math.max((x1-x0)*cosine,.00001),280/Math.max(y1-y0,.00001));
    const xy=p=>[40+(p[0]-x0)*cosine*scale,320-(p[1]-y0)*scale];
    for (const f of selected) {
      let node;
      if (f.geometry.type==='Point') {node=document.createElementNS(map.namespaceURI,'circle'); const p=xy(f.geometry.coordinates);node.setAttribute('cx',p[0]);node.setAttribute('cy',p[1]);node.setAttribute('r','5');}
      else {node=document.createElementNS(map.namespaceURI,'path');node.setAttribute('d',f.geometry.coordinates.map((p,i)=>(i?'L':'M')+xy(p).join(',')).join(' '));}
      node.setAttribute('class',f.geometry.type==='Point' ? 'response-snap' : 'response-path response-'+mode.value);
      const title=document.createElementNS(map.namespaceURI,'title');title.textContent=f.id;node.append(title);map.append(node);
    }
    const pathCount=selected.filter(f=>f.properties.kind==='response-route').length;
    mapNote.textContent=(value.state!=='COMPLETE_SCENARIO' ? 'Routes not assessed. ' : pathCount ? 'Mapped route schematic. ' : 'No mapped route in this view. ')+'Points are network snaps, not surveyed settlement locations. Unknown roads may hide closure; this is not navigation.';
  }
  loadButton.addEventListener('click',()=>request(null)); resetButton.addEventListener('click',()=>request([]));
  applyButton.addEventListener('click',()=>request([...ways.selectedOptions].map(o=>o.value)));
  mode.addEventListener('change',()=>{if (value) render();});
  if (location.hash==='#response') responseButton.click();
})();
