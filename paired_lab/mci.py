"""Published paired change caption and road/building masks, with preserved raw caption."""
import sys,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,'/root/satquery/paired-lab/deps')
import numpy as np,torch
from PIL import Image
_cache=None
MANIFEST=Path('/root/satquery/paired-lab/mci-model/manifest.json')
def load(device='cpu'):
    global _cache
    if _cache is None:
        from mci_vendor.model_encoder_att import Encoder,AttentiveEncoder
        from mci_vendor.model_decoder import DecoderTransformer
        vocab=json.loads((ROOT/'mci_vendor/vocab.json').read_text())
        state=torch.load(json.loads(MANIFEST.read_text())['path'],map_location='cpu',weights_only=True)
        encoder=Encoder('segformer-mit_b1')
        att=AttentiveEncoder(train_stage=None,n_layers=3,feature_size=[16,16,512],heads=8,dropout=.1)
        dec=DecoderTransformer(encoder_dim=512,feature_dim=512,vocab_size=len(vocab),max_lengths=41,word_vocab=vocab,n_head=8,n_layers=1,dropout=.1)
        checks={}
        for name,net in [('encoder',encoder),('encoder_trans',att),('decoder',dec)]:
            weights=state[name+'_dict'];required=set(net.state_dict())
            missing=required-set(weights)
            if missing:raise ValueError(f'MCI checkpoint lacks required tensors: {sorted(missing)}')
            unused=sorted(set(weights)-required)
            net.load_state_dict({k:weights[k] for k in required},strict=True)
            checks[name]={'all_required_tensors_loaded':True,'unused_training_branch_tensors':unused}
            net.eval()
        _cache=(encoder,att,dec,vocab,checks)
    for net in _cache[:3]:net.to(device)
    return _cache

def infer(a,b,device='cpu',progress=lambda stage:None):
    progress('Loading or reusing MCI on CPU' if device=='cpu' else 'Loading MCI')
    encoder,att,dec,vocab,checks=load(device)
    mean=np.array([.39073,.38623,.32989],dtype=np.float32)[:,None,None]*255
    std=np.array([.15329,.14628,.13648],dtype=np.float32)[:,None,None]*255
    tensors=[torch.from_numpy((np.asarray(z,dtype=np.float32).transpose(2,0,1)-mean)/std)[None].to(device) for z in [a,b]]
    progress('Predicting road/building changes and caption')
    with torch.inference_mode():
        f1,f2=encoder(*tensors);f1,f2,logits=att(f1,f2);seq=dec.sample(f1,f2,k=1)
        probs=logits.softmax(1)[0].cpu().numpy();mask=probs.argmax(0).astype(np.uint8)
    reverse={v:k for k,v in vocab.items()};skip={vocab[k] for k in ['<START>','<END>','<NULL>']}
    caption=' '.join(reverse[w] for w in seq if w not in skip)
    return caption,mask,probs,checks

def temporal(a,b,out,progress=lambda stage:None):
    start=time.perf_counter();a=np.asarray(a);b=np.asarray(b)
    if a.shape!=(256,256,3) or b.shape!=a.shape or a.dtype!=np.uint8 or b.dtype!=np.uint8:raise ValueError('MCI needs two corresponding 256 × 256 uint8 RGB crops.')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    caption,mask,probs,checks=infer(a,b,progress=progress)
    progress('Rendering temporal masks and calculating pixel counts')
    counts={'road':int((mask==1).sum()),'building':int((mask==2).sum())};count=sum(counts.values());n=mask.size
    colour=np.zeros_like(a);colour[mask==1]=[0,210,230];colour[mask==2]=[241,183,69]
    overlay=b.copy();overlay[mask>0]=(overlay[mask>0]*.45+colour[mask>0]*.55).astype(np.uint8)
    for filename,arr in [('before.png',a),('after.png',b),('change-mask.png',colour),('overlay.png',overlay)]:Image.fromarray(arr).save(out/filename)
    np.savez_compressed(out/'scores.npz',classes=mask,scores=probs)
    result={'task':'temporal','answer':caption,'raw_caption':caption,'caption_status':'model interpretation; may be wrong','changed_pixels':count,'denominator_pixels':int(n),'coverage_percent':100*count/n,'class_pixels':counts,'direction':'caption interpretation only; masks do not encode gain/removal','seconds':time.perf_counter()-start,'confidence':{'kind':'uncalibrated class softmax','mask_rule':'argmax: unchanged / road change / building change'},'trace':[{'tool':'MCI change captioning + segmentation','checkpoint':json.loads(MANIFEST.read_text()),'device':'cpu','load_checks':checks,'normalization':'RGB channel mean/std from published inference code','decoding':'greedy; maximum 41 tokens','classes':{'0':'unchanged','1':'road change','2':'building change'}}],'limitations':['Captions can misinterpret objects, position or direction. Inspect the paired images and masks.','Masks detect changed road/building pixels; not building counts or surveyed area.','LEVIR-MCI domain; no CDVQA or Cartosat/RISAT benchmark claim.','Changes outside road/building classes can be missed.']}
    (out/'result.json').write_text(json.dumps(result,indent=2));return result
