import sys,json,copy,hashlib,py_compile
from pathlib import Path
P=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');sys.path.insert(0,str(P))
import engine,controller
from inputs import inspect,validate
import numpy as np
from PIL import Image
for f in ['server.py','inputs.py','controller.py','single_bridge.py','flood.py','mci.py','registration.py']:py_compile.compile(str(P/f),doraise=True)
results=[]
def check(name,fn,reject=False):
 try:out=fn();ok=not reject;msg=str(out)
 except ValueError as e:ok=reject;msg=str(e)
 except Exception as e:ok=False;msg=repr(e)
 results.append({'name':name,'passed':ok,'output':msg});print(name,ok,msg[:250],flush=True)
a=inspect(P/'samples/levir-test_102_0512_0000/before.tif','optical');b=copy.deepcopy(a)
for r,date in [(a,'2020-01-01'),(b,'2021-01-01')]:r.update(crs='EPSG:32643',transform=[.5,0,300000,0,-.5,2000000],date=date,bands=['red','green','blue'],sensor='test optical')
check('single VQA route',lambda:controller.plan('Describe this image.',[{'modality':'optical','geo':None}]))
check('single NDVI route',lambda:controller.plan('Calculate NDVI coverage.',[{'modality':'optical','geo':{'ndvi_supported':True}}]))
check('RGB cannot measure NDVI',lambda:controller.plan('Calculate NDVI coverage.',[{'modality':'optical','geo':None}]),True)
check('one image cannot answer temporal',lambda:controller.plan('What changed?',[{'modality':'optical','geo':None}]),True)
check('two optical dates route',lambda:controller.plan('What changed?',[a,b]))
check('road caption route',lambda:controller.plan('What changed in the roads?',[a,b]))
check('identical optical geometry',lambda:validate([a,b],'temporal',enforce_content=True))
c=copy.deepcopy(b);c['data']=np.roll(c['data'],5,axis=2)
check('forged matching metadata shifted pixels rejected',lambda:validate([a,c],'temporal',enforce_content=True),True)
c2=copy.deepcopy(b);c2['data']=np.clip((c2['data'].astype(float)-127.5)*1.2+127.5+15,0,255).astype('uint8')
check('brightness-only remains registered',lambda:validate([a,c2],'temporal',enforce_content=True))
c3=copy.deepcopy(b);c3['transform'][2]+=1
check('shifted geographic grid rejected',lambda:validate([a,c3],'temporal'),True)
c4=copy.deepcopy(a);c5=copy.deepcopy(b);c4['transform'][1]=c5['transform'][1]=.1
check('shared shear rejected',lambda:validate([c4,c5],'temporal'),True)
c6=copy.deepcopy(b);c6['sensor']='different sensor'
check('cross-sensor temporal rejected',lambda:validate([a,c6],'temporal'),True)
catalog=json.loads((P/'samples/catalog.json').read_text())
for sample in [s for s in catalog if s['kind']=='water_map']:
 rr=[inspect(P/'samples'/sample['id']/f,m) for f,m in zip(sample['files'],['optical','sar'])]
 check('water contract '+sample['id'],lambda rr=rr:validate(rr,controller.plan('Map water using both sensors.',rr)['task']))
rr=[inspect(P/'samples/ben-validation-33-69'/f,m) for f,m in [('optical.tif','optical'),('sar.tif','sar')]]
check('scene fusion route preserved',lambda:controller.plan('Identify land cover using optical and SAR.',rr))
check('sensor pair temporal ambiguity rejected',lambda:controller.plan('What changed?',rr),True)
before=json.loads((P/'evidence/demo-before.json').read_text());changed=[n for n,h in before.items() if hashlib.sha256((P.parent/n).read_bytes()).hexdigest()!=h]
results.append({'name':'preserved demo files unchanged','passed':not changed,'changed':changed,'files':len(before)})
(P/'evidence/resumed/input-controller-tests.json').write_text(json.dumps(results,indent=2));print('PASS',sum(r['passed'] for r in results),'/',len(results),flush=True)
if not all(r['passed'] for r in results):raise SystemExit(1)
