"""New synthetic acceptance challenges; not a natural-query accuracy estimate."""
from pathlib import Path
import sys,json,random,math
from fractions import Fraction
import numpy as np
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI')
sys.path[:0]=[str(ROOT),str(ROOT/'paired_lab')]
import controller,geo
OUT=Path(__file__).resolve().parent/'acceptance-20260926'
o={'modality':'optical','width':256,'height':256,'count':3,'geo':None}
sar={'modality':'sar','width':512,'height':512,'count':2}
water=[dict(o,count=13),sar];land=[dict(o,count=10),sar]
cases=[
 ('Describe the visible scene in this image.',[o],'vqa'),
 ('Is there a road in this scene?',[o],'vqa'),
 ('Compute NDVI for this raster.',[dict(o,geo={'ndvi_supported':True})],'ndvi'),
 ('Compute NDVI for this raster.',[o],'refuse'),
 ('Compare buildings across these dates.',[o,o],'temporal'),
 ('Show road changes between these dates.',[o,o],'temporal'),
 ('Map water pixels in the supplied pair.',water,'water_map'),
 ('Identify land-cover classes for this pair.',land,'optical_sar'),
 ('Draw bounding boxes around aircraft.',[o],'grounding'),
 ('Outline ships.',[o],'grounding'),
 ('Predict inundation tomorrow.',water,'refuse'),
 ('Estimate water depth in this pair.',water,'refuse'),
 ('Map roads and water.',water,'refuse'),
 ('Compare the colours of cars between dates.',[o,o],'refuse'),
 ('Report hectares of new buildings.',[o,o],'refuse'),
 ('Locate buildings in this optical SAR pair.',land,'refuse'),
 ('Describe the visible scene.',[sar],'refuse'),
 ('Describe these images.',[o,o,o],'refuse'),
 ('Outline the car nearest the building.',[o],'refuse'),
 ('Show NDVI changes between dates.',[o,o],'refuse')]
def freeze():
 p=OUT/'contract-freeze.json'
 if p.exists():raise RuntimeError('Already frozen')
 p.write_text(json.dumps({'criteria':'All 20 expected dispatch/refusal outcomes and 100 exact-rational NDVI comparisons within 1e-12; all failures retained. Synthetic engineering gate, not scientific accuracy.','seed':20260926,'cases':cases},indent=2))
def run():
 f=json.loads((OUT/'contract-freeze.json').read_text());rows=[]
 for q,records,expected in f['cases']:
  try:actual=controller.plan(q,records)['task'];reason=None
  except ValueError as e:actual='refuse';reason=str(e)
  rows.append({'query':q,'expected':expected,'actual':actual,'passed':actual==expected,'reason':reason})
 rng=random.Random(f['seed']);pairs=[(rng.randint(0,10000),rng.randint(0,10000)) for _ in range(100)]
 r=np.array([p[0] for p in pairs],dtype=float);n=np.array([p[1] for p in pairs],dtype=float)
 got,valid=geo.calculate(r,n);reference=np.array([float(Fraction(b-a,b+a)) if b+a else np.nan for a,b in pairs]);error=float(np.nanmax(np.abs(got-reference)))
 result={'routing':rows,'routing_passed':sum(r['passed'] for r in rows),'routing_total':len(rows),'ndvi_cases':100,'ndvi_max_absolute_error':error,'passed':all(r['passed'] for r in rows) and error<=1e-12 and valid.all()}
 filename='contract-regression.json' if sys.argv[1]=='regression' else 'contract-results.json'
 if (OUT/filename).exists():raise RuntimeError('Do not overwrite existing evidence')
 (OUT/filename).write_text(json.dumps(result,indent=2,default=lambda v:bool(v)));print(json.dumps(result,default=lambda v:bool(v)),flush=True)
if __name__=='__main__':{'freeze':freeze,'run':run,'regression':run}[sys.argv[1]]()
