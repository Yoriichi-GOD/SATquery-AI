"""Two observed dates; deterministic indices, never flood/urban ground truth."""
import re,time,json,hashlib
from pathlib import Path
from datetime import datetime
import numpy as np
import rasterio
from PIL import Image, ImageDraw, ImageFont
VERSION='spectral-pair-v1'
FORMULAS={'vegetation':'(NIR-Red)/(NIR+Red)','water':'(Green-NIR)/(Green+NIR)'}
ALIASES={'red':'red','b04':'red','green':'green','b03':'green','nir':'nir','b08':'nir','scl':'scl','blue':'blue','b02':'blue'}

def comparison_panel(frames, captions):
    h,w=frames[0].shape[:2]
    footer=max(64,int(w*.16));canvas=Image.new('RGB',(w*len(frames),h+footer),(16,16,16));draw=ImageDraw.Draw(canvas)
    try:font=ImageFont.truetype('DejaVuSans.ttf',max(12,int(w*.035)))
    except OSError:font=ImageFont.load_default()
    for i,(frame,lines) in enumerate(zip(frames,captions)):
        canvas.paste(Image.fromarray(frame),(i*w,0))
        for j,line in enumerate(lines):
            box=draw.textbbox((0,0),line,font=font);width=box[2]-box[0]
            draw.text((i*w+(w-width)/2,h+8+j*max(18,int(w*.045))),line,font=font,fill=(230,223,200))
    return canvas

def requested(query):
    q=' '.join(query.lower().strip().rstrip('.!?').split())
    broad=bool(re.fullmatch(r'(?:please )?(?:analy[sz]e|compare) (?:these |the |both )?(?:two )?(?:images|dates|observations)(?: comprehensively| in detail)?',q))
    tasks=[]
    if broad or re.search(r'\b(ndvi|vegetation)\b',q):tasks.append('vegetation')
    if broad or re.search(r'\b(ndwi|water)\b',q):tasks.append('water')
    return tasks,broad

def validate(records):
    if len(records)!=2 or any(r['modality']!='optical' for r in records):raise ValueError('Spectral comparison requires two optical surface-reflectance GeoTIFFs, earlier date first.')
    loaded=[];dates=[]
    for r in records:
        with rasterio.open(r['path']) as ds:
            tags=ds.tags()
            if tags.get('reflectance_units')!='surface_reflectance':raise ValueError('Both dates require declared surface_reflectance calibration and real spectral bands. RGB or L1C products cannot substitute.')
            if not tags.get('sensor'):raise ValueError('Declare the actual sensor in both TIFF metadata records; cross-sensor spectral comparison is not supported.')
            date=tags.get('acquisition_date') or tags.get('acquired') or r.get('date','')
            if r.get('date') and r['date']!=date:raise ValueError('Entered date conflicts with source acquisition metadata.')
            try:dates.append(datetime.strptime(date,'%Y-%m-%d'))
            except (ValueError,TypeError):raise ValueError('Provide actual acquisition dates in YYYY-MM-DD, earlier image first.')
            mapping={}
            for i,b in enumerate(ds.descriptions,1):
                key=ALIASES.get((b or '').lower())
                if key in mapping:raise ValueError('Duplicate spectral band identities; provide unambiguous band labels.')
                if key:mapping[key]=i
            if 'scl' not in mapping:raise ValueError('This comparison requires a Sentinel-2 SCL quality band on each grid to exclude clouds, shadows and invalid pixels. Supply genuine SCL labels; do not fabricate a clear mask.')
            if tags['sensor'] not in ['Sentinel-2','Sentinel-2 L2A']:raise ValueError('Initial spectral comparison supports Sentinel-2 surface reflectance with SCL only.')
            if not ds.crs or not ds.crs.is_projected or ds.crs.linear_units not in ['metre','meter']:raise ValueError('Use matching projected geographic grids in metres for this comparison.')
            t=ds.transform
            if not np.isfinite(list(t)).all() or abs(t.a*t.e-t.b*t.d)<1e-12 or t.b or t.d:raise ValueError('Spectral comparison requires finite, non-rotated, nonsingular grids.')
            arrays={}
            for name,i in mapping.items():
                a=ds.read(i,masked=True).astype('float64').filled(np.nan)
                if name!='scl':a=a*ds.scales[i-1]+ds.offsets[i-1]
                elif ds.scales[i-1]!=1 or ds.offsets[i-1]!=0:raise ValueError('SCL must contain unscaled categorical labels.')
                arrays[name]=a
            loaded.append({'arrays':arrays,'profile':ds.profile.copy(),'sensor':tags['sensor'],'date':date,'sha256':hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()})
    a,b=loaded
    if dates[0]>=dates[1]:raise ValueError('The before date must precede the after date.')
    if a['sensor']!=b['sensor']:raise ValueError('Use the same declared sensor/product convention at both dates.')
    for key in ['crs','width','height','transform']:
        if a['profile'][key]!=b['profile'][key]:raise ValueError('Both dates must share the exact CRS, dimensions and transform. Align outside SatQuery; headers alone do not certify physical registration.')
    return loaded

def analyse(records,tasks,threshold,water_threshold,out,progress=lambda s:None,include_built_up=False):
    start=time.perf_counter();data=validate(records);a,b=data;profile=a['profile'];h,w=profile['height'],profile['width'];results={};arrays={};images=[]
    for task in tasks:
        progress('Comparing '+('NDVI vegetation' if task=='vegetation' else 'NDWI water candidates'))
        positive,negative=('nir','red') if task=='vegetation' else ('green','nir');cut=threshold if task=='vegetation' else water_threshold
        if any(positive not in d['arrays'] or negative not in d['arrays'] for d in data):
            results[task]={'status':'unavailable','reason':'Both dates need labelled '+positive+' and '+negative+' bands.'};continue
        indices=[];valids=[]
        for d in data:
            x,y=d['arrays'][positive],d['arrays'][negative];v=np.isfinite(x)&np.isfinite(y)&(x>=0)&(y>=0)&((x+y)>1e-8)&np.isin(d['arrays']['scl'],[4,5,6,7]);value=np.full(x.shape,np.nan);np.divide(x-y,x+y,out=value,where=v);indices.append(value);valids.append(v)
        common=valids[0]&valids[1];n=int(common.sum())
        if not n:results[task]={'status':'unavailable','reason':'No common quality-valid pixels with usable bands at both dates.'};continue
        before=(indices[0]>=cut)&common;after=(indices[1]>=cut)&common;gain=after&~before;loss=before&~after;delta=np.where(common,indices[1]-indices[0],np.nan)
        for key,value in [('before',np.where(common,indices[0],np.nan)),('after',np.where(common,indices[1],np.nan)),('delta',delta),('valid',common)]:arrays[task+'_'+key]=value
        area=abs(profile['transform'].a*profile['transform'].e)
        results[task]={'status':'complete','formula':FORMULAS[task],'threshold':cut,'comparison':'>=','valid_pixels':n,'full_pixels':h*w,'before_pixels':int(before.sum()),'after_pixels':int(after.sum()),'gain_pixels':int(gain.sum()),'loss_pixels':int(loss.sum()),'net_pixels':int(after.sum()-before.sum()),'net_percentage_points':float(100*(after.sum()-before.sum())/n),'mean_index_change':float(delta[common].mean()),'net_grid_area_m2':float((after.sum()-before.sum())*area),'quality_rule':'SCL 4,5,6,7 retained at both dates; finite nonnegative calibrated bands and nonzero denominator','interpretation':'Threshold-based spectral candidates, not verified land-cover conversion.'}
        rgb=np.zeros((h,w,3),dtype='uint8');rgb[common]=[55,55,55];rgb[before&after]=[160,160,160];rgb[gain]=[40,210,170];rgb[loss]=[235,90,150];Image.fromarray(rgb).save(out/(task+'-change.png'))
        states=[]
        for selected in [before,after]:
            state=np.zeros((h,w,3),dtype='uint8');state[common]=[55,55,55];state[selected]=[40,210,170];states.append(state)
        panel=comparison_panel([*states,rgb],[[a['date'],str(int(before.sum()))+' selected pixels'],[b['date'],str(int(after.sum()))+' selected pixels'],['Change: '+('NDVI' if task=='vegetation' else 'NDWI'),'Green gain / pink loss','Grey retained / black invalid']])
        panel.save(out/(task+'-comparison.png'));images.append(np.asarray(panel))
        meta={k:profile[k] for k in ['crs','transform','width','height']};meta.update(driver='GTiff',count=3,dtype='float64',nodata=np.nan,compress='deflate')
        with rasterio.open(out/(task+'-indices.tif'),'w',**meta) as dst:
            for i,key in enumerate(['before','after','delta'],1):dst.write(arrays[task+'_'+key],i);dst.set_band_description(i,key)
            dst.update_tags(formula=FORMULAS[task],threshold=str(cut),common_valid_pixels=str(n))
    if not images:raise ValueError('No requested parameter could be calculated. '+ ' '.join(v['reason'] for v in results.values()))
    Image.fromarray(np.concatenate(images,axis=0)).save(out/'comparison.png');np.savez_compressed(out/'comparison-arrays.npz',**arrays)
    previews=[]
    for label,d in zip(['Before','After'],data):
        if all(k in d['arrays'] for k in ['red','green','blue']):
            # Identical fixed display stretch at both dates; never modifies analysis arrays.
            raw=np.stack([d['arrays'][k] for k in ['red','green','blue']],axis=-1)
            valid=np.isfinite(raw).all(axis=-1)
            rgb=(np.clip(np.nan_to_num(raw,nan=0)/0.3,0,1)*255).astype('uint8');rgb[~valid]=0
            filename=label.lower()+'.png';Image.fromarray(rgb).save(out/filename)
            previews.append({'file':filename,'label':label+' source - '+d['date']+' - RGB preview','display':'RGB surface reflectance, fixed 0-0.3 stretch; invalid pixels black; source TIFF unchanged'})
    if include_built_up:results['built_up']={'status':'unavailable','reason':'No validated built-up expansion measurement in this workflow. NDVI loss is not urban growth.'}
    return {'task':'spectral_pair','source_previews':previews,'answer':'Observed-date spectral comparison. Green marks newly threshold-selected pixels; pink marks lost selection. Each parameter uses its own common valid area across the two dates.','seconds':time.perf_counter()-start,'parameters':results,'dates':[x['date'] for x in data],'trace':[{'tool':VERSION,'device':'cpu','source_sha256':[x['sha256'] for x in data],'dates':[x['date'] for x in data],'thresholds':{'vegetation':threshold,'water':water_threshold}}],'confidence':{'kind':'Deterministic arithmetic, not classification accuracy'},'limitations':['NDWI candidates can include built-up surfaces; not confirmed water or flood extent.','NDVI change is not vegetation health or urban expansion.','Matching metadata does not prove physical co-registration.','Season, sun angle and source processing can change index values.','SCL exclusions are only as reliable as supplied quality labels; no new cloud model is run.','No forecasting or built-up measurement is performed.']}
