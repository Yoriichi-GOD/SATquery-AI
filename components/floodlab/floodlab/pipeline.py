"""Reproducible prepared-SAR pipeline. This is NOT raw SAFE preprocessing."""
import argparse,csv,hashlib,json,time,html
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from scipy.ndimage import binary_dilation,binary_erosion
from shapely.geometry import mapping,shape
from shapely.ops import transform as transform_geometry
from pyproj import Transformer
from .core import validate_manifest,read_pair,sar_change
from .impact import mask_geometry,exposure,road_graph,reachability


def write_json(path,value): path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify_tiled(pre,post,valid,tile_size,**kwargs):
    if not isinstance(tile_size,int) or tile_size<=0: raise ValueError('Invalid tile size')
    out=np.full(valid.shape,255,dtype='uint8')
    for y in range(0,out.shape[0],tile_size):
        for x in range(0,out.shape[1],tile_size):
            sl=(slice(y,y+tile_size),slice(x,x+tile_size))
            out[sl]=sar_change(pre[(slice(None),)+sl],post[(slice(None),)+sl],valid[sl],**kwargs)
    return out


def report(result,lang):
    s=dict(result['summary']); s['potentially_cut_off']=s['potentially_cut_off'] if s.get('connectivity_assessed',True) else 'not assessed / मूल्याङ्कन नभएको'; label='SYNTHETIC SOFTWARE TEST' if result['synthetic'] else 'EXPERIMENTAL OBSERVATION ANALYSIS'
    if lang=='ne':
        title='बाढी प्रभाव: प्रयोगात्मक स्थिति प्रतिवेदन'
        body=f"नयाँ पानीका सम्भावित पिक्सेल: {s['new_water_pixels']}; क्षेत्रफल: {s['new_water_m2']:.2f} m²। पानीसँग जुधेका भवन: {s['exposed_buildings']}। पानीसँग जुधेको सडक लम्बाइ: {s['exposed_road_m']:.2f} m। सम्भावित पहुँच विच्छेद भएका बस्ती: {s['potentially_cut_off']}।"
        caveat='यो परीक्षणात्मक अनुमान हो। वास्तविक सडक बन्द, भवनको क्षति वा बस्ती अलग भएको पुष्टि होइन। नेपाली पाठको मानव समीक्षा बाँकी छ।'
    else:
        title='Flood Impact: experimental situation report'
        body=f"New-water candidate pixels: {s['new_water_pixels']}; area: {s['new_water_m2']:.2f} m². Intersected buildings: {s['exposed_buildings']}. Intersected road length: {s['exposed_road_m']:.2f} m. Potentially cut-off settlements: {s['potentially_cut_off']}."
        caveat='Hypotheses only: intersections do not establish building damage or actual road closure. Unknown coverage and truncated networks cannot establish isolation.'
    if 'debris_candidate_m2' in s:
        body+=f" Debris-candidate area / मलबाको सम्भावित क्षेत्र: {s['debris_candidate_m2']:.2f} m². This proxy is unvalidated."
    limitations=' '.join(result['limitations'])
    return f'<!doctype html><html lang="{lang}"><meta charset="utf-8"><title>{title}</title><style>body{{font:17px system-ui;max-width:780px;margin:50px auto;line-height:1.7;padding:20px}}strong{{color:#955900}}@media print{{body{{margin:0;font-size:12pt}}}}</style><h1>{title}</h1><strong>{label}</strong><p>{html.escape(result["event_name"])}</p><p>{body}</p><p>{caveat}</p><p>{html.escape(limitations)}</p><p>Run: {html.escape(result["run_id"])} · Evidence: result.json, exposure.csv, connectivity.json, prediction.tif</p></html>'


def run(manifest_path,out):
    start=time.perf_counter(); manifest_path=Path(manifest_path).resolve(); root=manifest_path.parent
    m=json.loads(manifest_path.read_text(encoding='utf-8-sig'));validate_manifest(m)
    out=Path(out)
    if out.exists(): raise ValueError('Run directory already exists; do not overwrite frozen evidence')
    pre,post,valid,profile=read_pair(m,root)
    ipath=root/m['infrastructure_path']
    if digest(ipath)!=m['infrastructure_sha256']: raise ValueError('Infrastructure hash mismatch')
    infra=json.loads(ipath.read_text())
    if infra.get('snapshot')!=m['osm_snapshot'] or infra.get('role')!='historical_osm': raise ValueError('Infrastructure provenance mismatch')
    if rasterio.crs.CRS.from_user_input(infra['analysis_crs'])!=profile['crs']: raise ValueError('Infrastructure CRS mismatch')
    cfg=m['analysis']; prediction=classify_tiled(pre,post,valid,cfg['tile_size'],water_db=cfg['water_db'],drop_db=cfg['drop_db'])
    valid=prediction!=255; new=prediction==2
    if not valid.any(): raise ValueError('No valid paired observations; cannot report impact')
    flood=mask_geometry(new,profile['transform']); observed=mask_geometry(valid,profile['transform'])
    rows=exposure(infra['features'],flood,observed,profile['crs'])
    roads=infra.get('graph_roads',[f for f in infra['features'] if f['properties']['kind'] in ('road','bridge')])
    debris_geometry=None;debris_rows=[];debris_mask=None
    disruption=flood;network_observed=observed
    if m.get('debris'):
        dp=root/m['debris']['path']
        if digest(dp)!=m['debris']['sha256']:raise ValueError('Debris input hash mismatch')
        with rasterio.open(dp) as ds:
            if any(ds.profile[k]!=profile[k] for k in ('crs','transform','width','height')):raise ValueError('Debris grid mismatch')
            debris_mask=ds.read(1)
        debris_geometry=mask_geometry(debris_mask==1,profile['transform'])
        debris_observed=mask_geometry(debris_mask!=255,profile['transform'])
        debris_rows=exposure(infra['features'],debris_geometry,debris_observed,profile['crs'])
        disruption=flood.union(debris_geometry)
        network_observed=observed.intersection(debris_observed)
    g,affected,unknown=road_graph(roads,disruption,network_observed,profile['crs'],cfg['min_exposed_road_m'])
    access=reachability(g,infra['settlements'],infra['hub_node_ids'])
    pixel_area=abs(profile['transform'].a*profile['transform'].e-profile['transform'].b*profile['transform'].d)
    summary={'valid_pixels':int(valid.sum()),'total_pixels':int(valid.size),'new_water_pixels':int(new.sum()),'new_water_m2':float(new.sum()*pixel_area),
             'water_in_both_pixels':int((prediction==1).sum()),'mapped_buildings':sum(r['kind']=='building' for r in rows),
             'exposed_buildings':sum(r['kind']=='building' and r['exposed']>0 for r in rows),
             'exposed_road_m':sum(r['exposed'] for r in rows if r['kind'] in ('road','bridge')),
             'exposed_bridge_features':sum(r['kind']=='bridge' and r['exposed']>0 for r in rows),
             'connectivity_assessed':bool(infra['hub_node_ids']) and any(not x.get('boundary_truncated',True) for x in infra['settlements']),
             'potentially_cut_off':sum(r['status']=='potentially_cut_off' for r in access)}
    if debris_mask is not None:
        summary.update(debris_candidate_pixels=int((debris_mask==1).sum()),debris_candidate_m2=float((debris_mask==1).sum()*pixel_area),debris_valid_pixels=int((debris_mask!=255).sum()),debris_intersected_buildings=sum(r['kind']=='building' and r['exposed']>0 for r in debris_rows),debris_intersected_road_m=sum(r['exposed'] for r in debris_rows if r['kind'] in ('road','bridge')))
    sensitivity={}
    for name,mask in [('eroded_1px',binary_erosion(new)),('original',new),('dilated_1px',binary_dilation(new)&valid)]:
        f=mask_geometry(mask,profile['transform']); rr=exposure(infra['features'],f,observed,profile['crs'])
        sensitivity[name]={'exposed_buildings':sum(r['kind']=='building' and r['exposed']>0 for r in rr),'exposed_road_m':sum(r['exposed'] for r in rr if r['kind'] in ('road','bridge'))}
    out.mkdir(parents=True)
    if (root/'topology-audit.json').exists():
        import shutil
        shutil.copy2(root/'topology-audit.json',out/'topology-audit.json')
    meta={k:profile[k] for k in ('crs','transform','height','width')};meta.update(driver='GTiff',count=1,dtype='uint8',nodata=255,compress='deflate')
    with rasterio.open(out/'prediction.tif','w',**meta) as ds: ds.write(prediction,1)
    result={'run_id':out.name,'event_name':m['event_name'],'synthetic':m.get('synthetic',False),'summary':summary,'analysis':cfg,
            'classes':{'0':'no candidate under this heuristic','1':'water observed in both dates, not proven permanent','2':'new-water candidate','255':'invalid'},
            'limitations':['Fixed VV threshold baseline is uncalibrated and unvalidated for this event.','No debris classifier, optical pathway, radar layover mask or raw SAFE preprocessing.','Water in two observations is not proof of permanent water.','Nearest hub is selected by pre-event road distance; alternative hub access is reported separately.','Explicit node IDs required; settlement snapping and AOI completeness require preparation.','Templated reports are not an AI copilot.'],
            'provenance':{'manifest_sha256':digest(manifest_path),'infrastructure_sha256':digest(ipath),'prediction_sha256':digest(out/'prediction.tif')},'seconds':time.perf_counter()-start}
    result['limitations'].extend(m.get('limitations',[]))
    result['graph_disruption_basis']='water and debris candidates' if debris_mask is not None else 'water candidates'
    if debris_mask is not None:
        result['limitations']=[x for x in result['limitations'] if x!='No debris classifier, optical pathway, radar layover mask or raw SAFE preprocessing.']
        result['limitations'].append('Debris proxy is not a validated classifier; radar layover masking remains incomplete. Provider preprocessing is recorded in input provenance.')
        import shutil
        shutil.copy2(root/m['debris']['path'],out/'debris-candidates.tif')
        with (out/'debris-exposure.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(debris_rows[0]) if debris_rows else ['id','kind','exposed']);w.writeheader();w.writerows(debris_rows)
    write_json(out/'result.json',result); write_json(out/'manifest.json',m);write_json(out/'connectivity.json',access);write_json(out/'sensitivity.json',sensitivity)
    write_json(out/'graph.json',{'nodes':[{'id':n,'xy':d['xy']} for n,d in g.nodes(data=True)],'edges':[dict(d,u=u,v=v) for u,v,d in g.edges(data=True)],'affected':affected,'unknown':unknown})
    with (out/'exposure.csv').open('w',newline='',encoding='utf-8') as f:
        cols=['id','kind','total','observed','exposed','unit','exposed_fraction','coverage_fraction','status'];w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
    reproject=Transformer.from_crs(profile['crs'],'EPSG:4326',always_xy=True).transform
    layers=[]
    for f in infra['features']:
        layers.append(dict(f,geometry=mapping(transform_geometry(reproject,shape(f['geometry'])))))
    layers.append({'id':'new-water','type':'Feature','properties':{'kind':'new-water-candidate'},'geometry':mapping(transform_geometry(reproject,flood))})
    if debris_geometry is not None:
        layers.append({'id':'debris-candidates','type':'Feature','properties':{'kind':'debris-candidate'},'geometry':mapping(transform_geometry(reproject,debris_geometry))})
    write_json(out/'layers.geojson' ,{'type':'FeatureCollection','features':layers})
    for lang in ('en','ne'): (out/f'report-{lang}.html').write_text(report(result,lang),encoding='utf-8')
    # Identical fixed display stretch across dates; never used for classification.
    for period,array in [('pre',pre),('post',post)]:
        preview=np.clip((array[0]+30)/30*255,0,255).astype('uint8')
        preview[~valid]=0
        with rasterio.open(out/(period+'.png'),'w',driver='PNG',width=preview.shape[1],height=preview.shape[0],count=1,dtype='uint8') as ds:ds.write(preview,1)
    write_json(out/'freeze.json',{'files':{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()},'evaluation_started':False})
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('out');a=p.parse_args(); print(json.dumps(run(a.manifest,a.out),indent=2))
