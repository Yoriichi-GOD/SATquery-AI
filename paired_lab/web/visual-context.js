/* Verified retained optical previews beside the existing terrain renderer. */
(() => {
  'use strict';
  if(!window.SQNoir)return;
  const $=s=>document.querySelector(s),make=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
  let host,stage,controls,note,record,recordBody,source=null,current=null,version=0,controller=null,phase='after';
  const enabled=new Set(),sameGrid=(a,b)=>a&&b&&a.crs===b.crs&&a.width===b.width&&a.height===b.height&&JSON.stringify(a.transform)===JSON.stringify(b.transform);
  function create(){
    if(host)return true;const viewer=$('#earth-viewer');if(!viewer)return false;
    const pair=make('div',null,'sq-observation-pair');viewer.before(pair);pair.append(viewer);
    host=make('section',null,'sq-visual-context');host.setAttribute('aria-label','Verified optical imagery and source overlays');
    host.append(make('span','RETAINED OPTICAL · SOURCE CONTEXT','eyebrow'),make('h3','See the observed surface.'));
    controls=make('div',null,'sq-rgb-controls');stage=make('div',null,'sq-rgb-stage');note=make('p','Select a saved observation to check optical availability.','sq-rgb-note');note.setAttribute('role','status');
    record=make('details');record.append(make('summary','Optical source, dates & overlay limits'));recordBody=make('div');record.append(recordBody);
    host.append(controls,stage,note,record);pair.append(host);return true;
  }
  function clear(message){if(!create())return;source=null;enabled.clear();controls.replaceChildren();stage.replaceChildren(make('p',message));recordBody.replaceChildren();note.textContent=message;}
  function render(){
    if(!source||!create())return;
    controls.replaceChildren();stage.replaceChildren();
    const dates=make('div',null,'sq-rgb-dates');dates.setAttribute('role','group');dates.setAttribute('aria-label','Optical source date');
    for(const key of ['before','after']){const item=source[key],button=make('button',(key==='before'?'Before':'After')+' RGB · '+item.date);button.type='button';button.setAttribute('aria-pressed',String(phase===key));button.onclick=()=>{phase=key;render();};dates.append(button);}
    controls.append(dates);
    const overlayControls=make('div',null,'sq-rgb-overlays');
    const base=make('img');base.src=source[phase].url;base.alt='Retained optical RGB · '+source[phase].date;stage.append(base);
    const thisVersion=version,overlayNodes=[];
    for(const item of source.overlays||[]){
      const label=make('label'),check=make('input');check.type='checkbox';check.checked=enabled.has(item.id);check.setAttribute('aria-label','Show '+item.label);
      const swatch=make('span',null,'sq-rgb-swatch');swatch.dataset.layer=item.id;swatch.setAttribute('aria-hidden','true');label.append(check,swatch,make('span',item.label));overlayControls.append(label);
      const layer=make('img');layer.src=item.url;layer.alt='';layer.className='sq-rgb-overlay';layer.hidden=true;layer.dataset.layer=item.id;stage.append(layer);overlayNodes.push([item,layer]);
      check.onchange=()=>{if(check.checked)enabled.add(item.id);else enabled.delete(item.id);layer.hidden=!enabled.has(item.id)||!base.complete||!base.naturalWidth;};
      layer.onerror=()=>{if(thisVersion===version&&layer.isConnected){layer.hidden=true;check.checked=false;check.disabled=true;enabled.delete(item.id);note.textContent='The '+item.label+' preview is unavailable. Its measurement is unchanged; inspect the source record.';}};
    }
    controls.append(overlayControls);
    const selected=source[phase];note.textContent=selected.date+' · '+selected.display;
    base.onload=()=>{if(thisVersion!==version||!base.isConnected)return;overlayNodes.forEach(([item,n])=>n.hidden=!enabled.has(item.id));};
    base.onerror=()=>{if(thisVersion!==version||!base.isConnected)return;overlayNodes.forEach(([,n])=>n.hidden=true);stage.replaceChildren(make('p','Verified optical preview unavailable. No substitute image is shown.'));note.textContent='Optical source could not be loaded. Check the local source service.';};
    if(base.complete&&base.naturalWidth)base.onload();
    recordBody.replaceChildren();
    for(const text of source.limitations||[])recordBody.append(make('p',text));
    recordBody.append(make('p','Water: cyan. Possible debris: copper. Historical mapped buildings: violet outlines, not confirmed damage. Uncoloured imagery is not proof of absence.'));
    const a=make('a','Open this verified RGB preview ↗');a.href=selected.url;a.target='_blank';a.rel='noopener';recordBody.append(a,make('pre',JSON.stringify({run_id:source.run_id,before:source.before,after:source.after,overlays:source.overlays,coverage:source.coverage},null,2)));
  }
  async function update(run){
    const id=run?.id||null;if(current===id&&host)return;current=id;++version;const token=version;controller?.abort();controller=new AbortController();clear(id?'Checking retained optical sources…':'No saved flood observation selected. Optical RGB is unavailable.');
    const h=$('#earth .earth-intro h1'),k=$('#earth .earth-intro .eyebrow');
    if(h&&k){h.textContent=id==='event-fe47db331390'?'The Road Home.':'Terrain & flood.';k.textContent=id==='event-fe47db331390'?'SYAPRU BESI, NEPAL · SAVED OBSERVATIONS':'CONNECTED EARTH OBSERVATIONS';}
    if(!id)return;
    try{
      const response=await fetch('/api/flood/runs/'+encodeURIComponent(id)+'/visual-context',{cache:'no-store',signal:controller.signal});if(!response.ok)throw Error('Retained optical service unavailable ('+response.status+').');
      const value=await response.json();if(token!==version)return;
      if(value.run_id!==id)throw Error('Source run identity does not match the current selection.');
      if(!value.optical_available){clear(value.reason||'No hash-verified retained optical RGB is available for this run. SAR and terrain remain available.');return;}
      if(!value.before?.source_sha256||!value.after?.source_sha256||!sameGrid(value.before.grid,value.grid)||!sameGrid(value.after.grid,value.grid))throw Error('Optical grid or source identity is not verified for this display.');
      source=value;phase='after';enabled.clear();render();
    }catch(error){if(token!==version||error.name==='AbortError')return;clear(error.message);}
  }
  const previous=window.SQNoir.context;window.SQNoir.context=function(run,...args){previous.call(this,run,...args);update(run);};
})();
