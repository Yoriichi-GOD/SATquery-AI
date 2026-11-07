'use strict';
async function currentBenchmarks(){
 const overview=element('section'),detail=element('section');
 overview.className=detail.className='current-benchmarks';
 $('#evidence-highlights').before(overview);$('#eval-content').prepend(detail);
 try{
  const r=await fetch('/api/experimental-evidence');if(!r.ok)throw Error('Evidence unavailable');const d=await r.json();
  overview.append(element('h3','Flood Impact · verification'),element('p','Software checks and real-event benchmarks are kept separate. Synthetic fixtures cannot establish flood accuracy.'));
  const cards=element('div');cards.className='metrics';overview.append(cards);
  metric(cards,'Software tests passed',String(d.tests.passed));metric(cards,'Failures / errors',`${d.tests.failures} / ${d.tests.errors}`);metric(cards,'Real-event benchmarks',String(d.benchmarks.metrics.length));
  overview.append(element('p','Real Syapru Besi SAR and historical OSM are acquired. A frozen water-change baseline is available. AOI01 reference is landslide-labelled, so no matching-class flood IoU or F1 is claimed.'));
  detail.append(element('h3','Executable regression checks'),table(['Test suite','Checks'],d.tests.suites.map(x=>[x.name,x.count])),element('p','Source: saved pytest JUnit report. These are software checks, not remotely sensed accuracy measurements.'));
  detail.append(element('h3','Saved experimental runs'),table(['Run','Evidence type','New-water candidate pixels'],d.runs.map(x=>[x.run_id,x.synthetic?'Synthetic fixture':'Observation analysis',x.summary.new_water_pixels])));
  detail.append(element('h3','Real-event benchmark ledger'));
  if(!d.benchmarks.metrics.length)detail.append(element('p','No measured entries yet. Each future result must identify its dataset, split, sample/event count, metric definition and source artifact.'));
  else detail.append(table(['Task','Dataset / split','Metric','Value','Samples','Source'],d.benchmarks.metrics.map(x=>[x.task,x.dataset+' / '+x.split,x.metric,x.value,x.samples,x.source])));
  for(const [url,label] of [['/api/experimental-evidence','Download current evidence ledger'],['/assets/benchmark-data.json','Download benchmark registry']]){const a=element('a',label);a.href=url;a.download='';detail.append(a,element('br'));}
 }catch(e){overview.append(element('p',e.message));}
}currentBenchmarks();

async function datasetReadiness(){
 const section=element('section');section.className='current-benchmarks';$('#eval-content').append(section);
 try{const r=await fetch('/assets/dataset-readiness.json');if(!r.ok)throw Error('Dataset register unavailable');const d=await r.json();
 section.append(element('h3','Nepal data readiness'),element('p','Both EMSR927 references are evaluation-only. AOI01 class metadata was inspected after prediction freeze: Mass Movement / Landslide. Water-only predictions are not a compatible landslide benchmark.'));
 section.append(table(['Area','Reference','Compatible SAR candidate pairs','Downloaded imagery'],d.areas.map(a=>[a.area,d.references.find(r=>r.area===a.area).filename,a.candidate_pairs.length,a.area==='syapru_besi'?'Acquired and processed':'Metadata only'])));
 section.append(element('p','16 August → 28 August 2026: same platform, ascending orbit 85; catalogue footprints cover both AOIs. Syapru Besi pixels and georeferencing are verified; predictive accuracy remains unvalidated.'));
 const a=element('a','Download scene candidates and reference hashes');a.href='/assets/dataset-readiness.json';a.download='dataset-readiness.json';section.append(a);
 }catch(e){section.append(element('p',e.message))}
}datasetReadiness();

(async()=>{try{const r=await fetch('/assets/debris-reference-agreement.json');if(!r.ok)return;const d=await r.json();const section=element('section');section.className='current-benchmarks';section.append(element('h3','Debris candidate reference agreement · one AOI'),element('p','Post-freeze comparison against EMSR927 landslide extent. This is a diagnostic proxy comparison, not validated debris accuracy.'),table(['IoU','F1','Precision','Recall','Valid pixels'],[[d.iou.toFixed(3),d.f1.toFixed(3),d.precision.toFixed(3),d.recall.toFixed(3),d.valid_pixels]]));d.limitations.forEach(x=>section.append(element('p',x)));const a=element('a','Download comparison and provenance');a.href='/assets/debris-reference-agreement.json';section.append(a);$('#eval-content').append(section)}catch(e){}})();
