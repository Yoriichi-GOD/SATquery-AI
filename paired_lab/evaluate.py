import sys,json,time,hashlib,subprocess
from pathlib import Path
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');sys.path.insert(0,str(ROOT))
import engine
import numpy as np
from PIL import Image
import pandas as pd,lmdb
from safetensors.numpy import load
E=ROOT/'evidence'/('repeat-trial-'+time.strftime('%Y%m%d-%H%M%S'));E.mkdir(parents=True,exist_ok=True)
samples=ROOT/'samples';samples.mkdir(exist_ok=True)
summary={'temporal':[],'optical_sar':[],'notes':['All results are small public development trials; no full benchmark or ISRO accuracy claim.','ConfigILM fixtures are real BigEarthNet subsets, concentrated in one Austrian scene.','ChangeFormer upstream training selects checkpoint using test split: LEVIR sample metrics are not clean held-out proof.']}
catalog=[]
def metric(p,g):
    tp=int((p&g).sum());fp=int((p&~g).sum());fn=int((~p&g).sum());tn=int((~p&~g).sum())
    return {'tp':tp,'fp':fp,'fn':fn,'tn':tn,'iou':tp/(tp+fp+fn) if tp+fp+fn else 1.,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 1.}
src=engine.DATA/'ChangeFormer/samples_LEVIR'
for a in sorted((src/'A').glob('test*.png')):
    b=src/'B'/a.name;g=src/'label'/a.name
    if not b.exists() or not g.exists():continue
    aa=np.asarray(Image.open(a).convert('RGB'));bb=np.asarray(Image.open(b).convert('RGB'))
    if aa.shape!=(256,256,3):continue
    name='levir-'+a.stem;out=E/name
    result=engine.temporal(aa,bb,out)
    gt=np.asarray(Image.open(g).convert('L'))>0;pred=np.load(out/'scores.npz')['mask']
    Image.fromarray(gt.astype('uint8')*255).save(out/'reference.png')
    m=metric(pred,gt);summary['temporal'].append({'sample':name,'kind':'public-test-named-demo','metrics':m,'seconds':result['seconds']})
    pair=samples/name;pair.mkdir(exist_ok=True);Image.fromarray(aa).save(pair/'before.tif');Image.fromarray(bb).save(pair/'after.tif')
    info={'id':name,'kind':'temporal','name':a.stem,'source':'ChangeFormer official LEVIR samples','source_revision':engine.MODELS['temporal']['revision'],'benchmark':'LEVIR-CD development','registration':'publisher paired crop; no geographic metadata','dates':'ordered A/B; exact dates unavailable','files':['before.tif','after.tif'],'shape':[256,256]}
    (pair/'manifest.json').write_text(json.dumps(info,indent=2));catalog.append(info)
    print(name,m,round(result['seconds'],2),flush=True)
    if len(summary['temporal'])==1:
        control=E/(name+'-identical');r=engine.temporal(aa,aa,control);p=np.load(control/'scores.npz')['mask']
        summary['temporal'].append({'sample':name+'-identical','kind':'same-image-control','metrics':metric(p,np.zeros_like(p)),'seconds':r['seconds']})
        print('same-image control',int(p.sum()),flush=True)
base=engine.DATA/'ConfigILM/configilm/extra/mock_data/BENv2'
df=pd.read_parquet(base/'metadata.parquet');env=lmdb.open(str(base/'BigEarthNet-V2-LMDB'),readonly=True,lock=False)
for _,row in df.iterrows():
    if row['split']=='train':continue
    with env.begin() as txn:bands={**load(txn.get(row['s1_name'].encode())),**load(txn.get(row['patch_id'].encode()))}
    bands={k:bands[k] for k in engine.S1+engine.S2}
    name='ben-'+row['split']+'-'+row['patch_id'].split('_')[-2]+'-'+row['patch_id'].split('_')[-1]
    result=engine.fusion(bands,E/name)
    gt=np.array([c in row['labels'] for c in engine.CLASSES]);metrics={k:metric(np.array([s[c]>=.5 for c in engine.CLASSES]),gt) for k,s in result['scores'].items()}
    summary['optical_sar'].append({'sample':name,'split':row['split'],'reference_labels':list(row['labels']),'metrics':metrics,'scores':result['scores'],'seconds':result['seconds']})
    pair=samples/name;pair.mkdir(exist_ok=True)
    # TIFF carries bands; manifest carries authoritative dataset pairing. No fabricated CRS.
    import rasterio
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for filename,order in [('sar.tif',engine.S1),('optical.tif',engine.S2)]:
            data=np.stack([engine.F.interpolate(engine.torch.from_numpy(bands[k].astype('float32'))[None,None],size=(120,120),mode='nearest')[0,0].numpy() for k in order])
            with rasterio.open(pair/filename,'w',driver='GTiff',width=120,height=120,count=len(order),dtype='float32') as dst:
                dst.write(data)
                for i,k in enumerate(order,1):dst.set_band_description(i,k)
                dst.update_tags(sensor='Sentinel-1' if filename=='sar.tif' else 'Sentinel-2',units='dB' if filename=='sar.tif' else 'reflectance_x10000',source_patch=row['s1_name'] if filename=='sar.tif' else row['patch_id'])
    info={'id':name,'kind':'optical_sar','name':'Austria '+row['split']+' '+name.split('-',2)[-1],'source':'ConfigILM official BigEarthNet v2 real-data fixture','source_revision':subprocess.check_output(['git','-C',str(engine.DATA/'ConfigILM'),'rev-parse','HEAD'],text=True).strip(),'benchmark':'BigEarthNet v2 development','split':row['split'],'optical_patch':row['patch_id'],'sar_patch':row['s1_name'],'registration':'publisher paired sample; geographic transform unavailable in LMDB fixture','files':['optical.tif','sar.tif'],'shape':[120,120]}
    (pair/'manifest.json').write_text(json.dumps(info,indent=2));catalog.append(info)
    print(name,metrics,flush=True)
    (E/'summary.json').write_text(json.dumps(summary,indent=2))
env.close()
(samples/'catalog.json').write_text(json.dumps(catalog,indent=2))
for part in ['temporal','optical_sar']:
    pass
(E/'summary.json').write_text(json.dumps(summary,indent=2))
print('FINISHED',len(summary['temporal']),len(summary['optical_sar']),flush=True)
