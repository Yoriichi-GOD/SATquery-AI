import sys,json
from pathlib import Path
R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');sys.path.insert(0,str(R));import engine
import numpy as np
from PIL import Image
src=engine.DATA/'ChangeFormer/samples_LEVIR';rows=[]
# Deliberate perturbations are controls, not extra independent benchmark images.
p=src/'A/test_102_0512_0000.png';a=np.asarray(Image.open(p).convert('RGB'))
for name,b in [('brightness-only',np.clip(a.astype(float)*1.1+3,0,255).astype('uint8')),('identical-second-scene',np.asarray(Image.open(src/'A/test_77_0512_0256.png').convert('RGB')))]:
    first=a if name=='brightness-only' else b
    out=R/'evidence/controls'/name;r=engine.temporal(first,b,out);rows.append({'name':name,'kind':'synthetic-no-change-control','changed_pixels':r['changed_pixels'],'denominator':r['denominator_pixels'],'seconds':r['seconds']})
# Find a no-building-change window in a real paired crop using its reference mask.
for p in sorted((src/'label').glob('test*.png')):
    g=np.asarray(Image.open(p).convert('L'))
    found=False
    for y in [0,128]:
        for x in [0,128]:
            if g[y:y+128,x:x+128].shape!=(128,128) or np.any(g[y:y+128,x:x+128]):continue
            pair=[]
            for folder in ['A','B']:
                im=Image.open(src/folder/p.name).convert('RGB').crop((x,y,x+128,y+128)).resize((256,256),Image.Resampling.BILINEAR);pair.append(np.asarray(im))
            r=engine.temporal(*pair,R/'evidence/controls/real-pair-negative-crop')
            rows.append({'name':'real-pair-negative-crop','kind':'derived real pair; reference has zero building change','source':p.name,'source_window':[x,y,128,128],'resize':'128 to 256 bilinear; changed physical scale; not independent benchmark','changed_pixels':r['changed_pixels'],'denominator':r['denominator_pixels'],'seconds':r['seconds']});found=True;break
        if found:break
    if found:break
(R/'evidence/controls/summary.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
