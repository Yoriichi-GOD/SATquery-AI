"""QA-only historical scene selection followed by one frozen-method diagnostic run."""
import argparse,json,shutil
from pathlib import Path
import numpy as np
from shapely.geometry import shape,box
from research.datasets.cog import acquire,get_json
from research.cases.process_campaign import metric_grid,roi,warp,landsat_clear,terrain,historical,figure,rgb_figure
from research.terrain_exposure.io import save_json,sha256
from research.registration.diagnostics import audit

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'research/experiments/validation-closure-20261107.json'
LICENCE='https://www.usgs.gov/landsat-missions/landsat-data-access'

def strict_alignment(result,threshold=1.5):
    if result['status']=='UNAVAILABLE':return {'status':'UNAVAILABLE','reason':result['reason']}
    if result.get('held_out_matches',0)<5:return {'status':'UNAVAILABLE','reason':'INSUFFICIENT_HELDOUT_SUPPORT'}
    raw=result.get('pre_correction_displacement_p95_px')
    return {'status':'RELATIVE_VISIBLE_FEATURE_ALIGNMENT_ONLY' if raw is not None and raw<=threshold else 'MISALIGNED_UNCORRECTED',
        'precorrection_p95_px':raw,'threshold_px':threshold,'absolute_geolocation':'NOT_VALIDATED',
        'optical_to_SAR':'NOT_VALIDATED','post_fit_residual_not_used_to_pass_uncorrected_product':True,
        'claim_scope':'Shared visible features at this resolution; no surveyed control or whole-scene accuracy'}

def run(baseline,output):
    baseline=Path(baseline);out=Path(output)
    if out.exists():raise FileExistsError('Keep prior quality runs immutable')
    out.mkdir(parents=True);protocol=json.loads(PROTOCOL.read_text());cfg=protocol['kedarnath_scene_selection']
    save_json(out/'protocol.json',protocol)
    request={'collections':'landsat-c2-l2','bbox':','.join(map(str,cfg['bbox'])),
        'datetime':cfg['candidate_start']+'/'+cfg['candidate_end'],'limit':100}
    items=get_json('https://planetarycomputer.microsoft.com/api/stac/v1/search',request)
    if any(x.get('rel')=='next' for x in items.get('links',[])):raise ValueError('STAC selection truncated')
    save_json(out/'catalogue.json',items)
    candidates=[i for i in items['features'] if i['id'].startswith('LC08_L2SP_145039_') and i['id'].endswith('_02_T1')
        and shape(i['geometry']).covers(box(*cfg['bbox']))]
    candidates.sort(key=lambda x:x['id'])
    save_json(out/'sealed-candidate-ids.json',{'ids':[i['id'] for i in candidates],
        'selection_rule':'AllsameL8T1path145row039fullAOIcoverageinpredeclaredtimewindow','protocol_sha256':sha256(PROTOCOL),
        'no_change_predictions_or_reference_labels_read':True})
    casecfg={'bbox':cfg['bbox'],'crs':'EPSG:32644'};grid=metric_grid(casecfg,30)
    inside=roi(cfg['bbox'],grid.shape,grid.transform,grid.crs)
    qa=warp([baseline/'landsat-before-qa_pixel.tif'],grid);sat=warp([baseline/'landsat-before-qa_radsat.tif'],grid)
    baseclear=landsat_clear(np.nan_to_num(qa),np.nan_to_num(sat),inside&np.isfinite(qa)&np.isfinite(sat))
    rows=[]
    for item in candidates:
        folder=out/'qa'/item['id'];folder.mkdir(parents=True)
        receipts={}
        for band in ['qa_pixel','qa_radsat']:
            receipts[band]=acquire(item['assets'][band]['href'],cfg['bbox'],folder/(band+'.tif'),
                license_url=LICENCE,product=item['id']+':'+band,max_pixels=4_000_000)
        qa=warp([folder/'qa_pixel.tif'],grid);sat=warp([folder/'qa_radsat.tif'],grid)
        clear=landsat_clear(np.nan_to_num(qa),np.nan_to_num(sat),inside&np.isfinite(qa)&np.isfinite(sat))
        row={'id':item['id'],'datetime':item['properties']['datetime'],'scene_cloud_cover':item['properties'].get('eo:cloud_cover'),
            'common_clear_pixels':int((baseclear&clear).sum()),'roi_pixels':int(inside.sum()),
            'common_clear_fraction':float((baseclear&clear).sum()/inside.sum()),'receipts':receipts}
        rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='receipts'}),flush=True)
        save_json(out/'quality-rows.json',rows)
    ranked=sorted(rows,key=lambda r:(-r['common_clear_fraction'],r['datetime'],r['id']))
    selected=ranked[0] if ranked and ranked[0]['common_clear_fraction']>=cfg['minimum_common_clear_fraction'] else None
    decision={'selected_id':selected['id'] if selected else None,'threshold':cfg['minimum_common_clear_fraction'],
        'role':'QAselectedlaterseasoncontext_not_peakdisasterextent','ranking':[{k:v for k,v in row.items() if k!='receipts'} for row in ranked],
        'protocol_sha256':sha256(PROTOCOL),'selected_before_reflectance_change_or_registration':True}
    save_json(out/'selection.json',decision)
    if selected is None:return decision
    item=next(x for x in candidates if x['id']==selected['id']);pair=out/'pair';pair.mkdir();provenance=[]
    for source in sorted(baseline.glob('landsat-before-*.tif')):
        shutil.copyfile(source,pair/source.name);provenance.append({'filename':source.name,'sha256':sha256(source),'role':'unchanged_fixedbaseline'})
    for band in ['blue','green','red','nir08','swir16','swir22','qa_pixel','qa_radsat']:
        target=pair/f'landsat-after-{band}.tif'
        receipt=acquire(item['assets'][band]['href'],cfg['bbox'],target,license_url=LICENCE,product=item['id']+':'+band)
        provenance.append({'filename':target.name,**receipt})
    save_json(out/'pair-sources.json',provenance)
    parent=json.loads((ROOT/'research/experiments/case-campaign-20261107.json').read_text())
    acquisition=json.loads((baseline/'acquisition.json').read_text())
    resultdir=out/'analysis';resultdir.mkdir()
    _,hydros=terrain(baseline,casecfg,resultdir,parent,acquisition['assets'])
    hc={**casecfg,'before':'2013-05-22','after':selected['datetime'][:10]}
    metrics,panels=historical(pair,hc,resultdir,hydros[30],parent)
    metrics['strict_uncorrected_alignment']=strict_alignment(metrics['registration'])
    metrics['interpretation']='May22toQAselectedlaterseasonobservation; notJune16–17peak extent; seasonal/phenology/snowchangesconfounded'
    save_json(resultdir/'summary.json',metrics);figure(panels,resultdir,'Kedarnath quality-selected context');rgb_figure(pair,hc,resultdir,hydros[30].grid,parent)
    # Controls execute on actual acquired reflectance, separate from geospatial truth.
    a=warp([pair/'landsat-before-red.tif'],grid);valid=np.isfinite(a)&inside
    import cv2
    rng=np.random.default_rng(20261107)
    moved=cv2.warpAffine(np.nan_to_num(a),np.float32([[1,0,4],[0,1,-3]]),(a.shape[1],a.shape[0]),borderValue=0)
    movedmask=cv2.warpAffine(valid.astype('uint8'),np.float32([[1,0,4],[0,1,-3]]),(a.shape[1],a.shape[0]),flags=cv2.INTER_NEAREST)>0
    controls={name:audit(a,b,valid,v,grid,grid) for name,b,v in [
        ('self',a,valid),('known_shift',moved,movedmask),('unrelated_random',rng.normal(10000,1000,a.shape),valid)]}
    save_json(resultdir/'software-controls.json',{'population':'ACTUAL_IMAGE_CONTROL_TRANSFORMS_NOT_GROUNDCONTROL','controls':controls})
    print(json.dumps({'selected':selected['id'],'common_clear':metrics['common_clear_fraction'],
        'registration_status':metrics['registration']['status'],'strict':metrics['strict_uncorrected_alignment']}),flush=True)
    return decision

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.baseline,a.output)
