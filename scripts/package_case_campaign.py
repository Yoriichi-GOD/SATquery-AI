"""Collect actual measurement receipts, figures and private native-window copies."""
import argparse,csv,json,shutil,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.terrain_exposure.io import sha256,save_json,candidate_raster

ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(Path(p).read_text())
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)

def package(work,notes,output):
    work=Path(work);out=Path(output)
    if out.exists():raise FileExistsError('Choose a new immutable paper pack')
    out.mkdir(parents=True)
    raw=ROOT/'research/datasets/local/campaign-20261107';raw.mkdir(parents=True,exist_ok=True)
    rawfiles={}
    for path in (work/'sources').rglob('*'):
        if path.is_file():
            relative=path.relative_to(work/'sources');target=raw/relative
            if target.exists() and sha256(target)!=sha256(path):raise FileExistsError('Different private source copy')
            if not target.exists():copy(path,target)
            if sha256(path)!=sha256(target):raise AssertionError('Source copy failed')
            rawfiles[relative.as_posix()]=sha256(target)
    save_json(raw/'LOCAL_MANIFEST.json',{'files':rawfiles,'role':'Private local acquired sources; hashes in portable paper pack'})
    save_json(out/'LOCAL_DATA_MANIFEST.json',{'local_root':'research/datasets/local/campaign-20261107','files':rawfiles,
        'source_distribution':'Native-window inputs kept local; licenses and API signing requirements recorded per asset'})
    cases=load(work/'measurements-v1/summary.json')
    for case in cases:
        for p in (work/'measurements-v1'/case).iterdir():
            if p.is_file() and p.suffix in {'.json','.csv','.png'}:copy(p,out/'cases'/case/p.name)
    copy(work/'measurements-v1/protocol.json',out/'protocol.json')
    nepal=load(work/'nepal-resolution-v1/summary.json');metrics={}
    for cell in ['30','90']:
        copy(work/f'nepal-resolution-v1/replay-{cell}m/summary.json',out/f'nepal/replay-{cell}m-summary.json')
        copy(work/f'nepal-resolution-v1/replay-{cell}m/manifest.json',out/f'nepal/replay-{cell}m-manifest.json')
        for name in ['metrics.json','metrics.csv','freeze.json','protocol.json','rows.json','evaluation-support.geojson','manifest.json']:
            copy(work/f'road-diagnostic-{cell}m-v1'/name,out/f'nepal/diagnostic-{cell}m'/name)
        metrics[cell]=load(work/f'road-diagnostic-{cell}m-v1/metrics.json')
    for name in ['independent-arithmetic-30m.json','source.json','protocol-amendment.json']:
        copy(work/'nepal-resolution-v1'/name,out/'nepal'/name)
    for p in (work/'evidence-challenge-v1').iterdir():
        if p.is_file():copy(p,out/'evidence-contract'/p.name)
    for p in Path(notes).glob('*.md'):copy(p,out/'sources'/p.name)
    copy(work/'osm-acquisition-summary.json',out/'osm-acquisition-summary.json') if (work/'osm-acquisition-summary.json').exists() else None
    # The OSM summary is under sources for the public adapter.
    if (work/'sources/osm-acquisition-summary.json').exists():copy(work/'sources/osm-acquisition-summary.json',out/'osm-acquisition-summary.json')
    acquisition={}
    for case in cases:
        rows=load(work/'sources'/case/'acquisition.json')['assets']
        acquisition[case]={'acquired_raster_windows':sum(r['state']=='ACQUIRED' for r in rows),
            'unavailable_raster_windows':sum(r['state']!='ACQUIRED' for r in rows)}
    acquisition['nepal']['additional_buffered_terrain_windows']=1
    save_json(out/'acquisition-summary.json',acquisition)
    rows=[]
    for case in ['varanasi','sangam-vihar']:
        u=cases[case]['urban']
        rows.append({'case':case,'metric':'annual_model_net_built_change','value':u['net_built_difference_ha'],'unit':'ha',
            'denominator':u['common_area_ha'],'denominator_unit':'ha','period':'2017–2023','evidence_role':'annual_model_transition_not_surveyed_construction'})
    k=cases['kedarnath']['historical']
    rows.append({'case':'kedarnath','metric':'common_clear_coverage','value':k['common_clear_fraction'],'unit':'fraction',
        'denominator':k['roi_pixels'],'denominator_unit':'ROI30m_pixels','period':'2013-05-22/2013-06-23','evidence_role':'quality_gate_registration_unavailable'})
    for key in ['new-water-proxy','vegetation-loss-proxy']:
        r=k[key];rows.append({'case':'kedarnath','metric':key,'value':r['area_ha'],'unit':'ha','denominator':r['valid_area_ha'],
            'denominator_unit':'ha','period':'2013-05-22/2013-06-23','evidence_role':'conditional_spectral_proxy_not_event_extent'})
    run=ROOT/'components/floodlab/artifacts/runs/event-fe47db331390'
    for layer,name,positive,valid in [('water','prediction.tif',[2],[0,1,2]),('debris','debris-candidates.tif',[1],[0,1])]:
        mask,support,g,meta=candidate_raster(run/name,positive,valid)
        rows.append({'case':'nepal','metric':layer+'_candidate_area','value':float(mask.sum()*g.area/10000),'unit':'ha',
            'denominator':float(support.sum()*g.area/10000),'denominator_unit':'ha','period':'retained_event_fe47db331390',
            'evidence_role':'saved_candidate_mask_not_independent_truth'})
    with (out/'MEASUREMENTS.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    figures(out,cases,metrics)
    save_json(out/'completion.json',{'definition_of_done':'Acquired-data measurements and integrated research release; publication validation remains partial',
        'steps':{'1_consolidated_release':'IMPLEMENTED; run current verification receipts before accepting',
            '2_nepal_measurement_prerequisites':'PARTIAL:target semantics/reference roles audited; 30m acquired; registration and10m feature resolution unresolved',
            '3_frozen_ABCD_comparison':'DEVELOPMENT_EXECUTED:22road fragments; no untouched class-compatible exposure validation',
            '4_urban_cases':'TEMPORAL_AND_TERRAIN_MEASURED_BOTH; historical infrastructure acquisition failed; exposure/transfer not validated',
            '5_kedarnath':'HISTORICAL_LANDSAT_AND_TERRAIN_PROCESSED;5.98% common clear; registration unavailable; event extent/exposure not validated',
            '6_evidence_and_novelty':'43software fault trials executed;8comparator review; human semantic experiment and scientific superiority unproved'},
        'hypotheses':{'H1':'NOT_PROVED:promising conditional terrain road-grade association only',
            'H2':'NOT_PROVED:annual urban model transitions measured without independent change labels',
            'H3':'NOT_PROVED:full graph below simpler terrain baseline; graph–proximity interval crosseszero',
            'H4':'SOFTWARE_GUARDS_TESTED;actual analyst/semantic causal experiment not run'},
        'publication_readiness':'NOT_READY_FOR_VALIDATED_SUPERIORITY_CLAIMS','training_performed':False,'synthetic_accuracy_results':False})
    save_json(out/'RELEASE_MANIFEST.json',{'schema':'satquery.case-research-release/1','files':{
        p.relative_to(out).as_posix():sha256(p) for p in sorted(out.rglob('*')) if p.is_file()},
        'manifest_scope':'Derived paper pack files, not authenticity of upstream satellite truth'})
    print(json.dumps({'acquired_native_rasters':sum(v['acquired_raster_windows']+v.get('additional_buffered_terrain_windows',0) for v in acquisition.values()),
        'private_local_files':len(rawfiles),'paper_pack':str(out)}))

def figures(out,cases,metrics):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    (out/'figures').mkdir()
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,case in zip(axes,['varanasi','sangam-vihar']):
        u=cases[case]['urban'];ax.bar(['2017','2023'],[u['built_before_ha'],u['built_after_ha']],color=['#777777','#222222'])
        ax.set_ylabel('Built class (ha), common10m support');ax.set_title(case)
        ax.text(.5,.96,f"Net +{u['net_built_difference_ha']:,.2f} ha",transform=ax.transAxes,ha='center',va='top')
    fig.suptitle('Annual land-cover model transitions; not independently surveyed construction',fontsize=10)
    for ext in ['png','pdf','svg']:fig.savefig(out/f'figures/urban-built-stock.{ext}',dpi=180)
    plt.close(fig)
    methods=['A_image_only','B_image_temporal','C_temporal_terrain','D_full_graph','proximity_only','terrain_only']
    fig,ax=plt.subplots(figsize=(10,4.5),layout='constrained');x=np.arange(len(methods))
    for i,cell in enumerate(['30','90']):
        values=[metrics[cell]['results'][m]['average_precision'] for m in methods]
        ax.bar(x+(i-.5)*.36,values,.36,color=['#222222','#999999'][i],label=f'{cell}m analysis of sameGLO30')
    ax.set_xticks(x,['A image','B temporal','C terrain','D graph','Proximity','Terrain only']);ax.set_ylim(0,1)
    ax.set_ylabel('Average precision');ax.legend(fontsize=8)
    ax.set_title('22previously inspected road-grade fragments;14positive/8negative\nExploratory association; no exposure truth or independent test',fontsize=10)
    for ext in ['png','pdf','svg']:fig.savefig(out/f'figures/nepal-development-baselines.{ext}',dpi=180)
    plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--notes',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();package(a.work,a.notes,a.output)
