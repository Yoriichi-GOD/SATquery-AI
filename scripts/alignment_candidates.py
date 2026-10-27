import json,hashlib
from pathlib import Path
import numpy as np,rasterio
from rasterio.windows import Window,from_bounds
from PIL import Image,ImageDraw
P=Path('/root/satquery/acquisition/s1s2-water-7-v2')
E=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/.runtime/alignment-20261021')
regions=[(5800,4700),(700,8800),(900,5700)]
manifest={'purpose':'Development landmark visibility screening, never acceptance selection','selection':'Three visually settlement-like regions from optical overview; no labels or model scores read','windows_col_row':regions,'size':1024,'accepted_landmarks':None,'inference':False}
(E/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2))
for n,(x,y) in enumerate(regions,1):
    arrays=[]
    for b in ['B04','B03','B02']:
        with rasterio.open(next(P.glob('*_'+b+'.jp2'))) as ds:
            w=Window(x,y,1024,1024);arrays.append(ds.read(1,window=w));bounds=ds.window_bounds(w);crs=ds.crs
    rgb=np.clip(np.stack(arrays,-1)/3000,0,1)
    with rasterio.open(P/'sentinel12_s1_7_img.tif') as ds:
        assert ds.crs==crs
        sw=from_bounds(*bounds,transform=ds.transform)
        sar=ds.read(1,window=sw,out_shape=(1024,1024)).astype('float32')/100
    sheet=Image.new('RGB',(2048,1060),'white')
    sheet.paste(Image.fromarray((rgb*255).astype('uint8')),(0,36))
    sheet.paste(Image.fromarray((np.clip((sar+25)/25,0,1)*255).astype('uint8')).convert('RGB'),(1024,36))
    ImageDraw.Draw(sheet).text((10,10),f'Candidate {n}; optical window {x},{y}; raw SAR right; 1 display pixel = 10m',fill='black')
    sheet.save(E/f'candidate-{n}.png')
print('Three candidate pairs saved')
