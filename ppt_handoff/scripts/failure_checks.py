
import requests,io,json,time,sys
import numpy as np,rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from pathlib import Path
h=Path(__file__).resolve().parents[1];b='http://127.0.0.1:8765';rows=[]
def note(case,r):rows.append({'case':case,'http':r.status_code,'response':r.text[:600]})
def tif(names,zeros=False,nodata=False,crs='EPSG:32643'):
 a=np.ones((len(names),4,4),dtype='float32')*.1
 if 'nir' in names:a[names.index('nir')]=.4
 if zeros:a[:]=0
 if nodata:a[:,:,:]=np.nan;a[:,0,0]=.1
 with MemoryFile() as mem:
  with mem.open(driver='GTiff',width=4,height=4,count=len(names),dtype='float32',crs=crs,transform=from_origin(788360,3359030,10,10),nodata=np.nan) as s:
   s.write(a);s.descriptions=tuple(names);s.update_tags(reflectance_units='surface_reflectance')
  return mem.read()
def upload(raw,name='test.tif'):return requests.post(b+'/api/images',files={'file':(name,raw)},timeout=30)
note('malformed image',upload(b'not an image','bad.png'))
note('malformed TIFF header',upload(b'II*\x00garbage'))
note('unsupported/unlabelled TIFF',upload(tif(['a','b','c','d'])))
note('oversized upload',upload(b'x'*(20*1024*1024+1),'large.png'))
for case,raw in [('missing NIR',tif(['red','green','blue'])),('zero denominator',tif(['red','green','blue','nir'],zeros=True)),('nodata-heavy',tif(['red','green','blue','nir'],nodata=True)),('missing CRS',tif(['red','green','blue','nir'],crs=None))]:
 u=upload(raw);note(case+' upload',u)
 if u.ok:
  r=requests.post(b+'/api/ndvi',data={'image_id':u.json()['id'],'threshold':.5})
  note(case+' NDVI submit',r)
  if r.ok:
   for _ in range(100):
    j=requests.get(b+'/api/runs/'+r.json()['id'])
    if j.json()['state'] in ['complete','error']:break
    time.sleep(.02)
   note(case+' NDVI result',j)
u=upload(tif(['red','green','blue','nir']))
for q in ['', 'x'*501,'Compare this to last year','Analyze SAR backscatter','What are the latitude coordinates?']:
 note('question: '+q[:40],requests.post(b+'/api/analyze',data={'image_id':u.json()['id'],'question':q}))
(h/'metrics/failure_checks.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
