import sys,json,time,random,hashlib,os
from pathlib import Path
P=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');sys.path.insert(0,str(P))
import flood
import torch,numpy as np,rasterio
from torch.utils.data import Dataset,DataLoader
torch.set_num_threads(4);torch.manual_seed(42);np.random.seed(42);random.seed(42)
torch.backends.cudnn.benchmark=False
D=flood.DATA;O=D/'training';O.mkdir(exist_ok=True)
splits=json.loads((D/'splits.json').read_text())
assert all(not set(splits[a])&set(splits[b]) for a,b in [('train','valid'),('train','test'),('valid','test'),('train','bolivia')])
def read(sid):
    arrays=[]
    for layer in ['S1Hand','S2Hand','LabelHand']:
        with rasterio.open(D/layer/(sid+'_'+layer+'.tif')) as ds:arrays.append(ds.read() if layer=='LabelHand' else ds.read(masked=True).astype('float32').filled(np.nan))
    x,valid=flood.prepare(*arrays[:2]);y=arrays[2][0].astype(np.int64);y[~valid]=-1
    return x,y
class TrainSet(Dataset):
    def __init__(self):self.cache=[read(sid) for sid in splits['train']]
    def __len__(self):return len(self.cache)*2
    def __getitem__(self,i):
        x,y=self.cache[i%len(self.cache)];h,w=y.shape;yy=random.randint(0,h-256);xx=random.randint(0,w-256)
        x=x[:,yy:yy+256,xx:xx+256];y=y[yy:yy+256,xx:xx+256];rot=random.randrange(4)
        x=np.rot90(x,rot,axes=(-2,-1));y=np.rot90(y,rot)
        if random.random()<.5:x=x[:,:,::-1];y=y[:,::-1]
        return torch.from_numpy(x.copy()),torch.from_numpy(y.copy())
def metrics(tp,fp,fn,tn):
    return {'tp':tp,'fp':fp,'fn':fn,'tn':tn,'water_iou':tp/(tp+fp+fn) if tp+fp+fn else None,'water_f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}
def score(net,cache,modes):
    totals={m:np.zeros(4,dtype=np.int64) for m in modes};rows=[]
    for sid,x,y in cache:
        x=torch.from_numpy(x)[None].cuda();valid=y>=0;truth=y==1;row={'sample':sid}
        for mode in modes:
            with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):pred=net(flood.available(x,mode)).argmax(1)[0].cpu().numpy()==1
            v=np.array([(pred&truth&valid).sum(),(pred&~truth&valid).sum(),(~pred&truth&valid).sum(),(~pred&~truth&valid).sum()],dtype=np.int64);totals[mode]+=v;row[mode]=metrics(*map(int,v))
        rows.append(row)
    return {'aggregate':{m:metrics(*map(int,v)) for m,v in totals.items()},'samples':rows}
print('Reading official training and validation data; test data remains unopened until model selection is finished.',flush=True)
train=TrainSet();valid=[(sid,*read(sid)) for sid in splits['valid']]
loader=DataLoader(train,batch_size=8,shuffle=True,num_workers=0,pin_memory=True)
net=flood.WaterUNet().cuda();optimizer=torch.optim.AdamW(net.parameters(),lr=.001,weight_decay=.0001)
scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=35,eta_min=.00005)
scaler=torch.amp.GradScaler('cuda');weights=torch.tensor([1.,2.],device='cuda')
best=-1;history=[];start=time.perf_counter();torch.cuda.reset_peak_memory_stats()
for epoch in range(1,36):
    net.train();losses=[]
    for x,y in loader:
        x=x.cuda(non_blocking=True);y=y.cuda(non_blocking=True);mode=random.choice(['s1','s2','all']);optimizer.zero_grad(set_to_none=True)
        with torch.autocast('cuda',dtype=torch.float16):
            logits=net(flood.available(x,mode));good=y>=0
            if not good.any():continue
            ce=torch.nn.functional.cross_entropy(logits,y,weight=weights,ignore_index=-1)
            prob=logits.softmax(1)[:,1];target=y==1;dice=1-(2*(prob*target*good).sum()+1)/((prob*good).sum()+(target*good).sum()+1);loss=ce+dice
        scaler.scale(loss).backward();scaler.unscale_(optimizer);torch.nn.utils.clip_grad_norm_(net.parameters(),5);scaler.step(optimizer);scaler.update();losses.append(float(loss.detach()))
    scheduler.step();net.eval();evaluation=score(net,valid,['all']);iou=evaluation['aggregate']['all']['water_iou']
    row={'epoch':epoch,'mean_loss':float(np.mean(losses)),'validation_joint':evaluation['aggregate']['all'],'elapsed_seconds':time.perf_counter()-start};history.append(row)
    if iou>best:
        best=iou;torch.save({'state_dict':net.cpu().state_dict(),'epoch':epoch,'validation_iou':iou,'seed':42,'architecture':'WaterUNet17-16-32-64-128-256','training_samples':len(train.cache)},O/'best.pt');net.cuda()
    (O/'history.json').write_text(json.dumps(history,indent=2));print(json.dumps(row),flush=True)
print('Model selection complete. Opening test and Bolivia holdout now.',flush=True)
net,_=flood.load('cuda',O/'best.pt');report={'model':'SatQuery WaterUNet v1','parameters':sum(p.numel() for p in net.parameters()),'selected_validation_iou':best,'training_seconds':time.perf_counter()-start,'training_peak_allocated_MiB':torch.cuda.max_memory_allocated()/2**20,'training_peak_reserved_MiB':torch.cuda.max_memory_reserved()/2**20,'history':history,'split_overlap':False,'interpretation':'Official split pixel water segmentation. Official test shares event regions with training; Bolivia is separate event holdout. No ISRO or building accuracy claim.'}
for split in ['valid','test','bolivia']:
    cache=valid if split=='valid' else [(sid,*read(sid)) for sid in splits[split]]
    report[split]=score(net,cache,['s1','s2','all']);print(split,json.dumps(report[split]['aggregate']),flush=True)
    (O/'evaluation.json').write_text(json.dumps(report,indent=2));(P/'evidence/resumed/water-evaluation.json').write_text(json.dumps(report,indent=2))
print('FINISHED',flush=True)
