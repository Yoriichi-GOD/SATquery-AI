'use strict';
const inputPreviews=new Map();
function showSuggestions(queries){
 const box=$('#suggestions');box.replaceChildren();box.hidden=!queries.length;
 if(!queries.length)return;
 box.append(element('p','You can ask:'));
 for(const query of queries){const b=element('button',query);b.type='button';b.className='suggestion';b.onclick=()=>{$('#question').value=query;$('#question').focus();feedback('Question selected. Press Analyze images to run it.');};box.append(b)}
}
function drawInputs(){
 if(active||!$('#result').hidden)return;
 const choice=$('#sample').value;if(choice!=='single'&&choice!=='')return;
 const ids=choice==='single'?['single-file']:['file-a','file-b'];
 const root=$('#views');root.replaceChildren();root.classList.remove('input-pair');
 const any=ids.some(id=>$( '#'+id).files.length);root.hidden=!any;$('#empty').hidden=any;if(!any)return;
 root.classList.add('input-pair');
 for(const [i,id] of ids.entries()){
  const file=$('#'+id).files[0],p=inputPreviews.get(id),card=element('section');card.className='input-card';
  const single=id==='single-file',suffix=id.slice(-1),mode=$(single?'#single-modality':'#mode-'+suffix).value;
  const mixed=!single&&$('#mode-a').value!==$('#mode-b').value;
  const role=single?'Input':mixed?(mode==='sar'?'SAR':'Optical'):(i===0?'Before · first image':'After · second image');
  card.append(element('h3',role));
  if(p?.url){const b=element('button');b.type='button';const img=element('img');img.src=p.url;img.alt=role+' — '+file?.name;b.append(img);b.onclick=()=>{$('#full').src=p.url;$('#viewer').showModal()};card.append(b)}
  else card.append(element('p',file?(p?.error||'Preparing preview…'):'Choose an image'));
  card.append(element('p',file?.name||'No file selected'));
  card.append(element('p',mode+' · '+(single?'Single observation':$('#date-'+suffix).value||'Date not supplied')));
  if(p?.label)card.append(element('small',p.label));root.append(card);
 }
 $('#visual-note').textContent='Input previews only. Review image order and dates before analysis; a preview does not establish input compatibility.';
}
async function previewInput(id){
 const field=$('#'+id),file=field.files[0],previous=inputPreviews.get(id);if(previous?.url)URL.revokeObjectURL(previous.url);
 const current={};inputPreviews.set(id,current);$('#result').hidden=true;$('#execution').hidden=true;showSuggestions([]);drawInputs();if(!file)return;
 if(file.size>20*1024*1024){current.error='Preview limit is 20 MB.';drawInputs();return}
 if(/\.(png|jpe?g|webp)$/i.test(file.name)){current.url=URL.createObjectURL(file);current.label='Original image preview; analysis eligibility checked separately';drawInputs();return}
 try{
  const body=new FormData();body.append('file',file);body.append('modality',$(id==='single-file'?'#single-modality':'#mode-'+id.slice(-1)).value);
  const response=await fetch('/api/input-preview',{method:'POST',body});
  if(!response.ok){const j=await response.json();throw Error(typeof j.detail==='string'?j.detail:'Preview unavailable')}
  const blob=await response.blob();if(inputPreviews.get(id)!==current)return;
  current.url=URL.createObjectURL(blob);current.label=response.headers.get('X-Preview-Description')||'Display preview only';
 }catch(error){if(inputPreviews.get(id)===current)current.error=error.message}
 if(inputPreviews.get(id)===current)drawInputs();
}
for(const id of ['single-file','file-a','file-b'])$('#'+id).addEventListener('change',()=>previewInput(id));
for(const [id,file] of [['single-modality','single-file'],['mode-a','file-a'],['mode-b','file-b']])$('#'+id).addEventListener('change',()=>previewInput(file));
for(const id of ['date-a','date-b'])$('#'+id).addEventListener('change',()=>{$('#result').hidden=true;$('#execution').hidden=true;showSuggestions([]);drawInputs()});
$('#sample').addEventListener('change',()=>{showSuggestions([]);drawInputs()});
const beforeViews=views;views=function(items){$('#views').classList.remove('input-pair');beforeViews(items)};

for(const id of ['own-mode','single-mode','pair-mode'])$('#'+id).addEventListener('click',drawInputs);
