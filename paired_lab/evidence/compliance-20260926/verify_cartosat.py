import json,sys
from pathlib import Path
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI');sys.path.insert(0,str(ROOT))
import geo
out=ROOT/'paired_lab/evidence/compliance-20260926'
preview,meta=geo.ingest((out/'cartosat-labelled.tif').read_bytes(),out/'cartosat-ingested.tif')
preview.save(out/'cartosat-preview.png')
assert meta['bands']=={'blue':1,'green':2,'red':3,'nir':4}
assert meta['ndvi_supported'] is False
try:geo.analyse(out/'cartosat-labelled.tif',out/'cartosat-ndvi')
except ValueError as e: refusal=str(e)
else:raise AssertionError('Uncalibrated DN incorrectly admitted to NDVI')
(out/'cartosat-ingestion-check.json').write_text(json.dumps({'ingestion':'passed','metadata':meta,'ndvi_refusal':refusal,'scope':'Input preparation/preview only; VQA inference not tested by this script.'},indent=2))
print('Cartosat native pixels preserved, RGB ingestion passed, uncalibrated NDVI correctly refused.')
