"""Isolated CPU specialists. No imports or changes to the existing demo."""
import sys,ast,json,time,hashlib
from pathlib import Path
DATA=Path('/root/satquery/paired-lab')
sys.path.insert(0,str(DATA/'deps'))
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
torch.set_num_threads(4)
MODELS=json.loads((DATA/'models.json').read_text())
S1=['VV','VH']
S2=['B02','B03','B04','B05','B06','B07','B08','B8A','B11','B12']
source=DATA/'ConfigILM/configilm/extra/BENv2_utils.py'
constants={}
for node in ast.parse(source.read_text()).body:
    if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ['means','stds','NEW_LABELS_ORIGINAL_ORDER']:
        constants[node.targets[0].id]=ast.literal_eval(node.value)
CLASSES=sorted(constants['NEW_LABELS_ORIGINAL_ORDER'])
_temporal=None;_fusion={}

def load_temporal():
    global _temporal
    if _temporal is None:
        sys.path.insert(0,str(DATA/'ChangeFormer'))
        from models.ChangeFormer import ChangeFormerV6
        candidate=ChangeFormerV6(embed_dim=256)
        # Only permit numeric numpy globals; do not disable the safe weights loader.
        with torch.serialization.safe_globals([(np.core.multiarray.scalar,'numpy.core.multiarray.scalar'),np.dtype,type(np.dtype(np.float64)),type(np.dtype(np.float32))]):
            ckpt=torch.load(MODELS['temporal']['path'],map_location='cpu',weights_only=True)
        candidate.load_state_dict(ckpt['model_G_state_dict'],strict=True)
        _temporal=candidate.eval()
    return _temporal

def temporal(a,b,out):
    start=time.perf_counter();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    a=np.asarray(a);b=np.asarray(b)
    if a.shape!=b.shape or a.ndim!=3 or a.shape[2]!=3:raise ValueError('Temporal inputs must be corresponding RGB grids of equal size.')
    if a.dtype!=np.uint8 or b.dtype!=np.uint8:raise ValueError('This checkpoint requires 8-bit RGB; explicit calibrated rendering is required for other inputs.')
    h,w=a.shape[:2]
    if h!=256 or w!=256:raise ValueError('Use a corresponding 256 x 256 RGB crop for this initial specialist. No silent resizing of large scenes.')
    net=load_temporal()
    x=torch.from_numpy(a.copy()).permute(2,0,1).float().unsqueeze(0)/127.5-1
    y=torch.from_numpy(b.copy()).permute(2,0,1).float().unsqueeze(0)/127.5-1
    with torch.inference_mode():
        logits=net(x,y)[-1]
        scores=logits.softmax(1)[0,1].numpy()
    mask=scores>=0.5
    Image.fromarray(a).save(out/'before.png');Image.fromarray(b).save(out/'after.png')
    Image.fromarray(mask.astype('uint8')*255).save(out/'change-mask.png')
    overlay=b.copy();overlay[mask]=(0.45*overlay[mask]+0.55*np.array([241,183,69])).astype('uint8')
    Image.fromarray(overlay).save(out/'overlay.png');np.savez_compressed(out/'scores.npz',change_score=scores,mask=mask)
    quadrants={}
    for name,ys,xs in [('upper left',slice(0,h//2),slice(0,w//2)),('upper right',slice(0,h//2),slice(w//2,w)),('lower left',slice(h//2,h),slice(0,w//2)),('lower right',slice(h//2,h),slice(w//2,w))]:
        quadrants[name]=int(mask[ys,xs].sum())
    count=int(mask.sum());coverage=100*count/mask.size
    if count:
        answer=f'The model marks possible building-related changes across {coverage:.2f}% of the full crop, with the most marked pixels in the {max(quadrants,key=quadrants.get)}. This binary map does not distinguish construction from removal.'
    else:answer='The model marks no building-related change in this crop. This is not proof that every type of change is absent.'
    result={'task':'temporal','answer':answer,'changed_pixels':count,'denominator_pixels':int(mask.size),'coverage_percent':coverage,'quadrant_pixels':quadrants,'direction':'not determined','seconds':time.perf_counter()-start,'confidence':{'kind':'uncalibrated model scores','mean_marked_score':float(scores[mask].mean()) if count else None},'trace':[{'tool':'ChangeFormerV6 LEVIR','revision':MODELS['temporal']['revision'],'device':'cpu','input_shape':[h,w,3],'normalization':'RGB / 127.5 - 1','threshold':0.5,'output':'last decoder head; two-class softmax','checkpoint_sha256':MODELS['temporal']['sha256']}], 'limitations':['Building-change specialist; not general change VQA.','No increase/decrease or surveyed-area claim.','LEVIR development evidence does not establish CDVQA or ISRO/SAC performance.']}
    (out/'result.json').write_text(json.dumps(result,indent=2));return result

def normalize(bands,order):
    values=[]
    for name in order:
        arr=np.asarray(bands[name],dtype=np.float32)
        if arr.ndim!=2 or not np.isfinite(arr).all():raise ValueError('Each band must contain finite 2D calibrated data.')
        x=torch.from_numpy(arr.copy())[None,None]
        if x.shape[-2:]!=(120,120):x=F.interpolate(x,size=(120,120),mode='nearest')
        values.append((x[0,0]-constants['means']['120_nearest'][name])/constants['stds']['120_nearest'][name])
    return torch.stack(values)[None]

def load_fusion(kind):
    if kind not in _fusion:
        import timm
        from safetensors.torch import load_file
        order={'s1':S1,'s2':S2,'all':S1+S2}[kind]
        architecture=json.loads((Path(MODELS[kind]['path'])/'config.json').read_text())['timm_model_name']
        net=timm.create_model(architecture,pretrained=False,in_chans=len(order),num_classes=19,drop_rate=.15,drop_path_rate=.15)
        state=load_file(str(Path(MODELS[kind]['path'])/'model.safetensors'))
        prefix='model.vision_encoder.'
        if not all(k.startswith(prefix) for k in state):raise ValueError('Unexpected checkpoint keys.')
        net.load_state_dict({k[len(prefix):]:v for k,v in state.items()},strict=True)
        _fusion[kind]=net.eval()
    return _fusion[kind]

def fusion(bands,out,progress=lambda stage:None):
    start=time.perf_counter();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if set(bands)!=set(S1+S2):raise ValueError('Joint inference requires VV, VH and all ten declared Sentinel-2 bands.')
    predictions={};trace=[]
    for kind,order in [('s1',S1),('s2',S2),('all',S1+S2)]:
        progress('Loading or reusing '+kind+' land-cover model on CPU')
        x=normalize(bands,order);net=load_fusion(kind)
        progress('Predicting land-cover scores: '+kind)
        with torch.inference_mode():scores=net(x).sigmoid()[0].numpy()
        predictions[kind]={c:float(v) for c,v in zip(CLASSES,scores)}
        trace.append({'tool':MODELS[kind]['repo'],'revision':MODELS[kind]['revision'],'device':'cpu','bands':order,'normalization':'reBEN 120_nearest training mean/std','input_shape':list(x.shape),'threshold':0.5})
    progress('Rendering land-cover evidence')
    rgb=np.stack([np.asarray(bands[x],dtype=float) for x in ['B04','B03','B02']],axis=-1)
    rgb=np.clip(rgb/3000,0,1);Image.fromarray((rgb*255).astype('uint8')).save(out/'optical.png')
    vv=np.asarray(bands['VV']);vh=np.asarray(bands['VH'])
    sar=np.stack([np.clip((vv+25)/30,0,1),np.clip((vh+32)/30,0,1),np.clip((vv-vh)/15,0,1)],axis=-1)
    Image.fromarray((sar*255).astype('uint8')).save(out/'sar.png')
    selected=[c for c in CLASSES if predictions['all'][c]>=.5]
    answer='The jointly trained optical–SAR model suggests '+(', '.join(selected) if selected else 'no class above the 0.5 display threshold')+'. These are scene-level land-cover labels, not mapped regions or measured area.'
    result={'task':'optical_sar','answer':answer,'classes':selected,'scores':predictions,'seconds':time.perf_counter()-start,'trace':trace,'confidence':{'kind':'uncalibrated sigmoid scores; not accuracy','threshold':.5},'limitations':['Sentinel-1 VV/VH and Sentinel-2 multispectral only; no demonstrated Cartosat/RISAT transfer.','Scene classification cannot locate built-up/water regions.','Fusion superiority must be tested; more sensors do not guarantee a better answer.']}
    (out/'result.json').write_text(json.dumps(result,indent=2));return result
