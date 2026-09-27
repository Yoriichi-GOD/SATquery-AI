import sys,json,time,subprocess,requests,zipfile,io
from pathlib import Path
R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI');O=R/'paired_lab/evidence/compliance-20260926';O.mkdir(exist_ok=True)
B='http://127.0.0.1:18767'
log=(O/'sar-live.log').open('w')
p=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--app-dir',str(R/'paired_lab'),'--host','127.0.0.1','--port','18767'],stdout=log,stderr=log)
try:
 for _ in range(60):
  try:
   if requests.get(B+'/api/status',timeout=1).ok:break
  except requests.RequestException:pass
  time.sleep(.5)
 else:raise RuntimeError('Validation service did not start')
 import rasterio
 from rasterio.windows import Window
 source=R/'paired_lab/evidence/external-water-20260920/S1Hand-annotated.tif'
 from rasterio.warp import calculate_default_transform,reproject,Resampling
 original_source=source;projected=O/'sar-projected.tif'
 with rasterio.open(source) as ds:
  transform,w,h=calculate_default_transform(ds.crs,'EPSG:32720',ds.width,ds.height,*ds.bounds,resolution=10)
  profile=ds.profile.copy();profile.update(crs='EPSG:32720',transform=transform,width=w,height=h,dtype='float32',nodata=float('nan'))
  with rasterio.open(projected,'w',**profile) as dst:
   for i in ds.indexes:
    reproject(source=rasterio.band(ds,i),destination=rasterio.band(dst,i),src_transform=ds.transform,src_crs=ds.crs,dst_transform=transform,dst_crs='EPSG:32720',src_nodata=ds.nodata,dst_nodata=float('nan'),resampling=Resampling.nearest)
    dst.set_band_description(i,ds.descriptions[i-1])
   dst.update_tags(**ds.tags())
 source=projected
 sample=O/'sar-native-crop.tif'
 with rasterio.open(source) as ds:
  import numpy as np
  window=None
  for y in range(0,ds.height-119,16):
   for x in range(0,ds.width-119,16):
    candidate=Window(x,y,120,120);v=ds.read(window=candidate,masked=True)
    if not np.ma.getmaskarray(v).any() and np.isfinite(v.data).all():window=candidate;break
   if window is not None:break
  if window is None:raise ValueError('No fully valid native crop available')
  a=ds.read(window=window);profile=ds.profile.copy();profile.update(width=120,height=120,transform=ds.window_transform(window))
  with rasterio.open(sample,'w',**profile) as dst:
   dst.write(a);dst.update_tags(**ds.tags())
   for i,d in enumerate(ds.descriptions,1):dst.set_band_description(i,d)
 (O/'sar-preparation.json').write_text(json.dumps({'source':str(original_source),'projected_source':str(source),'target_crs':'EPSG:32720','resolution_m':10,'window':list(window.flatten()),'processing':'Explicit nearest-neighbour reprojection to 10 m EPSG:32720, then first completely valid crop in row-major 16-pixel steps. dB samples retained; grid changed explicitly. No EOS-04 relabelling.','scope':'Functional integration on prior Bolivia data; classifier quality/domain transfer not measured.'},indent=2))
 res=requests.post(B+'/api/single-images',files={'file':('sar.tif',sample.read_bytes())},data={'modality':'sar'},timeout=30)
 print('UPLOAD',res.status_code,res.text[:400],flush=True);res.raise_for_status();record=res.json()
 job=requests.post(B+'/api/analyze',json={'images':[record['id']],'query':'Describe this SAR image'},timeout=30);job.raise_for_status();jid=job.json()['id']
 for _ in range(180):
  result=requests.get(B+'/api/jobs/'+jid,timeout=10).json()
  if result['state'] in ['complete','failed']:break
  time.sleep(.5)
 (O/'sar-live.json').write_text(json.dumps(result,indent=2));print(result['state'],result.get('error',result.get('result',{}).get('answer')),flush=True)
 assert result['state']=='complete'
 raw=requests.get(B+'/api/runs/'+jid+'/evidence.zip',timeout=30);raw.raise_for_status()
 with zipfile.ZipFile(io.BytesIO(raw.content)) as z:
  assert z.testzip() is None
  assert z.read('input-1.original')==sample.read_bytes()
 (O/'sar-live-evidence.zip').write_bytes(raw.content)
 print('Verified original bytes and archive integrity',flush=True)
finally:
 p.terminate();p.wait(timeout=15);log.close()
