
# Independent TIFF decoder + scalar Python arithmetic; does not import geo or rasterio.
import math,json,hashlib
from pathlib import Path
import tifffile
import numpy as np
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1]
source=Path('/root/satquery/scenes/dehradun-sentinel2-20211125.tif')
run=json.loads((root/'results/ndvi-integration.json').read_text())
with tifffile.TiffFile(source) as t:
 data=t.asarray()
 dx,dy,_=t.pages[0].tags['ModelPixelScaleTag'].value
 keys=t.pages[0].tags['GeoKeyDirectoryTag'].value
 mapping={keys[i]:keys[i+3] for i in range(4,len(keys),4)}
 assert mapping[3072]==32643 and mapping[3076]==9001
mask=np.zeros(data.shape[:2],dtype=bool)
values=np.full(data.shape[:2],np.nan,dtype='float64')
valid=0
for y in range(data.shape[0]):
 for x in range(data.shape[1]):
  red,green,blue,nir,scl=map(float,data[y,x])
  if all(math.isfinite(v) for v in [red,nir]) and red>=0 and nir>=0 and nir+red>1e-8 and scl in (4,5,6,7):
   valid+=1
   values[y,x]=(nir-red)/(nir+red)
   mask[y,x]=values[y,x]>=.5
selected=int(mask.sum())
art=Path('/root/satquery/app-data/runs')/run['id']
app_mask=np.asarray(Image.open(art/'overlay.png'))[:,:,3]>0
app_ndvi=tifffile.imread(art/'ndvi.tif')
result={'method':'tifffile decoder; scalar float64 Python arithmetic; TIFF pixel-scale/CRS tags; no application analytical imports','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'valid_pixels':valid,'selected_pixels':selected,'percent':100*selected/valid,'area_hectares':selected*dx*dy/10000,'footprint_hectares':data.shape[0]*data.shape[1]*dx*dy/10000,'mask_disagreement_pixels':int((mask!=app_mask).sum()),'max_ndvi_absolute_difference':float(np.nanmax(np.abs(values-app_ndvi)))}
(root/'results/independent-ndvi-check.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
# Display-only stretches; never feed these pixels into the measurement.
def display(indices):
 channels=[]
 for k in indices:
  a=data[:,:,k];lo,hi=np.percentile(a[np.isfinite(a)],[2,98])
  channels.append(np.clip((a-lo)/(hi-lo),0,1))
 return Image.fromarray((np.stack(channels,-1)*255).astype('uint8'))
rgb=display([0,1,2]);false=display([3,0,1])
overlay=rgb.convert('RGBA');ink=Image.new('RGBA',rgb.size)
ink.putdata([(255,215,0,170) if v else (0,0,0,0) for v in mask.flat]);overlay=Image.alpha_composite(overlay,ink).convert('RGB')
binary=Image.fromarray((mask*255).astype('uint8')).convert('RGB')
canvas=Image.new('RGB',(1048,1130),'#eeeeee');d=ImageDraw.Draw(canvas)
for im,title,pos in [(rgb,'RGB / independent 2-98% stretch',(8,32)),(false,'False colour: NIR, red, green',(528,32)),(overlay,'Gold: independent NDVI >= 0.50',(8,594)),(binary,'Selected pixels (white)',(528,594))]:
 canvas.paste(im,pos);d.text((pos[0],pos[1]-20),title,fill='black')
canvas.save(root/'results/ndvi-visual-validation.png')
assert valid==run['statistics']['valid_pixels']
assert selected==run['statistics']['selected_pixels']
assert result['mask_disagreement_pixels']==0
