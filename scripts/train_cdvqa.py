"""Train/validate only. Test answers are deliberately not loaded here."""
import os,sys,json,time,hashlib,random,collections
from pathlib import Path
import numpy as np,torch
from torch import nn
from PIL import Image
from torchvision.models import resnet50,ResNet50_Weights
from torchvision import transforms
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI');sys.path.insert(0,str(ROOT/'paired_lab'))
from cdvqa_model import PairedAnswerModel,encode_questions,tokens
DATA=Path('/root/satquery/cdvqa');OUT=ROOT/'paired_lab/evidence/cdvqa-trained-20260928';OUT.mkdir(exist_ok=True)
RGB=Path('/mnt/c/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/cdvqa-data/rgb')
OLD=ROOT/'paired_lab/evidence/cdvqa-20260927'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2))
def load(split):
    folder=DATA if split in ['Train','Val'] else OLD
    images={i['id']:i['file_name'] for i in json.loads((folder/(split+'_images.json')).read_text())['images']}
    if split=='Test':return sorted(set(images.values()))
    qs=json.loads((folder/(split+'_questions.json')).read_text())['questions'];ans={a['id']:a['answer'] for a in json.loads((folder/(split+'_answers.json')).read_text())['answers']}
    return [dict(id=q['id'],question=q['question'],type=q['type'],image=images[q['img_id']],answer=ans[q['answers_ids'][0]]) for q in qs if q['active']]

def main():
    torch.set_num_threads(4);torch.manual_seed(20260928);np.random.seed(20260928);random.seed(20260928)
    train=load('Train');val=load('Val');test_names=load('Test')
    sets=[{r['image'] for r in train},{r['image'] for r in val},set(test_names)]
    assert not (sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2])
    names=sorted(set.union(*sets));index={name:i for i,name in enumerate(names)}
    assert len(names)==2968
    vocab={w:i+2 for i,w in enumerate(sorted({t for r in train for t in tokens(r['question'])}))};answers=sorted({r['answer'] for r in train});amap={a:i for i,a in enumerate(answers)}
    save('protocol.json',dict(seed=20260928,train_questions=len(train),val_questions=len(val),train_pairs=len(sets[0]),val_pairs=len(sets[1]),test_pairs=len(sets[2]),split_pair_overlap=0,selection='Highest official validation overall exact-match accuracy; maximum 35 epochs, patience 7, AdamW lr 0.001 weight decay 0.01, batch 128. Paired model versus question-only baseline. No test answers loaded for selection.',encoder='torchvision ResNet50 IMAGENET1K_V2, frozen; RGB full-image resize 256x256, ImageNet mean/std; layer4 adaptive 4x4 spatial features.',answers=answers,vocab=vocab,train_label_hashes={p.name:sha(p) for p in DATA.glob('*.json')},code_hashes={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'paired_lab/cdvqa_model.py',ROOT/'scripts/train_cdvqa.py']},upstream_exposure='ImageNet pretrained encoder; remote-sensing benchmark pretraining exposure not independently audited. Test metadata read for disjointness and feature caching only; model does not receive filenames/IDs/labels.',prior_test_inspection='12 Test pairs previously probed; final metrics must separate those from remaining pairs.'))
    featurefile=DATA/'resnet50-features.pt'
    if not featurefile.exists():
        model=resnet50(weights=ResNet50_Weights.IMAGENET1K_V2).eval().cuda();encoder=nn.Sequential(*list(model.children())[:-2]).eval()
        transform=transforms.Compose([transforms.Resize((256,256),interpolation=transforms.InterpolationMode.BILINEAR),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
        class Images(torch.utils.data.Dataset):
            def __len__(self):return len(names)*2
            def __getitem__(self,i):
                p=RGB/('im1' if i%2==0 else 'im2')/names[i//2]
                with Image.open(p) as im:x=transform(im.convert('RGB'))
                return x,sha(p)
        loader=torch.utils.data.DataLoader(Images(),batch_size=24,num_workers=4,pin_memory=True)
        features=[];hashes=[];start=time.perf_counter()
        with torch.inference_mode():
            for batch,(x,h) in enumerate(loader):
                with torch.autocast('cuda',dtype=torch.float16):f=encoder(x.cuda(non_blocking=True));f=nn.functional.adaptive_avg_pool2d(f,(4,4)).flatten(2).transpose(1,2)
                features.append(f.cpu().half());hashes.extend(h)
                if batch%15==0:print('FEATURES',min((batch+1)*24,len(names)*2),'/',len(names)*2,round(time.perf_counter()-start,1),flush=True)
        tensor=torch.cat(features).reshape(len(names),2,16,2048)
        torch.save(dict(names=names,features=tensor,hashes=hashes),featurefile)
        save('encoder.json',dict(weights='ResNet50_Weights.IMAGENET1K_V2',checkpoint_hashes={p.name:sha(p) for p in Path('/root/.cache/torch/hub/checkpoints').glob('resnet50*')},extraction_seconds=time.perf_counter()-start,feature_cache_sha256=sha(featurefile)))
        del model,encoder,tensor,features;torch.cuda.empty_cache()
    data=torch.load(featurefile,weights_only=True);assert data['names']==names
    pairhash={name:hashlib.sha256((data['hashes'][2*i]+data['hashes'][2*i+1]).encode()).hexdigest() for i,name in enumerate(names)}
    hs=[{pairhash[n] for n in s} for s in sets]
    assert not (hs[0]&hs[1] or hs[0]&hs[2] or hs[1]&hs[2]),'Exact duplicated pair across splits'
    save('input-hashes.json',{n:dict(before=data['hashes'][2*i],after=data['hashes'][2*i+1],pair=pairhash[n]) for i,n in enumerate(names)})
    feat=data['features'].cuda();del data
    def tensors(rows):return (torch.tensor([index[r['image']] for r in rows],device='cuda'),encode_questions([r['question'] for r in rows],vocab).cuda(),torch.tensor([amap[r['answer']] for r in rows],device='cuda'))
    tr=tensors(train);va=tensors(val)
    def evaluate(model,inputs,rows):
        ids,q,y=inputs;pred=[];model.eval()
        with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16):
            for begin in range(0,len(ids),256):
                ix=ids[begin:begin+256];pred.extend(model(feat[ix,0],feat[ix,1],q[begin:begin+256]).argmax(-1).tolist())
        correct=np.array(pred)==y.cpu().numpy();by={typ:float(correct[[i for i,r in enumerate(rows) if r['type']==typ]].mean()) for typ in sorted({r['type'] for r in rows})}
        return dict(oa=float(correct.mean()),aa=float(np.mean(list(by.values()))),by_type=by),pred
    results={}
    for label,qonly in [('question_only',True),('paired',False)]:
        torch.manual_seed(20260928);model=PairedAnswerModel(len(vocab)+2,len(answers),qonly).cuda();optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.01);best=-1.;stale=0;history=[];start=time.perf_counter()
        for epoch in range(1,36):
            model.train();order=torch.randperm(len(train),device='cuda');losses=[]
            for begin in range(0,len(order),128):
                ix=order[begin:begin+128];im,q,y=[t[ix] for t in tr];optimizer.zero_grad(set_to_none=True)
                with torch.autocast('cuda',dtype=torch.bfloat16):loss=nn.functional.cross_entropy(model(feat[im,0],feat[im,1],q),y)
                loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1);optimizer.step();losses.append(loss.item())
            metrics,pred=evaluate(model,va,val);history.append(dict(epoch=epoch,loss=float(np.mean(losses)),**metrics));save(label+'-history.json',history)
            print(label,'EPOCH',epoch,'LOSS',round(float(np.mean(losses)),4),'VAL',metrics,'SECONDS',round(time.perf_counter()-start,1),flush=True)
            if metrics['oa']>best:
                best=metrics['oa'];stale=0
                torch.save(dict(state_dict=model.cpu().state_dict(),vocab=vocab,answers=answers,question_only=qonly,epoch=epoch,validation=metrics,architecture='paired-resnet50-gru-attention-v1'),DATA/(label+'-best.pt'));model.cuda()
                save(label+'-validation-predictions.json',[dict(**r,prediction=answers[v]) for r,v in zip(val,pred)])
            else:stale+=1
            if stale>=7:break
        results[label]=dict(best_validation=best,seconds=time.perf_counter()-start,checkpoint_sha256=sha(DATA/(label+'-best.pt')))
        save('training-summary.json',results);del model,optimizer;torch.cuda.empty_cache()
    print('TRAINING COMPLETE',results,flush=True)

if __name__=='__main__':main()
