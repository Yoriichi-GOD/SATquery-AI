import sys,json,tempfile,copy,time,hashlib,io,zipfile
from pathlib import Path
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');sys.path.insert(0,str(ROOT))
import engine
from inputs import inspect,route,validate
import numpy as np,rasterio,requests
from rasterio.transform import from_origin
results=[]
def check(name,fn,reject=False):
    try:fn();passed=not reject;message='accepted'
    except ValueError as e:passed=reject;message=str(e)
    except Exception as e:passed=False;message=repr(e)
    results.append({'test':name,'passed':passed,'message':message});print(name,passed,message,flush=True)
def record(mode='optical'):
    return {'modality':mode,'shape':[256,256],'count':3,'dtype':'uint8','crs':'EPSG:32643','transform':[.5,0,300000,0,-.5,2000000],'date':'2020-01-01','bands':['red','green','blue'],'data':np.ones((3,256,256),dtype='uint8'),'sensor':'','units':''}
a=record();b=record();b['date']='2021-01-01'
check('temporal matching geospatial pair',lambda:validate([a,b],'temporal'))
for name,mut in [('different CRS',{'crs':'EPSG:32644'}),('shifted grid',{'transform':[.5,0,300001,0,-.5,2000000]}),('missing CRS',{'crs':None}),('missing date',{'date':''}),('reversed dates',{'date':'2019-01-01'}),('equal dates',{'date':'2020-01-01'}),('unlabelled RGB',{'bands':[None,None,None]}),('different dimensions',{'shape':[255,256]}),('16-bit RGB',{'dtype':'uint16'})]:
    bb={**b,**mut};check(name,lambda bb=bb:validate([a,bb],'temporal'),True)
o={**a,'shape':[120,120],'bands':engine.S2,'count':10,'dtype':'float32','transform':[10,0,300000,0,-10,2000000],'sensor':'Sentinel-2','units':'reflectance_x10000'}
s={**o,'modality':'sar','bands':engine.S1,'count':2,'sensor':'Sentinel-1','units':'dB','date':'2020-01-03'}
check('supported optical SAR pair',lambda:validate([o,s],'optical_sar'))
for name,mut in [('SAR wrong units',{'units':'linear'}),('RISAT unsupported',{'sensor':'RISAT'}),('missing polarization',{'bands':['VV']}),('far-apart acquisitions',{'date':'2020-05-01'})]:
    ss={**s,**mut};check(name,lambda ss=ss:validate([o,ss],'optical_sar'),True)
check('degree grid is not 10 metres',lambda:validate([{**o,'crs':'EPSG:4326'},{**s,'crs':'EPSG:4326'}],'optical_sar'),True)
for q,rr,expected in [('What changed between these dates?',[a,b],'temporal'),('Has built-up area increased?',[a,b],'temporal'),('Use optical and SAR together for land cover',[o,s],'optical_sar'),('Describe the land cover',[o,s],'optical_sar')]:
    check('route '+q,lambda q=q,rr=rr,expected=expected: (_ for _ in ()).throw(ValueError('wrong task')) if route(q,rr)!=expected else None)
for q,rr in [('What changed?',[o,s]),('What changed?',[a]),('Use SAR together',[a,b]),('How many buildings changed?',[a,b]),('Where are water-covered regions?',[o,s]),('What changed in the forest?',[a,b]),('What is the car colour?',[o,s]),('',[a,b])]:check('reject '+q,lambda q=q,rr=rr:route(q,rr),True)
with tempfile.TemporaryDirectory() as td:
    for name,data,nodata in [('NaN',np.full((1,8,8),np.nan,dtype='float32'),None),('nodata',np.full((1,8,8),-9999,dtype='float32'),-9999)]:
        p=Path(td)/(name+'.tif')
        with rasterio.open(p,'w',driver='GTiff',width=8,height=8,count=1,dtype='float32',nodata=nodata,transform=from_origin(0,100,10,10),crs='EPSG:32643') as dst:dst.write(data)
        check(name+' pixels rejected',lambda p=p:inspect(p,'sar'),True)
before=json.loads((ROOT/'evidence/demo-before.json').read_text())
changed=[p for p,h in before.items() if not (ROOT.parent/p).exists() or hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest()!=h]
results.append({'test':'existing demo source unchanged','passed':not changed,'changed':changed,'files':len(before)})
for port in [8765,8767]:
    r=requests.get(f'http://127.0.0.1:{port}/api/status',timeout=10);results.append({'test':f'HTTP status {port}','passed':r.status_code==200,'response':r.json()})
(ROOT/'evidence/validation-tests.json').write_text(json.dumps(results,indent=2))
print('PASSED',sum(x['passed'] for x in results),'/',len(results),flush=True)
if not all(x['passed'] for x in results):raise SystemExit(1)
