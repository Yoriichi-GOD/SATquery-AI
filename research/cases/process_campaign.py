"""Reproducible measurements on declared case windows, never accuracy without labels."""
from __future__ import annotations
import argparse,csv,json,math,time
from pathlib import Path
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import reproject,Resampling,transform_bounds,transform_geom
from affine import Affine
from research.terrain_exposure.io import Grid,save_json,sha256,write_raster,resolution_status
from research.terrain_exposure.hydrology import derive
from research.registration.diagnostics import audit
from research.cases.acquire_campaign import PROTOCOL

CLASSES={1:'water',2:'trees',4:'flooded_vegetation',5:'crops',7:'built',8:'bare',9:'snow',11:'rangeland'}

def roi_geometry(bbox,crs):
    w,s,e,n=bbox;steps=64
    ring=[(x,s) for x in np.linspace(w,e,steps)]+[(e,y) for y in np.linspace(s,n,steps)]
    ring += [(x,n) for x in np.linspace(e,w,steps)]+[(w,y) for y in np.linspace(n,s,steps)]+[(w,s)]
    return transform_geom('EPSG:4326',crs,{'type':'Polygon','coordinates':[ring]})

def roi(bbox,shape,transform,crs):
    return geometry_mask([roi_geometry(bbox,crs)],shape,transform,invert=True)

def metric_grid(cfg,cell):
    l,b,r,t=transform_bounds('EPSG:4326',cfg['crs'],*cfg['bbox'],densify_pts=64)
    l,b=math.floor(l/cell)*cell,math.floor(b/cell)*cell
    r,t=math.ceil(r/cell)*cell,math.ceil(t/cell)*cell
    return Grid((round((t-b)/cell),round((r-l)/cell)),Affine(cell,0,l,0,-cell,t),cfg['crs'])

def warp(paths,grid,method=Resampling.nearest):
    result=np.full(grid.shape,np.nan)
    for path in sorted(paths):
        with rasterio.open(path) as src:
            data=src.read(1,masked=True).astype('float64').filled(np.nan)
            values=np.full(grid.shape,np.nan)
            reproject(data,values,src_transform=src.transform,src_crs=src.crs,src_nodata=np.nan,
                      dst_transform=grid.transform,dst_crs=grid.crs,dst_nodata=np.nan,resampling=method)
            result[np.isfinite(values)]=values[np.isfinite(values)]
    return result

def transitions(before,after,valid,pixel_area):
    if before.shape!=after.shape or valid.shape!=before.shape:raise ValueError('Transition grids differ')
    known=np.array(list(CLASSES))
    if not np.isin(before[valid],known).all() or not np.isin(after[valid],known).all():raise ValueError('Unknown class on valid support')
    count=lambda m:int((m&valid).sum())
    stock0=count(before==7);stock1=count(after==7)
    gain=count((before!=7)&(after==7));loss=count((before==7)&(after!=7))
    if stock1-stock0!=gain-loss:raise AssertionError('Urban stock-flow conservation failed')
    return {'common_pixels':int(valid.sum()),'pixel_area_m2':float(pixel_area),'common_area_ha':float(valid.sum()*pixel_area/10000),
        'built_before_ha':stock0*pixel_area/10000,'built_after_ha':stock1*pixel_area/10000,
        'gross_built_gain_ha':gain*pixel_area/10000,'gross_built_loss_ha':loss*pixel_area/10000,
        'net_built_difference_ha':(gain-loss)*pixel_area/10000,
        'water_before_ha':count(before==1)*pixel_area/10000,'water_after_ha':count(after==1)*pixel_area/10000,
        'transition_pixels':{f'{a}:{b}':count((before==a)&(after==b)) for a in CLASSES for b in CLASSES}}

def safe_stats(values):
    v=np.asarray(values);v=v[np.isfinite(v)]
    return {'n':int(v.size),'median':None if not v.size else float(np.median(v)),
            'p10':None if not v.size else float(np.percentile(v,10)),
            'p90':None if not v.size else float(np.percentile(v,90))}

def landsat_clear(qa,sat,valid):
    return valid & ((qa.astype('uint16')&63)==0)&(sat==0)

def index(a,b,valid):
    result=np.full(a.shape,np.nan);ok=valid&np.isfinite(a)&np.isfinite(b)&(abs(a+b)>1e-8)
    result[ok]=(a[ok]-b[ok])/(a[ok]+b[ok]);return result

def declared_terrain_files(folder,records,historical=False):
    prefix='nasadem-' if historical else 'dem30-'
    names=[r['file'] for r in records if r['state']=='ACQUIRED' and r['label'].startswith(prefix)]
    if any(Path(name).name!=name for name in names):raise ValueError('Unsafe registered terrain filename')
    return [Path(folder)/name for name in names]

def terrain(folder,cfg,out,protocol,records):
    result={};hydros={}
    for cell in protocol['terrain']['comparison_pixel_m']:
        g=metric_grid(cfg,cell);inside=roi(cfg['bbox'],g.shape,g.transform,g.crs)
        files=declared_terrain_files(folder,records,True) if folder.name=='kedarnath' else []
        historical=bool(files)
        if not files:files=declared_terrain_files(folder,records)
        if not files:raise ValueError('No registered terrain sources')
        z=warp(files,g,Resampling.bilinear);valid=np.isfinite(z)&inside
        h=derive(z,valid,g,protocol['terrain']['stream_area_m2'],protocol['terrain']['conditioning'])
        write_raster(out/f'dem-{cell}m.tif',z,g,valid)
        write_raster(out/f'hand-{cell}m.tif',h.hand,g,np.isfinite(h.hand)&valid)
        write_raster(out/f'slope-{cell}m.tif',h.slope,g,np.isfinite(h.slope)&valid)
        result[str(cell)]={'grid':g.describe(),'hydrology':h.summary,'elevation_m':safe_stats(z[valid]),
            'slope_degrees':safe_stats(h.slope[valid]),'hand_m':safe_stats(h.hand[valid]),
            'source_product':'NASADEM_HGT_v001' if historical else 'CopernicusGLO30',
            'source_information_scale_m':30,'analysis_pixel_m':cell,
            'street_scale_gate':resolution_status(cell,10 if folder.name=='nepal' else 5),
            'historical_role':'SRTM2000-derived reprocessing; not June2013 surface' if historical else 'Modern DSM; event-time terrain not certified'}
        hydros[cell]=h
    return result,hydros

def urban(folder,cfg,out,h):
    with rasterio.open(folder/'lulc-2017.tif') as a,rasterio.open(folder/'lulc-2023.tif') as b:
        if a.shape!=b.shape or a.crs!=b.crs or a.transform!=b.transform:raise ValueError('Native annual grids differ')
        x,y=a.read(1),b.read(1);inside=roi(cfg['bbox'],a.shape,a.transform,a.crs)
        valid=inside&(a.read_masks(1)>0)&(b.read_masks(1)>0)&~np.isin(x,[0,10])&~np.isin(y,[0,10])
        result=transitions(x,y,valid,abs(a.transform.a*a.transform.e))
        result.update(roi_pixels=int(inside.sum()),common_fraction_of_roi=float(valid.sum()/inside.sum()),
            measurement='Native10m annual model class transitions2017–2023, not verified physical change',
            native_crs=a.crs.to_string(),native_transform=list(a.transform)[:6])
        with (out/'transition-matrix.csv').open('w',newline='') as f:
            writer=csv.writer(f);writer.writerow(['before_class','after_class','pixels','hectares'])
            for key,n in result['transition_pixels'].items():writer.writerow([*key.split(':'),n,n*.01])
    g=h.grid;v=roi(cfg['bbox'],g.shape,g.transform,g.crs)
    a=warp([folder/'lulc-2017.tif'],g);b=warp([folder/'lulc-2023.tif'],g)
    common=v&np.isin(a,list(CLASSES))&np.isin(b,list(CLASSES));gain=common&(a!=7)&(b==7)
    write_raster(out/'urban-gain-30m.tif',gain.astype(float),g,common)
    result['terrain_conditioned_gain_context']={'analysis_grid_m':30,'gain_sampled_cells':int(gain.sum()),
        'slope_degrees':safe_stats(h.slope[gain]),'hand_m':safe_stats(h.hand[gain]),
        'interpretation':'Descriptive topographic context of resampled class gains; no validated exposure labels or drain survey'}
    contexts={}
    for year in [2020,2021]:
        wc=warp([folder/f'worldcover-{year}.tif'],g);ok=v&np.isfinite(wc)&(wc!=0)
        contexts[str(year)]={'valid_area_ha':float(ok.sum()*g.area/10000),
            'built_area_ha':float(((wc==50)&ok).sum()*g.area/10000),
            'water_area_ha':float(((wc==80)&ok).sum()*g.area/10000)}
    result['worldcover_context_30m_nearest']=contexts
    result['worldcover_temporal_difference']='NOT_REPORTED:2020v100 and2021v200 algorithms differ'
    for key in ['occurrence','seasonality']:
        j=warp([folder/f'jrc-{key}.tif'],g);ok=v&np.isfinite(j)&(j!=255)
        result['jrc_'+key]={'valid_cells':int(ok.sum()),'valid_area_ha':float(ok.sum()*g.area/10000),
            'nonzero_area_ha':float(((j>0)&ok).sum()*g.area/10000),'values':safe_stats(j[ok]),
            'role':'1984–2024 historical water context' if key=='occurrence' else '2024 seasonal water context; not event truth'}
    return result,{'2017 annual classes':a,'2023 annual classes':b,'Built class gains (30m sampling)':np.where(common,gain,np.nan),
                   'Elevation (m)':np.where(h.valid,h.original,np.nan),'Slope (degrees)':h.slope,'HAND (m; model)':h.hand}

def historical(folder,cfg,out,h,protocol):
    g=h.grid;inside=roi(cfg['bbox'],g.shape,g.transform,g.crs);bands={};clear={};metrics={}
    for epoch in ['before','after']:
        bands[epoch]={k:warp([folder/f'landsat-{epoch}-{k}.tif'],g) for k in protocol['landsat']['bands']}
        d=bands[epoch];valid=inside.copy()
        for band in d.values():valid&=np.isfinite(band)
        qa=np.nan_to_num(d['qa_pixel']);sat=np.nan_to_num(d['qa_radsat'])
        clear[epoch]=landsat_clear(qa,sat,valid)
        for k in ['blue','green','red','nir08','swir16','swir22']:
            d[k]=d[k]*protocol['landsat']['reflectance_scale']+protocol['landsat']['reflectance_offset']
        metrics[epoch]={'valid_pixels':int(valid.sum()),'qa_clear_pixels':int(clear[epoch].sum()),
            'clear_fraction_of_roi':float(clear[epoch].sum()/inside.sum())}
    common=clear['before']&clear['after'];a,b=bands['before'],bands['after']
    nd0=index(a['nir08'],a['red'],common);nd1=index(b['nir08'],b['red'],common)
    water0=index(a['green'],a['swir16'],common);water1=index(b['green'],b['swir16'],common)
    water_valid=common&np.isfinite(water0)&np.isfinite(water1)
    veg_valid=common&np.isfinite(nd0)&np.isfinite(nd1)
    water=water_valid&(water1>0)&(water0<=0)
    loss=veg_valid&(nd0>.4)&(nd1<.2)&((nd0-nd1)>=.25)
    reg=audit(a['red'],b['red'],clear['before'],clear['after'],g,g)
    save_json(out/'registration.json',reg)
    for name,candidate,valid in [('new-water-proxy',water,water_valid),('vegetation-loss-proxy',loss,veg_valid)]:
        write_raster(out/(name+'.tif'),candidate.astype(float),g,valid)
        metrics[name]={'candidate_pixels':int(candidate.sum()),'valid_pixels':int(valid.sum()),
            'area_ha':float(candidate.sum()*g.area/10000),'valid_area_ha':float(valid.sum()*g.area/10000),
            'registration_status':reg['status'],'interpretation':'Fixed spectral proxy; not confirmed flood/debris or damage'}
    metrics.update(roi_pixels=int(inside.sum()),roi_area_ha=float(inside.sum()*g.area/10000),
        common_clear_pixels=int(common.sum()),common_clear_fraction=float(common.sum()/inside.sum()),
        before_date=cfg['before'],after_date=cfg['after'],registration=reg,
        exposure_validation='NOT_ASSESSED:historical matched receptor inventory and class-compatible event reference absent',
        event_timing='Postevent June23 does not observe peak June16–17 inundation')
    return metrics,{'Before red reflectance':np.where(clear['before'],a['red'],np.nan),
        'After red reflectance':np.where(clear['after'],b['red'],np.nan),
        'Common clear support':np.where(inside,common,np.nan),'New water proxy':np.where(water_valid,water,np.nan),
        'Vegetation loss proxy':np.where(veg_valid,loss,np.nan),'Historical terrain (m)':np.where(h.valid,h.original,np.nan)}

def figure(panels,out,title):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(13,8),layout='constrained')
    for ax,(name,data) in zip(axes.ravel(),panels.items()):
        cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#d9d9d9')
        binary=any(key in name.lower() for key in ['proxy','gains','support'])
        im=ax.imshow(data,cmap=cmap,interpolation='nearest',**({'vmin':0,'vmax':1} if binary else {}))
        ax.set_title(name,fontsize=10);ax.set_xticks([]);ax.set_yticks([])
        fig.colorbar(im,ax=ax,shrink=.7,**({'ticks':[0,1]} if binary else {}))
    fig.suptitle(title+' — gray = unavailable; model/proxy results, not ground truth',fontsize=11)
    fig.savefig(out/'case-panels.png',dpi=160);plt.close(fig)

def process(sources,output,cases=None):
    protocol=json.loads(PROTOCOL.read_text());output=Path(output)
    if output.exists():raise FileExistsError('Choose a fresh immutable result folder')
    output.mkdir(parents=True);summary={}
    save_json(output/'protocol.json',protocol)
    for case,cfg in protocol['cases'].items():
        if cases and case not in cases:continue
        start=time.monotonic();folder=Path(sources)/case;out=output/case;out.mkdir()
        acquisition=json.loads((folder/'acquisition.json').read_text());inputs=[]
        for item in acquisition['assets']:
            if item['state']!='ACQUIRED':continue
            file=folder/item['file']
            if sha256(file)!=item['receipt']['sha256']:raise ValueError('Source checksum failed')
            inputs.append({'filename':file.name,**item['receipt']})
        save_json(out/'sources.json',{'case_id':case,'inputs':inputs,'missing':[i for i in acquisition['assets'] if i['state']!='ACQUIRED']})
        tr,hydros=terrain(folder,cfg,out,protocol,acquisition['assets'])
        result={'case_id':case,'bbox':cfg['bbox'],'boundary_role':cfg['role'],'terrain':tr,
            'protocol_sha256':sha256(PROTOCOL),'accuracy_metrics':'NOT_ASSESSED:no compatible independent targets',
            'limitations':['Finite exploratory ROI; external contributing area unavailable','DSM routes do not model culverts, urban sewers, hydraulic depth or debris physics']}
        if case in ['varanasi','sangam-vihar']:result['urban'],panels=urban(folder,cfg,out,hydros[30])
        elif case=='kedarnath':result['historical'],panels=historical(folder,cfg,out,hydros[30],protocol)
        else:
            panels={'Elevation30m':hydros[30].original,'Slope30m':hydros[30].slope,'HAND30m':hydros[30].hand,
                'Elevation90m':hydros[90].original,'Slope90m':hydros[90].slope,'HAND90m':hydros[90].hand}
        figure(panels,out,case)
        if case=='kedarnath':rgb_figure(folder,cfg,out,hydros[30].grid,protocol)
        result['seconds']=time.monotonic()-start;save_json(out/'summary.json',result)
        save_json(out/'manifest.json',{'files':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})
        summary[case]=result;print(json.dumps({'case':case,'state':'MEASURED_NOT_VALIDATED','seconds':round(result['seconds'],2)}),flush=True)
    save_json(output/'summary.json',summary)
    return summary

def rgb_figure(folder,cfg,out,g,protocol):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    inside=roi(cfg['bbox'],g.shape,g.transform,g.crs);images={};masks={}
    for epoch in ['before','after']:
        dn=np.stack([warp([folder/f'landsat-{epoch}-{b}.tif'],g) for b in ['red','green','blue']],axis=-1)
        images[epoch]=dn*protocol['landsat']['reflectance_scale']+protocol['landsat']['reflectance_offset']
        qa=warp([folder/f'landsat-{epoch}-qa_pixel.tif'],g);sat=warp([folder/f'landsat-{epoch}-qa_radsat.tif'],g)
        masks[epoch]=landsat_clear(np.nan_to_num(qa),np.nan_to_num(sat),inside&np.isfinite(dn).all(axis=-1)&np.isfinite(qa)&np.isfinite(sat))
    values=np.concatenate([im[inside&np.isfinite(im).all(axis=-1)].ravel() for im in images.values()])
    lo,hi=np.percentile(values,[2,98]);fig,axes=plt.subplots(2,2,figsize=(8,9),layout='constrained')
    for col,epoch in enumerate(['before','after']):
        rgb=np.clip((images[epoch]-lo)/max(hi-lo,1e-8),0,1)
        for row,mask in enumerate([inside&np.isfinite(rgb).all(axis=-1),masks[epoch]]):
            display=np.where(mask[...,None],rgb,.8)
            axes[row,col].imshow(display,interpolation='nearest');axes[row,col].set_xticks([]);axes[row,col].set_yticks([])
            axes[row,col].set_title(f"{cfg[epoch]} {'RGB' if row==0 else 'QA clear only'}",fontsize=10)
    fig.suptitle('Landsat8 surface reflectance: same2–98% display stretch\nGray = excluded/NoData; color is illustrative, not a change classifier',fontsize=10)
    fig.savefig(out/'optical-rgb.png',dpi=160);plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sources',required=True);p.add_argument('--output',required=True);p.add_argument('--case',action='append')
    a=p.parse_args();process(a.sources,a.output,a.case)
