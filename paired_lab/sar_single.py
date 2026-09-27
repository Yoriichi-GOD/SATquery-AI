"""Bounded Sentinel-1 scene description through the existing SAR classifier."""
import re,json,time
from pathlib import Path
import numpy as np
from rasterio.crs import CRS
from PIL import Image

def validate(r):
    if r.get('modality')!='sar' or r.get('sensor') not in ['Sentinel-1','Sentinel-1 GRD'] or r.get('units')!='dB':
        raise ValueError('Single SAR classification requires Sentinel-1 VV/VH in dB; EOS-04/RISAT transfer is not validated.')
    if r.get('shape')!=[120,120] or list(r.get('bands',[]))!=['VV','VH']:
        raise ValueError('Use a 120 by 120 crop with ordered VV/VH bands at 10 m.')
    if not r.get('crs'):raise ValueError('A projected metre CRS is required.')
    c=CRS.from_user_input(r['crs']);t=np.asarray(r.get('transform',[]),dtype=float)
    if not c.is_projected or c.linear_units not in ['metre','meter'] or t.shape!=(6,) or not np.isfinite(t).all() or abs(t[0]-10)>1e-7 or abs(t[4]+10)>1e-7 or abs(t[1])+abs(t[3])>1e-10:
        raise ValueError('Single SAR classification requires a north-up 10 m projected grid.')
    if 'data' in r and (np.asarray(r['data']).shape!=(2,120,120) or not np.isfinite(r['data']).all()):raise ValueError('Supply two completely finite calibrated SAR bands.')

def eligible(query):
    q=' '.join(query.lower().strip(' .?!').split())
    return bool(re.fullmatch(r'(?:describe (?:this|the) (?:sar |radar )?(?:image|scene)|(?:identify|classify) (?:the )?land[- ]cover(?: classes)?(?: in (?:this|the) (?:sar |radar )?(?:image|scene))?)',q))

def preview(r,target):
    validate(r);vv,vh=r['data']
    rgb=np.stack([np.clip((vv+25)/30,0,1),np.clip((vh+32)/30,0,1),np.clip((vv-vh)/15,0,1)],axis=-1)
    Image.fromarray((rgb*255).astype('uint8')).save(target)

def run(r,out,progress=lambda _:None):
    validate(r)
    import engine,torch
    start=time.perf_counter();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    bands={name:r['data'][i] for i,name in enumerate(['VV','VH'])}
    progress('Running Sentinel-1 scene classifier on CPU')
    with torch.inference_mode():scores=engine.load_fusion('s1')(engine.normalize(bands,engine.S1)).sigmoid()[0].numpy()
    values={c:float(v) for c,v in zip(engine.CLASSES,scores)};selected=[c for c,v in values.items() if v>=.5]
    preview(r,out/'sar.png');np.savez_compressed(out/'scores.npz',scores=scores,classes=np.array(engine.CLASSES))
    result={'task':'sar_scene','answer':'The SAR-only model suggests '+(', '.join(selected) if selected else 'no class above the 0.5 threshold')+'. Scene-level interpretation; no object locations or measured area. A low score does not establish absence.','scores':values,'classes':selected,'seconds':time.perf_counter()-start,'confidence':{'kind':'uncalibrated sigmoid; not accuracy','threshold':.5},'trace':[{'tool':engine.MODELS['s1']['repo'],'revision':engine.MODELS['s1']['revision'],'bands':['VV','VH'],'units':'dB','normalization':'reBEN 120_nearest mean/std','device':'cpu','preview':'fixed VV/VH/difference display stretch; not true colour'}],'limitations':['Sentinel-1 only; no EOS-04/RISAT transfer claim.','Scene-level land-cover description, not unrestricted SAR VQA or grounding.','Class scores are uncalibrated; expert review remains necessary.']}
    return result
