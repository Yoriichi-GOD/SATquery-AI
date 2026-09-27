import json,sys,zipfile,hashlib
from pathlib import Path
import rasterio
from rasterio.windows import Window
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI')
sys.path[:0]=[str(ROOT),str(ROOT/'paired_lab')]
import geo,inputs
OUT=Path(__file__).resolve().parent
rows=[]
def trial(name,fn):
 try:
  fn();rows.append({'check':name,'outcome':'accepted'})
 except ValueError as e:rows.append({'check':name,'outcome':'refused','reason':str(e)})
for archive in sys.argv[1:]:
 p=OUT/archive
 with zipfile.ZipFile(p) as z:
  bad=z.testzip()
  if bad:raise RuntimeError('ZIP CRC failed: '+bad)
  rasters=[n for n in z.namelist() if n.lower().endswith(('.tif','.tiff'))]
  image_rasters=[n for n in rasters if not any(k in n.lower() for k in ['_lia','incidence','angle'])]
  first=image_rasters[0]
  with rasterio.open('/vsizip/'+str(p)+'/'+first) as ds:
   window=Window(max(0,ds.width//2-256),max(0,ds.height//2-256),min(512,ds.width),min(512,ds.height))
   data=ds.read(window=window);profile=ds.profile.copy();profile.update(width=data.shape[2],height=data.shape[1],transform=ds.window_transform(window))
   crop=OUT/(p.stem+'-native-crop.tif')
   with rasterio.open(crop,'w',**profile) as dst:
    dst.write(data);dst.update_tags(**ds.tags())
    for i in ds.indexes:
     if ds.descriptions[i-1]:dst.set_band_description(i,ds.descriptions[i-1])
     dst.update_tags(i,**ds.tags(i))
   rows.append({'check':archive+' archive integrity','outcome':'passed','all_members_crc_valid':True,'crop_member':first,'crop_window':list(window.flatten()),'crop_sha256':hashlib.sha256(crop.read_bytes()).hexdigest(),'preparation':'Native central crop only; no resampling, calibration, band naming or sensor relabelling.'})
  raw=crop.read_bytes()
  trial(archive+' single image native crop ingestion',lambda:geo.ingest(raw,OUT/'accepted.tif'))
  trial(archive+' native crop NDVI',lambda:geo.analyse(crop,OUT/(p.stem+'-ndvi')))
  modality='optical' if archive.startswith('cartosat') else 'sar'
  trial(archive+' native crop paired metadata inspection',lambda:inputs.inspect(crop,modality))
(OUT/'contract-results.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
