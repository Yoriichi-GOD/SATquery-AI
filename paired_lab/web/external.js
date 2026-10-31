/* External data is inspected privately before any specialist is offered. */
(async () => {
  'use strict';
  try{const status=await fetch('/api/status',{cache:'no-store'}).then(r=>r.json());if(status.external_dataset_api!==true)return;}catch{return;}
  const $=s=>document.querySelector(s), make=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
  const state={dataset:null,report:null,files:[],job:null,upload:null,protocol:null,selection:[],lastPrediction:null,predictionInputs:[],lastJob:null,phase:"",submitting:false,poll:0,contextVersion:0};
  const tab=make('button','Datasets');tab.id='external-tab';$('header nav').append(tab);
  const panel=make('section');panel.id='external';panel.hidden=true;
  panel.innerHTML=`<div class="intro"><div><span class="eyebrow">EXTERNAL DATA · INDEPENDENT CHECKS</span><h1>External dataset evaluation.</h1></div><p>Inspect the inputs. Verify the contract. Measure against labels.</p></div>
  <div class="ext-layout"><div class="ext-card"><span class="eyebrow">1 · REGISTER & INSPECT</span><h2>Your dataset.</h2><label for="ext-saved">Private datasets</label><div class="ext-row"><select id="ext-saved"><option value="">New dataset</option></select><button id="ext-refresh">Refresh</button></div><label for="ext-name">Dataset name</label><input id="ext-name" maxlength="120" placeholder="Judge-supplied evaluation dataset"><div class="ext-row"><label class="ext-file-button">Select files<input id="ext-files" type="file" multiple accept=".tif,.tiff,.zip,.json,.csv,.xml,.txt,.md"></label><label class="ext-file-button">Select folder<input id="ext-folder" type="file" webkitdirectory multiple></label></div><p class="muted">TIFFs, validated ZIPs and companion metadata. Up to the configured 4 GiB dataset cap; uploads use 8 MiB chunks. Model input limits remain separate.</p><div id="ext-pending"></div><div class="ext-row"><button class="primary" id="ext-import" disabled>Import & inspect</button><button id="ext-inspect" disabled>Inspect stored files</button><button id="ext-stop" hidden>Stop</button></div><progress id="ext-progress" max="100" value="0" hidden></progress><p id="ext-state" role="status" aria-live="polite">Select files or an existing private dataset.</p><div id="ext-inventory"></div><details><summary>Source inventory & metadata</summary><pre id="ext-metadata"></pre><p>Headers and declared sensor names do not independently authenticate pixels. Preview stretches are display-only; original bytes are retained.</p></details></div>
  <div class="ext-card"><span class="eyebrow">2 · COMPATIBILITY & EXECUTION</span><h2>Use the right specialist.</h2><p class="muted">Select at most two input TIFFs in the inventory. Every mismatch stays inspectable; opening a TIFF is not model compatibility.</p><details><summary>CDVQA question & pairing declaration</summary><label for="ext-question">Exact supported CDVQA question</label><textarea id="ext-question" maxlength="500" rows="2"></textarea><label class="ext-check"><input type="checkbox" id="ext-aligned">Same area, already aligned, before then after (user declaration).</label></details><button id="ext-preflight" disabled>Run compatibility preflight</button><div id="ext-contracts"></div><div class="ext-links" id="ext-report-downloads" hidden><a id="ext-report-json">Compatibility JSON ↓</a><a id="ext-report-csv">Compatibility CSV ↓</a></div><label for="ext-specialist">Eligible specialist</label><select id="ext-specialist" disabled><option value="">Inspect data first</option></select><details><summary>Explicit analytical thresholds</summary><label for="ext-threshold">NDVI threshold</label><input id="ext-threshold" type="number" min="-1" max="1" step="0.05" value="0.5"><label for="ext-water-threshold">NDWI threshold</label><input id="ext-water-threshold" type="number" min="-1" max="1" step="0.05" value="0"></details><button class="primary" id="ext-analyze" disabled>Run selected specialist</button><div id="ext-result" hidden></div></div>
  <div class="ext-card ext-evaluation"><span class="eyebrow">3 · INDEPENDENT EVALUATION</span><h2>Reference labels, then a score.</h2><p>Assign label files the <b>reference</b> role. A supplied protocol must declare dataset revision, evaluation population, class semantics, mappings, ignore values, licence and reference provenance before scoring. No labels means no accuracy, IoU or F1.</p><div class="ext-eval-grid"><div><label for="ext-reference">Independent reference</label><select id="ext-reference"><option value="">No compatible ground truth provided</option></select><label class="ext-file-button">Load evaluation protocol JSON<input id="ext-protocol" type="file" accept=".json"></label><p id="ext-protocol-state" class="muted">No protocol loaded. Prediction-only execution remains available.</p><details><summary>Protocol and current dataset revision</summary><pre id="ext-protocol-preview"></pre></details></div><div><label for="ext-prediction">Imported predictions (optional)</label><select id="ext-prediction"><option value="">Use the last completed model prediction</option></select><button id="ext-evaluate" disabled>Evaluate unchanged predictions</button><p class="muted">This creates a new immutable evaluation run. Labels are never used to tune the model or its thresholds.</p><div id="ext-evidence"></div></div></div></div></div>`;
  $('main').append(panel);
  const picker=window.customPicker;if(typeof picker==='function')window.customPicker=function(select){if(select.closest('#external'))return;return picker(select);};
  function open(){document.querySelectorAll('main > section').forEach(n=>n.hidden=n!==panel);$('main > .intro').hidden=true;document.querySelectorAll('header nav > button').forEach(n=>n.classList.toggle('active',n===tab));history.replaceState(null,'',location.pathname+location.search+'#datasets');refresh();}
  tab.onclick=open;$('header nav').addEventListener('click',event=>{if(event.target.closest('button')?.id!=='external-tab')panel.hidden=true;});
  function message(value){$('#ext-state').textContent=value;}
  const cacheKey='external-workspace-v2';
  function cache(){try{return JSON.parse(localStorage.getItem(cacheKey)||'{}');}catch{return {};}}
  function remember(){
    if(!state.dataset)return;
    const saved=cache();saved[state.dataset.id]={inputs:selected(),reference:$('#ext-reference').value,
      prediction:$('#ext-prediction').value,protocol:state.protocol,lastPrediction:state.lastPrediction,
      predictionInputs:state.predictionInputs,lastJob:state.lastJob,question:$('#ext-question').value,
      aligned:$('#ext-aligned').checked,threshold:$('#ext-threshold').value,waterThreshold:$('#ext-water-threshold').value};
    try{localStorage.setItem(cacheKey,JSON.stringify(saved));}catch{/* A full browser store must never change an analysis. */}
  }
  function selected(){return [...document.querySelectorAll('.ext-input-select:checked')].map(n=>n.value);}
  function sameInputs(a,b){return Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>v===b[i]);}
  function busy(){return Boolean(state.phase||state.job||state.upload||state.submitting);}
  function controls(){
    const locked=busy();
    document.querySelectorAll('#external input,#external select,#external textarea,#external button').forEach(n=>n.disabled=locked);
    document.querySelectorAll('.ext-input-select').forEach(n=>n.disabled=locked||n.dataset.eligible!=='true');
    $('#ext-stop').hidden=!(state.job||state.upload);$('#ext-stop').disabled=false;
    if(locked)return;
    $('#ext-import').disabled=!state.files.length;
    $('#ext-inspect').disabled=!state.dataset||!state.dataset.files.length||state.dataset.files.some(f=>!['STORED','INSPECTED','REJECTED'].includes(f.state));
    $('#ext-preflight').disabled=!state.dataset?.revision;
    $('#ext-specialist').disabled=!state.report?.eligible_specialists.length;
    $('#ext-analyze').disabled=!state.report?.eligible_specialists.includes($('#ext-specialist').value);
    const compatibleProtocol=state.protocol&&state.protocol.dataset_revision===state.dataset?.revision;
    const reusable=state.lastPrediction&&sameInputs(state.predictionInputs,selected());
    $('#ext-evaluate').disabled=!state.dataset?.revision||!$('#ext-reference').value||!compatibleProtocol||!($('#ext-prediction').value||reusable);
  }
  async function api(path,options={}){
    const response=await fetch('/api/datasets'+path,{cache:'no-store',...options});let value;
    try{value=await response.json();}catch{throw Error('Unreadable local-service response.');}
    if(!response.ok)throw Error((value.code||'REQUEST_FAILED')+' · '+value.detail);
    return value;
  }
  const post=(path,value={})=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
  function clearAnalysis(){
    state.report=null;$('#ext-result').hidden=true;$('#ext-result').replaceChildren();
    $('#ext-evidence').replaceChildren();$('#ext-contracts').replaceChildren();$('#ext-report-downloads').hidden=true;
    $('#ext-specialist').replaceChildren(new Option('Run preflight',''));
  }
  function protocolDisplay(){
    const matches=state.protocol?.dataset_revision===state.dataset?.revision;
    $('#ext-protocol-state').textContent=!state.protocol?'No protocol loaded. Prediction-only execution remains available.':
      matches?'Protocol loaded for this exact dataset revision; it will be frozen in the next immutable run.':'Protocol revision differs. Inspect the current revision and load its explicit protocol before scoring.';
    $('#ext-protocol-preview').textContent='Current dataset revision: '+(state.dataset?.revision||'Inspect files first')+'\n\n'+(state.protocol?JSON.stringify(state.protocol,null,2):'No protocol loaded.');
  }
  async function load(id){
    remember();const token=++state.contextVersion;clearAnalysis();state.dataset=null;controls();
    const value=await api('/'+id);if(token!==state.contextVersion)return;
    state.dataset=value;localStorage.setItem('external-dataset',id);const settings=cache()[id]||{};
    state.selection=settings.inputs||[];state.protocol=settings.protocol||null;
    state.lastPrediction=settings.lastPrediction||null;state.predictionInputs=settings.predictionInputs||[];state.lastJob=settings.lastJob||null;
    $('#ext-question').value=settings.question||'';$('#ext-aligned').checked=settings.aligned===true;
    $('#ext-threshold').value=settings.threshold??'.5';$('#ext-water-threshold').value=settings.waterThreshold??'0';
    $('#ext-name').value=value.name;$('#ext-metadata').textContent=JSON.stringify(value,null,2);
    inventory(settings);protocolDisplay();
  }
  async function refresh(){
    if(busy())return;remember();state.phase='refresh';controls();
    try{
      const result=await api('');const current=state.dataset?.id||localStorage.getItem('external-dataset')||'';
      const select=$('#ext-saved');select.replaceChildren(new Option('New dataset',''));
      result.datasets.forEach(d=>select.append(new Option(d.name+' · '+d.state,d.id)));
      select.value=result.datasets.some(d=>d.id===current)?current:'';
      if(select.value)await load(select.value);
      if(result.active_job){
        const running=await api('/jobs/'+result.active_job);
        if(state.dataset?.id!==running.dataset_id)await load(running.dataset_id);
        state.phase='';poll(running.id);return;
      }
      const previous=state.lastJob||localStorage.getItem('external-job');
      if(previous&&state.dataset){const saved=await api('/jobs/'+previous);if(saved.dataset_id===state.dataset.id&&saved.operation!=='inspect')resultView(saved);}
      message(state.dataset?'Stored observations ready. Run preflight for the selected input files.':'Select files or an existing private dataset.');
    }catch(error){message(error.message);}finally{state.phase='';controls();}
  }
  function inventory(settings={}){
    const root=$('#ext-inventory');root.replaceChildren(make('h3','Dataset inventory'));
    $('#ext-reference').replaceChildren(new Option('No compatible ground truth provided',''));
    $('#ext-prediction').replaceChildren(new Option('Use the last completed model prediction',''));
    let defaults=0;
    state.dataset.files.forEach(file=>{
      const row=make('div');row.className='ext-inventory-row';
      const box=make('input');box.type='checkbox';box.value=file.id;box.className='ext-input-select';
      box.setAttribute('aria-label','Use '+file.name+' for analysis');
      box.dataset.eligible=String(file.role==='input'&&file.state==='INSPECTED'&&Boolean(file.raster));
      box.checked=box.dataset.eligible==='true'&&(state.selection.length?state.selection.includes(file.id):defaults++<2);
      box.onchange=()=>{state.selection=selected();clearAnalysis();remember();controls();};
      const text=make('div');text.append(make('strong',file.name),make('small',(file.bytes/1024**2).toFixed(2)+' MiB · '+file.state+
        (file.raster?' · '+file.raster.width+'×'+file.raster.height+' · '+file.raster.count+' bands':'')));
      if(file.error)text.append(make('p',file.error.code+' · '+file.error.message));
      const role=make('select');role.setAttribute('aria-label','Role for '+file.name);
      ['input','reference','prediction','metadata'].forEach(v=>role.append(new Option(v,v)));role.value=file.role;
      role.onchange=async()=>{
        remember();state.phase='role';controls();
        try{await post('/'+state.dataset.id+'/files/'+file.id+'/role',{role:role.value});await load(state.dataset.id);message('Role changed. Inspect again to freeze the updated dataset revision.');}
        catch(error){message(error.message);}finally{state.phase='';controls();}
      };
      row.append(box,text,role);root.append(row);
      if(file.role==='reference'||file.role==='prediction')$('#ext-'+file.role).append(new Option(file.name,file.id));
      if(file.raster){
        const details=make('details');details.append(make('summary','Preview '+file.name));
        const datasetId=state.dataset.id;
        details.addEventListener('toggle',()=>{if(details.open&&!details.querySelector('img')){
          const image=make('img');image.alt='Bounded native-pixel display preview: '+file.name;
          image.src='/api/datasets/'+datasetId+'/files/'+file.id+'/preview';details.append(image,make('p',file.raster.preview));
        }});root.append(details);
      }
    });
    for(const name of ['reference','prediction'])if([...$('#ext-'+name).options].some(o=>o.value===settings[name]))$('#ext-'+name).value=settings[name];
    state.selection=selected();
  }
  function pending(files){
    state.files=[...files].map(file=>({file,role:['.tif','.tiff','.zip'].some(s=>file.name.toLowerCase().endsWith(s))?'input':'metadata'}));
    const list=$('#ext-pending');list.replaceChildren();
    state.files.forEach(item=>{const row=make('div');row.className='ext-pending-row';
      const label=make('span',item.file.webkitRelativePath||item.file.name),role=make('select');
      role.setAttribute('aria-label','Import role for '+item.file.name);
      ['input','reference','prediction','metadata'].forEach(v=>role.append(new Option(v,v)));role.value=item.role;
      role.onchange=()=>item.role=role.value;row.append(label,role);list.append(row);
    });
    controls();message(state.files.length+' files selected · '+(state.files.reduce((n,x)=>n+x.file.size,0)/1024**2).toFixed(1)+
      ' MiB. Set label files to reference. Re-importing an incomplete file restarts its temporary bytes; completed originals stay immutable.');
  }
  async function upload(){
    if(busy())return;state.upload=new AbortController();controls();$('#ext-progress').hidden=false;
    let uploaded=0;const total=state.files.reduce((n,x)=>n+x.file.size,0);
    try{
      if(!state.dataset)state.dataset=await post('',{name:$('#ext-name').value||'External evaluation dataset'});
      localStorage.setItem('external-dataset',state.dataset.id);
      for(const item of state.files){
        if(state.upload.signal.aborted)throw new DOMException('Stopped','AbortError');
        const file=item.file,name=file.webkitRelativePath||file.name;
        const existing=state.dataset.files.find(f=>f.name===name);let registered;
        if(existing){
          if(!['UPLOADING','INTERRUPTED','CANCELLED'].includes(existing.state))throw Error('ORIGINAL_IMMUTABLE · '+name+' is already stored. Select only the new or incomplete files to import.');
          if(existing.bytes!==file.size||existing.role!==item.role)throw Error('INCOMPLETE_FILE_MISMATCH · Reselect the original incomplete file and its role, or create a new dataset.');
          registered=await post('/'+state.dataset.id+'/files/'+existing.id+'/restart');
        }else registered=await post('/'+state.dataset.id+'/files',{name,size:file.size,role:item.role});
        for(let offset=0;offset<file.size;offset+=8*1024**2){
          if(state.upload.signal.aborted)throw new DOMException('Stopped','AbortError');
          const chunk=file.slice(offset,offset+8*1024**2);
          await api('/'+state.dataset.id+'/files/'+registered.id+'/content?offset='+offset,{method:'PUT',body:chunk,signal:state.upload.signal});
          uploaded+=chunk.size;$('#ext-progress').value=100*uploaded/total;message('Uploading '+name+' · '+Math.round(100*uploaded/total)+'%');
        }
        await post('/'+state.dataset.id+'/files/'+registered.id+'/finish');
      }
      state.files=[];$('#ext-pending').replaceChildren();state.upload=null;await inspect();
    }catch(error){message(error.name==='AbortError'?'Upload stopped. Completed originals remain; reselect the incomplete file to restart.':error.message);}
    finally{state.upload=null;controls();}
  }
  async function inspect(){
    if(!state.dataset||busy())return;remember();state.submitting=true;controls();
    try{const job=await post('/'+state.dataset.id+'/inspect',{full_scan:true});state.submitting=false;poll(job.id);}
    catch(error){message(error.message);}finally{state.submitting=false;controls();}
  }
  function parameters(){
    const value={inputs:selected(),question:$('#ext-question').value,aligned_ordered:$('#ext-aligned').checked,
      threshold:Number($('#ext-threshold').value),water_threshold:Number($('#ext-water-threshold').value)};
    if($('#ext-reference').value){
      if(!state.protocol||state.protocol.dataset_revision!==state.dataset.revision)throw Error('Load the explicit evaluation protocol for this dataset revision before using labels.');
      value.reference_id=$('#ext-reference').value;value.protocol=state.protocol;
    }
    return value;
  }
  function download(link,value,name,type){if(link.href.startsWith('blob:'))URL.revokeObjectURL(link.href);link.href=URL.createObjectURL(new Blob([value],{type}));link.download=name;}
  async function preflight(){
    if(!state.dataset||busy())return;state.phase='preflight';controls();remember();
    try{
      const declarations={inputs:selected(),question:$('#ext-question').value,aligned_ordered:$('#ext-aligned').checked,protocol:state.protocol||{}};
      state.report=await post('/'+state.dataset.id+'/compatibility',declarations);
      const root=$('#ext-contracts');root.replaceChildren();
      state.report.specialists.forEach(item=>{
        const d=make('details');d.append(make('summary',item.name+' · '+item.status+' · '+item.blocking_reasons.length+' blocking'));
        const table=make('table'),head=make('tr');
        ['Parameter','Expected','Observed','Status / severity','Explanation / preparation'].forEach(v=>head.append(make('th',v)));table.append(head);
        item.parameters.forEach(row=>{const tr=make('tr');[row.parameter,typeof row.expected==='string'?row.expected:JSON.stringify(row.expected),
          typeof row.observed==='string'?row.observed:JSON.stringify(row.observed),row.status+' · '+row.severity,row.explanation+' '+row.suggested_preparation].forEach(v=>tr.append(make('td',v)));table.append(tr);});
        const scroll=make('div');scroll.className='ext-table';scroll.append(table);d.append(make('p',item.scope),scroll);root.append(d);
      });
      const select=$('#ext-specialist');select.replaceChildren(new Option(state.report.eligible_specialists.length?'Choose an eligible specialist':'No eligible specialist',''));
      state.report.specialists.filter(v=>v.eligible).forEach(v=>select.append(new Option(v.name,v.specialist)));
      if(state.report.eligible_specialists.length===1)select.value=state.report.eligible_specialists[0];
      download($('#ext-report-json'),JSON.stringify(state.report,null,2),'compatibility_report.json','application/json');
      const csv=await fetch('/api/datasets/'+state.dataset.id+'/compatibility.csv',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(declarations)});
      $('#ext-report-csv').hidden=!csv.ok;if(csv.ok)download($('#ext-report-csv'),await csv.text(),'compatibility_report.csv','text/csv');
      $('#ext-report-downloads').hidden=false;
      message(state.report.eligible_specialists.length?state.report.eligible_specialists.length+' specialist(s) passed preflight. No model has run yet.':
        'No eligible specialist · inspect all blocking parameters. The diagnostic report completed; no incompatible model was run.');
    }catch(error){state.report=null;message(error.message);}finally{state.phase='';controls();}
  }
  async function launch(operation){
    if(busy())return;
    try{
      const payload=parameters();
      if(operation==='analyze')payload.specialist=$('#ext-specialist').value;
      else{
        if(!payload.reference_id)throw Error('EVALUATION_NOT_POSSIBLE — COMPATIBLE_GROUND_TRUTH_NOT_PROVIDED');
        if($('#ext-prediction').value)payload.prediction_id=$('#ext-prediction').value;
        else if(state.lastPrediction&&sameInputs(state.predictionInputs,selected()))payload.prediction_job_id=state.lastPrediction;
        else throw Error('Select imported predictions or complete an analysis for these exact input files first.');
      }
      remember();state.submitting=true;clearAnalysis();controls();
      const job=await post('/'+state.dataset.id+'/'+operation,payload);state.submitting=false;poll(job.id);
    }catch(error){message(error.message);}finally{state.submitting=false;controls();}
  }
  async function poll(id){
    state.job=id;localStorage.setItem('external-job',id);const token=++state.poll;controls();
    try{
      for(let i=0;i<1800&&state.poll===token;i++){
        const job=await api('/jobs/'+id);message(job.state+' · '+(job.progress?.stage||job.message||''));
        if(['COMPLETE','EVALUATED','EVALUATION_NOT_POSSIBLE','PROCESSING_FAILED','CANCELLED','INTERRUPTED'].includes(job.state)){
          state.job=null;state.phase='restore';await load(job.dataset_id);state.lastJob=job.id;remember();state.phase='';
          if(job.operation==='inspect'&&job.state==='COMPLETE')await preflight();else resultView(job);
          controls();return;
        }
        await new Promise(resolve=>setTimeout(resolve,500));
      }
      message('Polling deadline reached. Refresh to recover the persistent worker state.');
    }catch(error){message(error.message);}finally{if(state.poll===token){state.job=null;state.phase='';controls();}}
  }
  function resultView(job){
    const root=$('#ext-result');root.hidden=false;root.replaceChildren();const data=job.result;
    const predicted=['EVALUATION_NOT_POSSIBLE','EVALUATED'].includes(job.state);
    root.append(make('h3',job.state==='EVALUATION_NOT_POSSIBLE'?'Analysis complete · no evaluation labels':job.state));
    root.append(make('p',data?.metrics?.message||job.message||'Inspect the retained failure report.'));
    if(predicted&&job.operation==='analyze'){state.lastPrediction=job.id;state.predictionInputs=selected();remember();}
    if(data?.analysis_result){
      const result=data.analysis_result;
      if(result.answer)root.append(make('p',result.answer));
      const s=result.statistics;
      if(s?.valid_pixels!=null)root.append(make('p',(s.selected_pixels!=null?s.selected_pixels.toLocaleString()+' threshold-selected pixels / ':'')+
        s.valid_pixels.toLocaleString()+' valid pixels. This measurement is not an accuracy score.'));
      const details=make('details');details.append(make('summary','Actual analysis output'),make('pre',JSON.stringify(result,null,2)));root.append(details);
    }
    if(data?.metrics?.state==='EVALUATED'){
      const m=data.metrics;root.append(make('p','Evaluated '+(m.valid_pixels??m.denominator_cases??m.denominator)+' '+(m.task==='segmentation'?'valid pixels':'cases')+
        (m.excluded_pixels!=null?' · '+m.excluded_pixels+' excluded pixels.':'.')));
      const scope=data.evaluation_scope;if(scope?.reference_provenance)root.append(make('p',scope.split+' · '+scope.reference_provenance));
      if(m.per_class){
        const cards=make('div');cards.className='ext-score-grid';m.per_class.forEach(c=>{
          const card=make('div');card.append(make('strong',c.class_name),make('p',(c.IoU!=null?'IoU '+(100*c.IoU).toFixed(2)+'% · ':'')+
            'F1 '+(c.F1==null?'undefined':(100*c.F1).toFixed(2)+'%')),make('small','Reference support: '+c.support));cards.append(card);
        });root.append(cards);
      }else if(m.exact_match!=null)root.append(make('p','Answer match: '+m.correct+' / '+m.denominator+' ('+(100*m.exact_match).toFixed(2)+'%)'));
      const full=make('details');full.append(make('summary','Complete metrics, denominators & class mappings'),make('pre',JSON.stringify(m,null,2)));root.append(full);
    }
    if(data?.failures?.length||job.failures?.length)root.append(make('pre',JSON.stringify(data?.failures||job.failures,null,2)));
    const evidence=$('#ext-evidence');evidence.replaceChildren();
    if(data){
      if(data.artifacts?.includes('prediction-preview.png')){
        const preview=make('details');preview.append(make('summary','Prediction and reference previews'));
        const images=make('div');images.className='ext-preview-grid';
        [['prediction-preview.png','Prediction · native labels'],...(data.artifacts.includes('reference-preview.png')?[['reference-preview.png','Reference · native labels']]:[])].forEach(([file,label])=>{
          const figure=make('figure'),image=make('img');image.alt=label;image.loading='lazy';image.src='/api/datasets/jobs/'+job.id+'/export/'+file;
          figure.append(image,make('figcaption',label));images.append(figure);
        });
        preview.append(images,make('p','Top-left native window, up to 512×512. Native labels: 0 gray, 1 gold, 2 brown; NoData and declared reference-ignore pixels transparent. Other codes are gray. The frozen protocol defines exact class semantics.'));
        root.append(preview);
      }
      ['evidence.zip','result.json','metrics.json','metrics.md','predictions.csv','checksums.sha256','reproduce.md'].filter(name=>data.artifacts?.includes(name)).forEach(name=>{
        const link=make('a',name+' ↓');link.href='/api/datasets/jobs/'+job.id+'/export/'+name;evidence.append(link);
      });
      const details=make('details');details.append(make('summary','Actual timing and worker memory'),make('pre',JSON.stringify({worker:data.timings,
        operation_wall_seconds:job.wall_seconds,observed_worker_peak_rss:job.peak_observed_worker_rss_bytes},null,2)));evidence.append(details);
    }
  }
  $('#ext-files').onchange=e=>pending(e.target.files);$('#ext-folder').onchange=e=>pending(e.target.files);
  $('#ext-import').onclick=upload;$('#ext-inspect').onclick=inspect;$('#ext-preflight').onclick=preflight;
  $('#ext-analyze').onclick=()=>launch('analyze');$('#ext-evaluate').onclick=()=>launch('evaluate');$('#ext-refresh').onclick=refresh;
  ['ext-specialist','ext-reference','ext-prediction','ext-threshold','ext-water-threshold'].forEach(id=>$('#'+id).onchange=()=>{remember();controls();});
  ['ext-question','ext-aligned'].forEach(id=>$('#'+id).onchange=()=>{clearAnalysis();remember();controls();});
  $('#ext-saved').onchange=async e=>{
    if(busy())return;remember();state.files=[];$('#ext-pending').replaceChildren();state.phase='selection';controls();
    try{
      if(e.target.value)await load(e.target.value);
      else{
        ++state.contextVersion;state.dataset=null;state.lastPrediction=null;state.predictionInputs=[];state.protocol=null;state.lastJob=null;clearAnalysis();
        $('#ext-inventory').replaceChildren();$('#ext-metadata').textContent='';$('#ext-name').value='';
        $('#ext-reference').replaceChildren(new Option('No compatible ground truth provided',''));
        $('#ext-prediction').replaceChildren(new Option('Use the last completed model prediction',''));localStorage.removeItem('external-dataset');protocolDisplay();
      }
      message(state.dataset?'Stored observations ready. Run preflight for this selection.':'Choose files for the new dataset. Previous results cleared.');
    }catch(error){message(error.message);}finally{state.phase='';controls();}
  };
  $('#ext-protocol').onchange=async e=>{
    try{
      const file=e.target.files[0];if(!file)return;if(file.size>65536)throw Error('Protocol JSON must be at most 64 KiB.');
      const value=JSON.parse(await file.text());if(!value||Array.isArray(value)||typeof value!=='object')throw Error('Protocol must be a JSON object.');
      state.protocol=value;remember();protocolDisplay();controls();
    }catch(error){state.protocol=null;protocolDisplay();message(error.message);controls();}
  };
  $('#ext-stop').onclick=async()=>{
    try{
      if(state.upload){
        state.upload.abort();if(state.dataset){
          for(let i=0;i<10;i++){
            try{await post('/'+state.dataset.id+'/cancel-upload');state.upload=null;state.phase='restore';await load(state.dataset.id);message('Upload stopped. Temporary chunks removed; reselect the incomplete file to restart. Completed originals retained.');break;}
            catch(error){if(i===9)throw error;await new Promise(resolve=>setTimeout(resolve,150));}
          }
        }
      }else if(state.job){await post('/jobs/'+state.job+'/cancel');message('Stopping the actual isolated worker…');}
    }catch(error){message(error.message);}finally{state.phase='';controls();}
  };
  if(location.hash==='#datasets')open();
})();
