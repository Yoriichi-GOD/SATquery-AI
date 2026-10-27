/* Saved benchmark results; no model execution and no synthetic scores. */
'use strict';
async function currentBenchmarks(){
 const detail=element('section'),overview=element('section');
 detail.className='current-benchmarks';overview.className='current-benchmarks';
 $('#eval-content').prepend(detail);$('#evidence-highlights').before(overview);
 const pct=x=>(100*x).toFixed(2)+'%',num=x=>x.toLocaleString('en-US');
 const heading=(parent,title,note)=>parent.append(element('h3',title),element('p',note));
 const cards=parent=>{const d=element('div');d.className='metrics';parent.append(d);return d};
 try{
  const response=await fetch('/assets/benchmark-data.json?v=20261014');if(!response.ok)throw Error('Saved benchmark data could not be loaded');const d=await response.json();
  heading(overview,'CDVQA · change-question answering','28 Sep 2026 · Frozen specialist benchmark; experimental RGB-pair mode is now available. Integration does not change these scores.');
  const cc=cards(overview);
  for(const [key,label] of [['Test','Test-1'],['Test2','Test-2']]){const m=d.cdvqa[key].all_official.paired;metric(cc,label+' · overall accuracy',pct(m.oa));cc.lastElementChild.append(element('p',num(m.n)+' questions · '+num(m.pairs)+' image pairs'));}
  overview.append(element('p','Both splits share imagery and overlap in questions; do not pool them. See detailed results for question-only controls, per-type accuracy and previously inspected pair exclusions.'));
  const metricRows=(workflow,split,metricName)=>d.metrics.filter(r=>r.workflow===workflow&&r.split===split&&r.metric===metricName);
  const mode={s1:'SAR only',s2:'Optical only',all:'Joint'};
  heading(overview,'Water segmentation · 90 test chips','Sen1Floods11 · pixel IoU · all three pathways shown on the same set.');
  const wc=cards(overview);wc.classList.add('water-metrics');for(const r of metricRows('water','test','iou'))metric(wc,mode[r.path_or_class]+' · water IoU',pct(r.value_0_to_1));
  overview.append(element('p','Optical-only scores highest on this test set. Joint fusion is not assumed to win. Bolivia is reported separately below.'));
  heading(overview,'Road / building change','21 Sep 2026 report · balanced 100-pair subset · pixel IoU.');
  const tc=cards(overview);for(const r of metricRows('temporal','balanced 100-pair subset','iou').filter(r=>r.path_or_class!=='unchanged'))metric(tc,r.path_or_class+' change',pct(r.value_0_to_1));
  heading(detail,'CDVQA · full evaluation and controls','OA: exact correct answers / all questions. AA: unweighted mean across eight question types. These are specialist scores, not overall SatQuery accuracy.');
  for(const [key,label] of [['Test','Test-1'],['Test2','Test-2']]){
   const x=d.cdvqa[key];heading(detail,label,'Official Train/Val used for training and checkpoint selection. Test imagery is shared across Test-1 and Test-2.');
   const rows=[];for(const [scope,scopeLabel] of [['all_official','Full split'],['excluding_12_previously_inspected_pairs','12 inspected pairs excluded']])for(const [model,title] of [['paired','Paired images'],['question_only','Question only'],['paired_shuffled_images','Shuffled images']]){const m=x[scope][model];rows.push([scopeLabel,title,num(m.n),num(m.pairs),pct(m.oa),pct(m.aa)])}
   detail.append(table(['Scope','Input/control','Questions','Pairs','OA','Macro AA'],rows));
   const p=x.all_official.paired,q=x.all_official.question_only;
   detail.append(table(['Question type','Questions','Paired accuracy','Question-only accuracy'],Object.entries(p.by_type).map(([k,v])=>[k.replaceAll('_',' '),num(v.n),pct(v.accuracy),pct(q.by_type[k].accuracy)])));
  }
  heading(detail,'Water · separate event and sensor pathways','90 test chips and a separate 15-chip Bolivia event. Water masks include permanent water; these scores do not establish flood identification or official-sensor transfer.');
  const wr=[];for(const split of ['test','bolivia'])for(const m of ['s1','s2','all']){const subset=d.metrics.filter(r=>r.workflow==='water'&&r.split===split&&r.path_or_class===m);wr.push([split,subset[0].samples,mode[m],...['iou','f1','precision','recall'].map(k=>pct(subset.find(r=>r.metric===k).value_0_to_1))])}
  detail.append(table(['Split','Chips','Pathway','IoU','F1','Precision','Recall'],wr));
  heading(detail,'Temporal · MCI road/building masks','Balanced 100-pair subset; mask metrics do not establish correctness of every caption detail.');
  detail.append(table(['Class','Pixel IoU','Pixel F1'],['unchanged','road','building'].map(c=>[c,...['iou','f1'].map(m=>pct(d.metrics.find(r=>r.workflow==='temporal'&&r.path_or_class===c&&r.metric===m).value_0_to_1))])));
  heading(detail,'Land cover · narrow fixture evaluation','12 existing Austrian fixtures from one source scene, mixing six validation and six test-labelled fixtures. Development evidence; not geographic generalisation.');
  detail.append(table(['Pathway','Micro F1'],metricRows('land_cover','12 existing fixtures','micro_f1').map(r=>[mode[r.path_or_class],pct(r.value_0_to_1)])));
  const a=element('a','Download saved benchmark data and source hashes');a.href='/assets/benchmark-data.json?v=20261014';a.download='satquery-benchmark-data.json';detail.append(a);
  detail.append(element('h3','Source files'),...d.sources.map(s=>element('p',s.path+' · '+s.hash_method+' · '+s.sha256)));
  detail.append(element('h3','Archived development checks'));
 }catch(error){overview.append(element('p','Benchmark evidence unavailable: '+error.message));detail.append(element('p','Benchmark evidence unavailable: '+error.message));}
}currentBenchmarks();
