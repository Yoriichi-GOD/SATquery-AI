"""Water segmentation: small locally trained U-Net, explicitly conditioned on available sensors."""
import json,time,hashlib
from pathlib import Path
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from PIL import Image

ROOT=Path(__file__).resolve().parent
DATA=Path('/root/satquery/paired-lab/sen1floods11')
WEIGHTS=ROOT/'checkpoints/water-v1.pt'
S2_BANDS=['B01','B02','B03','B04','B05','B06','B07','B08','B8A','B09','B10','B11','B12']

class Block(nn.Sequential):
    def __init__(self,a,b):
        super().__init__(nn.Conv2d(a,b,3,padding=1,bias=False),nn.GroupNorm(4,b),nn.SiLU(),nn.Conv2d(b,b,3,padding=1,bias=False),nn.GroupNorm(4,b),nn.SiLU())

class WaterUNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.down=nn.ModuleList([Block(17,16),Block(16,32),Block(32,64),Block(64,128)])
        self.bridge=Block(128,256)
        self.up=nn.ModuleList([Block(384,128),Block(192,64),Block(96,32),Block(48,16)])
        self.head=nn.Conv2d(16,2,1)
    def forward(self,x):
        skips=[]
        for layer in self.down:x=layer(x);skips.append(x);x=F.max_pool2d(x,2)
        x=self.bridge(x)
        for layer,skip in zip(self.up,reversed(skips)):
            x=layer(torch.cat([F.interpolate(x,size=skip.shape[-2:],mode='bilinear',align_corners=False),skip],1))
        return self.head(x)

def prepare(s1,s2):
    s1=np.asarray(s1,dtype=np.float32);s2=np.asarray(s2,dtype=np.float32)
    if s1.shape[0]!=2 or s2.shape[0]!=13 or s1.shape[1:]!=s2.shape[1:]:
        raise ValueError('Water model requires corresponding VV/VH and 13-band Sentinel-2 L1C arrays.')
    valid=np.isfinite(s1).all(0)&np.isfinite(s2).all(0)
    x=np.concatenate([np.clip((s1+20)/10,-3,3),np.clip(s2/3000,0,4)],0)
    x[:,~valid]=0
    return x,valid

def available(x,mode):
    # Same availability codes are used during training and inference.
    x=x.clone();b,_,h,w=x.shape
    flags=torch.ones((b,2,h,w),device=x.device,dtype=x.dtype)
    if mode=='s1':x[:,2:]=0;flags[:,1]=0
    elif mode=='s2':x[:,:2]=0;flags[:,0]=0
    elif mode!='all':raise ValueError('Unknown sensor configuration.')
    return torch.cat([x,flags],1)

def load(device='cpu',checkpoint=None):
    path=WEIGHTS if checkpoint is None else Path(checkpoint)
    if not path.exists():raise ValueError('The water specialist has not finished training and validation.')
    ckpt=torch.load(path,map_location='cpu',weights_only=True)
    net=WaterUNet();net.load_state_dict(ckpt['state_dict'],strict=True)
    return net.to(device).eval(),ckpt

def segment(s1,s2,out,profile=None,progress=lambda stage:None):
    start=time.perf_counter();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    progress('Normalizing optical and SAR channels')
    x,valid=prepare(s1,s2);h,w=valid.shape
    if h%16 or w%16 or max(h,w)>512:raise ValueError('Water mapping needs an aligned grid up to 512 pixels, dimensions divisible by 16.')
    progress('Loading WaterUNet on CPU')
    net,ckpt=load();tensor=torch.from_numpy(x)[None];scores={};masks={}
    for mode in ['s1','s2','all']:
        progress('Predicting water: '+{'s1':'SAR only','s2':'optical only','all':'joint'}[mode])
        with torch.inference_mode():p=net(available(tensor,mode)).softmax(1)[0,1].numpy()
        mask=(p>=.5)&valid;scores[mode]=p;masks[mode]=mask
        rgba=np.zeros((h,w,4),dtype=np.uint8);rgba[valid,3]=255;rgba[mask,:3]=[51,171,237]
        Image.fromarray(rgba).save(out/(mode+'-water.png'))
    progress('Rendering water evidence and counting predicted pixels')
    rgb=np.clip(np.asarray(s2)[[3,2,1]].transpose(1,2,0)/3000,0,1)
    rgb=np.nan_to_num(rgb);rgb=(rgb*255).astype(np.uint8)
    Image.fromarray(rgb).save(out/'optical.png')
    sar=np.stack([np.clip((s1[0]+25)/30,0,1),np.clip((s1[1]+32)/30,0,1),np.clip((s1[0]-s1[1])/15,0,1)],-1)
    Image.fromarray((np.nan_to_num(sar)*255).astype(np.uint8)).save(out/'sar.png')
    overlay=rgb.copy();overlay[masks['all']]=(overlay[masks['all']]*.45+np.array([51,171,237])*.55).astype(np.uint8)
    Image.fromarray(overlay).save(out/'water-overlay.png')
    np.savez_compressed(out/'water-scores.npz',valid=valid,**scores)
    if profile:
        import rasterio
        meta={k:profile[k] for k in ['crs','transform'] if k in profile};meta.update(driver='GTiff',height=h,width=w,count=1,dtype='uint8',nodata=255)
        with rasterio.open(out/'water-mask.tif','w',**meta) as ds:ds.write(np.where(valid,masks['all'].astype(np.uint8),255).astype(np.uint8),1)
    n=int(valid.sum());counts={k:int(v.sum()) for k,v in masks.items()}
    result={'task':'water_map','answer':f'The joint optical–SAR model marks {counts["all"]:,} of {n:,} valid pixels as water ({100*counts["all"]/n:.2f}%). Blue regions show this prediction. Water includes permanent water and floodwater; this single-date pair cannot distinguish them.','water_pixels':counts,'denominator_pixels':n,'full_image_pixels':h*w,'seconds':time.perf_counter()-start,'confidence':{'kind':'uncalibrated softmax; threshold 0.5','threshold':.5},'trace':[{'tool':'SatQuery WaterUNet v1','checkpoint_sha256':hashlib.sha256(WEIGHTS.read_bytes()).hexdigest(),'training':'Sen1Floods11 official train split; selected on validation only','selected_epoch':ckpt['epoch'],'device':'cpu','normalization':'SAR clip((dB+20)/10,-3,3); S2 L1C clip(DN/3000,0,4)','sensor_availability':'Two explicit flags; modality dropout during training','bands':{'sar':['VV','VH'],'optical':S2_BANDS}}],'limitations':['Water segmentation only; no building boundaries or counts.','Single-date water is not automatically flood extent.','Fixed local research model; scores are not calibrated confidence.','Sentinel-1 GRD and Sentinel-2 L1C only; no Cartosat/RISAT validation.','Coverage denominator excludes non-finite input pixels; no surveyed area claim.']}
    (out/'result.json').write_text(json.dumps(result,indent=2));return result
