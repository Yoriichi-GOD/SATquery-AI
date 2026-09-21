import json,sys
from pathlib import Path
O=Path(__file__).resolve().parent;R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI');sys.path.insert(0,str(R/'paired_lab'));import controller
opt={'modality':'optical','count':3,'width':256,'height':256};sar={'modality':'sar','count':2,'width':512,'height':512}
contexts={'single':[opt],'ndvi':[{**opt,'geo':{'ndvi_supported':True}}],'temporal':[opt,opt],'water':[{**opt,'count':13},sar],'land':[{**opt,'count':10},sar],'spectral':[{**opt,'reflectance_units':'surface_reflectance'}]*2}
spec=[
 ('single','vqa',['Describe this image.','Describe the entire scene.','What can you see in this image?','Is there water in this image?','Does this image contain buildings?','Is this image rural or urban?','How many baseball fields are there?']),
 ('single','grounding',['Outline buildings','Highlight ships','Locate aircraft','Draw bounding boxes around cars']),
 ('ndvi','ndvi',['Calculate NDVI','Compute NDVI','What percentage of the image is vegetation?']),
 ('temporal','temporal',['What changed between these dates?','Describe road changes','Show building changes','Compare the roads between these images','Identify construction and demolition']),
 ('water','water_map',['Map water','Show inundation','Identify water pixels','Map water using optical and SAR together']),
 ('land','optical_sar',['Identify land-cover classes','Classify land cover','Use optical and SAR to identify land-cover classes']),
 ('spectral','spectral_pair',['Analyze these images','Compare vegetation','Compare water','Compare NDVI and NDWI','Please analyze these images in detail']),
 ('single','refuse',['What changed between these dates?','Calculate NDVI','Predict water tomorrow','How many cars are there?','Outline red buildings','Outline buildings and ships','Estimate water depth','Diagnose crop disease']),
 ('temporal','refuse',['Compare water','How many buildings were constructed?','Measure road length change','Which red car was added?','Describe vegetation health','Compare these images and count all cars']),
 ('water','refuse',['Map roads and water','Calculate water depth','What changed since last year?','Predict inundation tomorrow','Measure water volume','Map water and vegetation','Identify water and soil moisture']),
 ('land','refuse',['Map buildings','Calculate water coverage','Segment water','Identify building locations']),
 ('spectral','refuse',['Predict water next week','Compare vegetation health','Compare water above 0.5','Compare vegetation and count buildings','Compare water and temperature','Analyze these images and estimate population']),
]
cases=[{'context':c,'expected':expected,'query':q} for c,expected,qs in spec for q in qs]
# Expectations are written before invoking the router. Metadata fixtures test dispatch,
# not real raster compatibility or model execution.
(O/'routing-manifest.json').write_text(json.dumps(cases,indent=2))
rows=[]
for c in cases:
 try:p=controller.plan(c['query'],contexts[c['context']]);actual=p['task'];reason=p['reason']
 except ValueError as e:actual='refuse';reason=str(e)
 rows.append({**c,'actual':actual,'correct':actual==c['expected'],'reason':reason})
(O/'routing-results.json').write_text(json.dumps({'n':len(rows),'correct':sum(r['correct'] for r in rows),'unsafe_dispatches':sum(r['expected']=='refuse' and r['actual']!='refuse' for r in rows),'false_refusals':sum(r['expected']!='refuse' and r['actual']=='refuse' for r in rows),'scope':'Predeclared hand-written challenge set; not natural-query population accuracy. Eligibility metadata fixtures only.','rows':rows},indent=2))
print(json.dumps([r for r in rows if not r['correct']],indent=2))
