import requests,time,json,zipfile,io,pathlib,numpy as np,rasterio
root=pathlib.Path('/mnt/c/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/day1/varanasi-pair');base='http://127.0.0.1:8767';ids=[];raws=[]
for year in [2024,2025]:
 p=root/'scenes'/f'varanasi-{year}'/f'varanasi-{year}.tif';raws.append(p.read_bytes());r=requests.post(base+'/api/images',files={'file':(p.name,raws[-1])},data={'modality':'optical'});r.raise_for_status();ids.append(r.json()['id'])
reports=[]
for q in ['Analyze these images','Compare vegetation','Compare water']:
 r=requests.post(base+'/api/analyze',json={'images':ids,'query':q,'threshold':.5,'water_threshold':0});r.raise_for_status();job=r.json();assert job['task']=='spectral_pair'
 for _ in range(200):
  d=requests.get(base+'/api/jobs/'+job['id']).json()
  if d['state'] in ['complete','failed']:break
  time.sleep(.2)
 assert d['state']=='complete',d
 raw=requests.get(base+'/api/runs/'+job['id']+'/evidence.zip').content;z=zipfile.ZipFile(io.BytesIO(raw));assert z.testzip() is None
 for i,b in enumerate(raws,1):assert z.read(f'input-{i}.tif')==b
 arrays=np.load(io.BytesIO(z.read('comparison-arrays.npz')))
 for key,v in d['result']['parameters'].items():
  if v['status']!='complete':continue
  pairs=[];valids=[]
  for b in raws:
   with rasterio.MemoryFile(b) as mem,mem.open() as ds:
    m={x:i for i,x in enumerate(ds.descriptions,1)};a=ds.read(m['nir' if key=='vegetation' else 'green']).astype('float64');c=ds.read(m['red' if key=='vegetation' else 'nir']).astype('float64');scl=ds.read(m['scl']);valid=np.isfinite(a)&np.isfinite(c)&(a>=0)&(c>=0)&((a+c)>1e-8)&np.isin(scl,[4,5,6,7]);index=np.full(a.shape,np.nan);index[valid]=(a[valid]-c[valid])/(a[valid]+c[valid]);pairs.append(index);valids.append(valid)
  common=valids[0]&valids[1];cut=.5 if key=='vegetation' else 0;before=(pairs[0]>=cut)&common;after=(pairs[1]>=cut)&common
  assert int(common.sum())==v['valid_pixels'];assert int((after&~before).sum())==v['gain_pixels'];assert int((before&~after).sum())==v['loss_pixels'];np.testing.assert_allclose(arrays[key+'_delta'],np.where(common,pairs[1]-pairs[0],np.nan),equal_nan=True)
 if q=='Compare vegetation':assert set(d['result']['parameters'])=={'vegetation'}
 if q=='Compare water':assert set(d['result']['parameters'])=={'water'}
 reports.append(d);(root/(job['id']+'.zip')).write_bytes(raw);print(q,json.dumps(d['result']['parameters']),flush=True)
for order,q in [(ids[::-1],'Analyze these images'),(ids,'Compare NDVI above 0.8'),(ids,'Predict water tomorrow')]:
 r=requests.post(base+'/api/analyze',json={'images':order,'query':q});assert r.status_code==400,(r.status_code,r.text)
(root/'live-verification.json').write_text(json.dumps({'runs':reports,'refusals':3,'scope':'Two actual observed crops; arithmetic and integration verification, not field validation or city-wide change estimates.'},indent=2))
