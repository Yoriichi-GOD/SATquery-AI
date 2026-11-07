"""Sealed image-first external water-component test. Not full exposure validation."""
import argparse,json,math,csv,logging
from pathlib import Path
from urllib.parse import urlsplit
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.warp import transform_bounds,reproject,Resampling
from rasterio.transform import array_bounds
from research.datasets.cog import acquire
from research.cases.process_campaign import metric_grid,warp
from research.terrain_exposure.hydrology import slope_aspect
from research.terrain_exposure.io import Grid,save_json,sha256,canonical_hash

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'research/experiments/worldfloods-blind-20261107.json'

def central_window(shape,size=512):
    if min(shape)<size:raise ValueError('Frozen test window does not fit source; no alternate sample')
    return Window((shape[1]-size)//2,(shape[0]-size)//2,size,size)

def write_window(path,values,grid):
    values=np.asarray(values)
    if values.ndim==2:values=values[None]
    with rasterio.open(path,'w',driver='GTiff',height=grid.shape[0],width=grid.shape[1],count=len(values),
        crs=grid.crs,transform=grid.transform,dtype=str(values.dtype),compress='deflate') as dst:dst.write(values)

def remote_window(url,path,bands,window=None,expected_grid=None):
    if not url.startswith('https://huggingface.co/datasets/isp-uv-es/WorldFloodsv2/resolve/'):raise ValueError('Unapproved benchmark URL')
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_HTTP_TIMEOUT='40',GDAL_HTTP_MAX_RETRY='2',
        GDAL_CACHEMAX=64,CPL_VSIL_CURL_CHUNK_SIZE=16384):
        with rasterio.open(url) as src:
            if not src.is_tiled:raise ValueError('Frozen benchmark requires bounded tiled raster access')
            if any(h*w*src.count*np.dtype(src.dtypes[0]).itemsize>32*1024*1024 for h,w in src.block_shapes):
                raise ValueError('Native remote decode block exceeds declared budget')
            if src.crs is None or any(b>src.count for b in bands):raise ValueError('Benchmark bands/CRS unavailable')
            window=window or central_window(src.shape)
            grid=Grid((int(window.height),int(window.width)),src.window_transform(window),src.crs.to_string())
            if expected_grid and grid!=expected_grid:raise ValueError('Input/reference native grids differ; no silent alignment')
            data=src.read(bands,window=window)
            receipt={'source_url':url,'source_shape':list(src.shape),'source_bands':src.count,'selected_bands':bands,
                'window':list(window.flatten()),'grid':grid.describe(),'native_block_shapes':[list(s) for s in src.block_shapes],
                'reference_product':'WorldFloodsv2@1f3faa2989e69930ac31d5c0a79fd224461123f8',
                'license':'CC-BY-NC4.0','resampling':'None;nativewindow','full_remote_checksum':'NOT_ASSERTED'}
    write_window(path,data,grid);receipt['sha256']=sha256(path);receipt['bytes']=path.stat().st_size
    save_json(path.with_suffix('.source.json'),receipt)
    return data,grid,window

def spectral_predictions(data,slope):
    green,nir,swir=data.astype(float)
    valid=np.isfinite(data).all(0)&(data>0).all(0)&np.isfinite(slope)&(abs(green+nir)>1e-8)&(abs(green+swir)>1e-8)
    ndwi=np.divide(green-nir,green+nir,out=np.full(green.shape,np.nan),where=valid)
    mndwi=np.divide(green-swir,green+swir,out=np.full(green.shape,np.nan),where=valid)
    return {'MNDWI0':valid&(mndwi>0),'NDWI0':valid&(ndwi>0),'MNDWI0_slope15':valid&(mndwi>0)&(slope<=15),
        'all_land':np.zeros(valid.shape,bool),'all_water':valid.copy()},valid

def confusion(pred,label,valid):
    p=np.asarray(pred,bool);y=np.asarray(label,bool);v=np.asarray(valid,bool)
    if p.shape!=y.shape or y.shape!=v.shape:raise ValueError('Metric arrays differ')
    return {name:int(m.sum()) for name,m in {'tp':p&y&v,'fp':p&~y&v,'fn':~p&y&v,'tn':~p&~y&v}.items()}

def ratios(counts):
    tp,fp,fn,tn=[counts[k] for k in ['tp','fp','fn','tn']]
    div=lambda n,d:None if d==0 else n/d
    return {**counts,'n':tp+fp+fn+tn,'iou':div(tp,tp+fp+fn),'f1':div(2*tp,2*tp+fp+fn),
        'precision':div(tp,tp+fp),'recall':div(tp,tp+fn),'accuracy':div(tp+tn,tp+fp+fn+tn)}

def run(output):
    out=Path(output)
    if out.exists():raise FileExistsError('The declared external test is single-run; keep failures and scores immutable')
    out.mkdir(parents=True);protocol=json.loads(PROTOCOL.read_text());save_json(out/'protocol.json',protocol)
    logging.getLogger('rasterio').setLevel(logging.CRITICAL)
    base=f"https://huggingface.co/datasets/{protocol['dataset']}/resolve/{protocol['revision']}/test"
    predictions={};receipts={};grids={};windows={};failures=[]
    save_json(out/'population-seal.json',{'ids':protocol['ids'],'protocol_sha256':sha256(PROTOCOL),
        'annotation_pixel_values_read':False,'selection':'Fixed before source/label pixels; no replacement of failed examples'})
    for identity in protocol['ids']:
        folder=out/identity;folder.mkdir()
        try:
            data,grid,window=remote_window(f'{base}/S2/{identity}.tif',folder/'input.tif',[3,8,12])
            bounds=transform_bounds(grid.crs,'EPSG:4326',*array_bounds(*grid.shape,grid.transform),densify_pts=21)
            cfg={'bbox':list(bounds),'crs':grid.crs};demfiles=[]
            # Small30mmetric grid surrounds the native test footprint; no label values used.
            for lat in range(math.floor(bounds[1]),math.ceil(bounds[3])):
                for lon in range(math.floor(bounds[0]),math.ceil(bounds[2])):
                    tile=f'Copernicus_DSM_COG_10_{"N" if lat>=0 else "S"}{abs(lat):02d}_00_{"E" if lon>=0 else "W"}{abs(lon):03d}_00_DEM'
                    path=folder/f'dem-{lat}-{lon}.tif'
                    acquire(f'https://copernicus-dem-30m.s3.amazonaws.com/{tile}/{tile}.tif',bounds,path,
                        license_url='https://registry.opendata.aws/copernicus-dem/',product='CopernicusGLO30',max_pixels=4_000_000)
                    demfiles.append(path)
            terrain_grid=metric_grid(cfg,30);z=warp(demfiles,terrain_grid,Resampling.bilinear)
            slope,_=slope_aspect(z,np.isfinite(z),terrain_grid);target_slope=np.full(grid.shape,np.nan)
            reproject(slope,target_slope,src_transform=terrain_grid.transform,src_crs=terrain_grid.crs,src_nodata=np.nan,
                dst_transform=grid.transform,dst_crs=grid.crs,dst_nodata=np.nan,resampling=Resampling.bilinear)
            methods,valid=spectral_predictions(data,target_slope)
            names=list(protocol['methods']);stack=np.stack([methods[n] for n in names]+[valid]).astype('uint8')
            write_window(folder/'predictions-and-valid.tif',stack,grid)
            write_window(folder/'slope-context.tif',target_slope.astype('float32'),grid)
            predictions[identity]=(methods,valid);grids[identity]=grid;windows[identity]=window
            receipts[identity]={'prediction_sha256':sha256(folder/'predictions-and-valid.tif'),
                'input_sha256':sha256(folder/'input.tif'),'slope_sha256':sha256(folder/'slope-context.tif'),
                'method_band_order':names+['valid'],'reference_pixels_read':False}
            print(json.dumps({'id':identity,'phase':'PREDICTIONS_SEALED','input_valid_pixels':int(valid.sum())}),flush=True)
        except Exception as exc:
            failures.append({'id':identity,'phase':'INPUT_OR_PREDICTION','error_type':type(exc).__name__})
            print(json.dumps(failures[-1]),flush=True)
    save_json(out/'prediction-seal.json',{'protocol_sha256':sha256(PROTOCOL),'predictions':receipts,'failures':failures,
        'all_selected_reference_pixels_unread':True})
    sealhash=sha256(out/'prediction-seal.json');events={}
    for identity,(methods,support) in predictions.items():
        folder=out/identity
        try:
            assert sha256(folder/'predictions-and-valid.tif')==receipts[identity]['prediction_sha256']
            label,_,_=remote_window(f'{base}/gt/{identity}.tif',folder/'reference.tif',[1,2],windows[identity],grids[identity])
            if not np.isin(label,[0,1,2]).all():raise ValueError('Unexpected benchmark reference encoding')
            valid=support&(label[0]==1)&np.isin(label[1],[1,2]);truth=label[1]==2
            metrics={name:ratios(confusion(pred,truth,valid)) for name,pred in methods.items()}
            events[identity]={'population':'NEW_WORKSPACE_FIXED_TOTAL_WATER_COMPONENT_TEST','pixels':int(valid.sum()),
                'reference_clear_pixels':int(((label[0]==1)&np.isin(label[1],[1,2])).sum()),
                'total_window_pixels':int(valid.size),'reference_water_pixels':int((truth&valid).sum()),
                'metrics':metrics,'prediction_seal_sha256':sealhash,'reference_sha256':sha256(folder/'reference.tif'),
                'terrain_common_support_fraction':float(valid.sum()/valid.size)}
            save_json(folder/'metrics.json',events[identity]);draw(folder,label,methods,valid)
            print(json.dumps({'id':identity,'phase':'SCORED','common_pixels':int(valid.sum()),'MNDWI_IoU':metrics['MNDWI0']['iou'],
                'terrain_IoU':metrics['MNDWI0_slope15']['iou']}),flush=True)
        except Exception as exc:
            failures.append({'id':identity,'phase':'REFERENCE_OR_SCORE','error_type':type(exc).__name__})
            print(json.dumps(failures[-1]),flush=True)
    totals={}
    for name in protocol['methods']:
        counts={k:sum(e['metrics'][name][k] for e in events.values()) for k in ['tp','fp','fn','tn']}
        vals=[e['metrics'][name]['iou'] for e in events.values() if e['metrics'][name]['iou'] is not None]
        totals[name]={**ratios(counts),'macro_event_iou':None if not vals else float(np.mean(vals)),'macro_eligible_events':len(vals)}
    summary={'dataset':protocol['dataset'],'revision':protocol['revision'],'selected_events':len(protocol['ids']),
        'scored_events':len(events),'failed_events':failures,'events':events,'totals':totals,'prediction_seal_sha256':sealhash,
        'scope':'Curated total-water component agreement on fixed small native windows;notnewwater,exposure,fullA–D,casevalidationorfieldtruth',
        'terrain_aggregation':'Single common support across all methods; no selection by labelwater or scores',
        'training':False,'tuning':False,'label_dates_and_quality':'WorldFloodsv2 reference polygons/hydrology/JRC; optical/reference temporal misalignment may affect agreement',
        'independence':'Newly selected across6public test activations; bounded local history search found no priorWorldFloodsevaluation. Upstream global exposure unknown.'}
    save_json(out/'summary.json',summary)
    with (out/'metrics.csv').open('w',newline='') as f:
        fields=['method','tp','fp','fn','tn','n','iou','f1','precision','recall','accuracy','macro_event_iou','macro_eligible_events']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({'method':n,**v} for n,v in totals.items())
    save_json(out/'manifest.json',{'files':{p.relative_to(out).as_posix():sha256(p) for p in out.rglob('*') if p.is_file()}})
    return summary

def draw(folder,label,methods,valid):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    panels={'Reference totalwater':label[1]==2,**{n:methods[n] for n in ['MNDWI0','NDWI0','MNDWI0_slope15']}}
    fig,axes=plt.subplots(1,4,figsize=(12,3.6),layout='constrained')
    cmap=plt.get_cmap('Blues').copy();cmap.set_bad('#ddd')
    for ax,(name,data) in zip(axes,panels.items()):
        ax.imshow(np.where(valid,data,np.nan),cmap=cmap,vmin=0,vmax=1,interpolation='nearest');ax.set_title(name,fontsize=9);ax.axis('off')
    fig.suptitle(folder.name+'\nFixedcenter512pxwindow;gray=excluded;curatedwaterreference,notexposuretruth',fontsize=9)
    fig.savefig(folder/'comparison.png',dpi=160);plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(a.output)
