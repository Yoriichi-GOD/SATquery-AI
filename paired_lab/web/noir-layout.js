/* Fixed shell and scroll ownership. No analytical state is changed here. */
(() => {
  'use strict';
  const $=s=>document.querySelector(s),make=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
  if(!$('#sq-evidence'))return;
  document.body.classList.add('sq-shell');
  const footer=$('body>footer');footer.tabIndex=0;footer.setAttribute('aria-label','Selected source metadata. On small screens scroll horizontally for all fields.');
  for(const field of footer.children)if(field.tagName==='DIV')field.classList.add('sq-footer-field');
  const art=make('div',null,'sq-footer-art');art.setAttribute('aria-hidden','true');
  const img=make('img');img.src='/assets/noir/thin-scientific-data-footer.png';img.alt='';art.append(img);footer.prepend(art);
  // Crop only the upper, non-text wave from the supplied footer artwork with CSS.
  // Its example sources/coordinates/dates remain outside the clipped region.
  const shellSize=()=>{
    document.documentElement.style.setProperty('--sq-header-h',Math.ceil($('body>header').getBoundingClientRect().height)+'px');
    document.documentElement.style.setProperty('--sq-footer-h',Math.ceil(footer.getBoundingClientRect().height)+'px');
  };
  new ResizeObserver(shellSize).observe($('body>header'));new ResizeObserver(shellSize).observe(footer);shellSize();
  // Measurements and the benchmark archive belong to the central evidence pane;
  // opening a long table never moves the independently scrollable inspector.
  const evidencePane=$('.sq-stage-panel');evidencePane.append($('#sq-measures'),$('.sq-archive'));
  const dialog=make('dialog',null,'sq-table-dialog');dialog.setAttribute('aria-labelledby','sq-table-title');
  const head=make('div',null,'sq-table-dialog-head'),title=make('h2','Table');title.id='sq-table-title';const close=make('button','Close table ×');close.type='button';close.onclick=()=>dialog.close();
  head.append(title,close);const content=make('div',null,'sq-table-dialog-body');content.tabIndex=0;content.setAttribute('aria-label','Full table; scroll vertically and horizontally');dialog.append(head,content);document.body.append(dialog);
  let scheduled=false;
  function enhance(){
    scheduled=false;
    for(const [selector,label] of [['.visual','Workspace images'],['.workspace>aside','Workspace analysis'],['.earth-visual','Terrain and observations'],['.earth-sidebar','Contextual analysis'],['.sq-catalog','Evidence catalogue'],['.sq-stage-panel','Evidence layers and tables'],['.sq-inspector','Source inspector']]){
      const pane=$(selector);if(pane){pane.tabIndex=0;if(!pane.hasAttribute('aria-label'))pane.setAttribute('aria-label',label+'; independently scrollable');}
    }
    for(const table of document.querySelectorAll('main table:not([data-sq-expandable])')){
      table.dataset.sqExpandable='true';
      if(table.querySelector('input,select,textarea,button'))continue;
      const button=make('button','Open table in full view ↗','sq-table-open');button.type='button';
      button.onclick=()=>{
        const copy=table.cloneNode(true);copy.removeAttribute('id');copy.querySelectorAll('[id]').forEach(n=>n.removeAttribute('id'));
        title.textContent=table.caption?.textContent||table.closest('details')?.querySelector('summary')?.textContent||'Table · recorded values';
        content.replaceChildren(copy);dialog.showModal();content.scrollTop=0;content.scrollLeft=0;
      };
      table.before(button);
    }
    const current=$('#earth')&&!$('#earth').hidden?'earth-tab':$('#external')&&!$('#external').hidden?'external-tab':!$('#evaluation').hidden?'eval-tab':'lab-tab';
    document.querySelectorAll('body>header nav button').forEach(b=>{const active=b.id===current;b.classList.toggle('active',active);if(active)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  }
  const schedule=()=>{if(!scheduled){scheduled=true;requestAnimationFrame(enhance);}};
  new MutationObserver(schedule).observe($('main'),{childList:true,subtree:true,attributes:true,attributeFilter:['hidden']});
  $('body>header nav').addEventListener('click',schedule);enhance();
})();
