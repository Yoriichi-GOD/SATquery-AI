"""Independent confusion/arithmetic checks and post-score reference-date audit."""
import argparse,json,sys,csv
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import rasterio,requests
from shapely.geometry import MultiLineString,shape
from shapely.ops import unary_union
from research.terrain_exposure.io import save_json,sha256

def band_index(order,method,count):
    if len(order)!=count or len(order)!=len(set(order)) or order[-1]!='valid':raise ValueError('Invalid prediction band declaration')
    if method not in order[:-1]:raise ValueError('Method not in saved prediction band declaration')
    return order.index(method)

def verify(root,output):
    root=Path(root);out=Path(output)
    if out.exists():raise FileExistsError('Keep earlier independent verification receipts')
    out.mkdir(parents=True)
    wf=root/'worldfloods-component-v1';protocol=json.loads((wf/'protocol.json').read_text())
    seal=json.loads((wf/'prediction-seal.json').read_text());summary=json.loads((wf/'summary.json').read_text())
    assert seal['all_selected_reference_pixels_unread'] and len(seal['predictions'])==6 and not seal['failures']
    totals={method:np.zeros(4,dtype='int64') for method in protocol['methods']};eventrows=[];dates=[]
    for identity in protocol['ids']:
        folder=wf/identity;assert sha256(folder/'predictions-and-valid.tif')==seal['predictions'][identity]['prediction_sha256']
        with rasterio.open(folder/'predictions-and-valid.tif') as s:p=s.read();grid=(s.shape,s.transform,s.crs)
        with rasterio.open(folder/'reference.tif') as s:y=s.read();assert grid==(s.shape,s.transform,s.crs)
        common=(p[-1]==1)&(y[0]==1)&np.isin(y[1],[1,2]);truth=y[1]==2
        for method in protocol['methods']:
            i=band_index(seal['predictions'][identity]['method_band_order'],method,len(p))
            # Independent4-bin encoding:00TN,01FN,10FP,11TP.
            codes=p[i][common].astype(int)*2+truth[common].astype(int);bins=np.bincount(codes,minlength=4)
            counts={'tp':int(bins[3]),'fp':int(bins[2]),'fn':int(bins[1]),'tn':int(bins[0])}
            stored=summary['events'][identity]['metrics'][method]
            assert all(stored[k]==v for k,v in counts.items())
            totals[method]+=np.array([counts[k] for k in ['tp','fp','fn','tn']])
            denom=counts['tp']+counts['fp']+counts['fn'];iou=None if not denom else counts['tp']/denom
            assert iou==stored['iou'];eventrows.append({'id':identity,'method':method,**counts,'iou':iou,'common_pixels':int(common.sum())})
        # Source metadata read only after all selected annotation scoring; never feeds selection/prediction.
        url=f"https://huggingface.co/datasets/{protocol['dataset']}/resolve/{protocol['revision']}/test/meta/{identity}.json"
        r=requests.get(url,timeout=35);r.raise_for_status();metadata=r.json();save_json(out/(identity+'-metadata.json'),metadata)
        ds,dr=metadata.get('s2_date'),metadata.get('satellite date');lag=None
        if ds and dr:
            lag=(datetime.fromisoformat(ds.replace('Z','+00:00'))-datetime.fromisoformat(dr.replace('Z','+00:00'))).total_seconds()/86400
        dates.append({'id':identity,'optical_date':ds,'reference_source_date':dr,'source_sensor':metadata.get('satellite'),
            'optical_minus_reference_days':lag,'reference_source':metadata.get('source'),'reference_encoding':metadata.get('encoding_values'),
            'independence_limit':'Curatedbenchmarkcombinesflood/hydrology/JRC;neitherfieldtruthnorcaseexposurelabels'})
    for method,counts in totals.items():
        actual=summary['totals'][method];assert all(int(counts[i])==actual[k] for i,k in enumerate(['tp','fp','fn','tn']))
    with (out/'independent-event-counts.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(eventrows[0]));w.writeheader();w.writerows(eventrows)
    save_json(out/'reference-date-audit.json',dates)
    # Independently reconstruct the official drainage union, using only the declared native layer.
    ref=root/'delhi-official-v1';a=json.loads((ref/'acquisition.json').read_text())
    record=next(r for r in a['layers'] if r['service']=='DIFC/sangam' and r['layer_id']==3)
    assert sha256(ref/record['file'])==record['sha256']
    raw=json.loads((ref/record['file']).read_text());lines=[]
    from research.cases.process_campaign import roi_geometry
    roi=shape(roi_geometry([77.225,28.47,77.28,28.51],'EPSG:32643'))
    for row in raw['features']:lines.extend([line.intersection(roi) for line in [MultiLineString(row['geometry']['paths'])]])
    union=unary_union(lines)
    receipt={'status':'PASS','external_events_recounted':6,'external_method_rows_recomputed':len(eventrows),
        'common_pixels':summary['totals']['MNDWI0']['n'],'prediction_seal_sha256':sha256(wf/'prediction-seal.json'),
        'official_drain_query_features':len(raw['features']),'independent_unique_clipped_drain_length_m':union.length,
        'scope':'Stored input/prediction/reference integrity and independent counts; not expert review or groundtruth certification'}
    save_json(out/'summary.json',receipt);print(json.dumps(receipt))
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sources',required=True);p.add_argument('--output',required=True);a=p.parse_args();verify(a.sources,a.output)
