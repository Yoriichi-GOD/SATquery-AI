"""Validation-only balanced loss and final ResNet projection adaptation."""
import argparse, copy, json, sys, time, random
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torchvision.models import resnet50
from torchvision import transforms
from PIL import Image


def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--reuse-balanced",type=Path);a=p.parse_args()
    sys.path[:0]=[str(a.repo/"scripts"),str(a.repo/"paired_lab")]
    from experiment_cdvqa_grid import sha,save,rows,metrics
    from cdvqa_model import PairedAnswerModel,encode_questions
    prior=Path("/root/satquery/experiments/grid-20261020-v1")
    data=Path("/root/satquery/cdvqa")
    rgb=Path("/mnt/c/Users/nrgen/.codex/visualizations/2026/09/19/01a0b9f9-b20e-71a2-b139-ca9ab926b94e/cdvqa-data/rgb")
    encpath=Path("/root/.cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth")
    assert not a.out.exists()
    freeze=json.loads((a.repo/"docs/EVALUATION_FREEZE_20261020.json").read_text())
    assert all(sha(a.repo/n)==h for n,h in freeze["files_sha256"].items())
    old=json.loads((prior/"manifest.json").read_text());extract=json.loads((prior/"extraction.json").read_text())
    assert sha(prior/"features-grid4.pt")==extract["cache_sha256"]["4"]
    train,val=rows(data,"Train"),rows(data,"Val")
    assert (len(train),len(val))==(65967,16441)
    torch.set_num_threads(4);torch.backends.cudnn.benchmark=False
    torch.cuda.set_per_process_memory_fraction(6*1024**3/torch.cuda.get_device_properties(0).total_memory)
    a.out.mkdir(parents=True)
    manifest=dict(version=1,scope="Train/Val only; no test evaluation or serving change",
      seeds=old["seeds"],variants=["balanced","continuation","encoder_projection"],
      hypotheses={"balanced":"inverse train question-type frequency loss improves macro accuracy",
       "encoder_projection":"fine-tuning last conv3 and bn3 affine improves visual answers versus matched head continuation"},
      selection="highest validation OA; earlier checkpoint wins ties; epoch0 retained for continuation branches",
      balanced=dict(start="fresh same-seed head",lr=.001,weight_decay=.01,epochs=35,patience=7,
       loss="per-example CE times N/(8*n_type), mean over batch; weights from train only"),
      adaptation=dict(start="same seed step2 grid4 best head; pretrained last ResNet bottleneck conv3/bn3",
       head_lr=.0001,encoder_lr=.00001,weight_decay=.01,epochs=5,patience=None,
       trainable_encoder="layer4.2.conv3 weight and bn3 affine only; BN running statistics frozen",
       frozen="all preceding encoder layers and residual input; same 256px RGB and 4x4 pooled features"),
      batch=128,validation_batch=256,precision="cached encoder intermediates float16; head/last projection bfloat16",
      limits=dict(seconds=1800 if a.reuse_balanced else 2400,torch_allocated_bytes=6*1024**3,disk_bytes=4*1024**3),
      gate="OA gain positive each seed, paired scene CI excludes zero; no AA/type drop >1pp; validation-only eligibility",
      balanced_interpretation="AA improvement with OA regression is a tradeoff, not an automatic promotion",
      baseline=sha(prior/"manifest.json"),source_sha256=sha(Path(__file__)),
      model_source_sha256=sha(a.repo/"paired_lab/cdvqa_model.py"),
      labels_sha256={f"{s}_{k}.json":sha(data/f"{s}_{k}.json") for s in ("Train","Val") for k in ("images","questions","answers")},
      encoder_sha256=sha(encpath),gpu=torch.cuda.get_device_name(0),torch=torch.__version__,
      exposure="validation used for selection, historical test weaknesses known; not unseen acceptance",
      controls="matched frozen projection continuation; existing question-only baseline; cyclic unrelated validation pairs",
      amendment="Remove extraction hooks before copying projection; no training/scoring changes",
      reused_balanced=str(a.reuse_balanced) if a.reuse_balanced else None)
    save(a.out/"manifest.json",manifest);print("FROZEN",sha(a.out/"manifest.json"),flush=True)
    start=time.monotonic()
    def budget():
        assert time.monotonic()-start<manifest["limits"]["seconds"],"Wall-time budget"
        assert torch.cuda.max_memory_allocated()<6*1024**3,"GPU allocation budget"
    try:
        cache=torch.load(prior/"features-grid4.pt",weights_only=True)
        names=cache["names"];features=cache["features"].cuda();index={n:i for i,n in enumerate(names)}
        ck=torch.load(prior/f"{old['seeds'][0]}-grid4/best.pt",weights_only=True)
        vocab,answers=ck["vocab"],ck["answers"];amap={s:i for i,s in enumerate(answers)}
        def tensors(records):
            return (torch.tensor([index[r["image"]] for r in records],device="cuda"),
                    encode_questions([r["question"] for r in records],vocab).cuda(),
                    torch.tensor([amap[r["answer"]] for r in records],device="cuda"))
        tr,va=tensors(train),tensors(val)
        unique=sorted({r["image"] for r in val});shift={n:unique[(i+1)%len(unique)] for i,n in enumerate(unique)}
        shuffled=torch.tensor([index[shift[r["image"]]] for r in val],device="cuda")
        from collections import Counter
        counts=Counter(r["type"] for r in train)
        lossweights=torch.tensor([len(train)/(len(counts)*counts[r["type"]]) for r in train],device="cuda")
        summary={}
        def execute(seed,label,projection=None,intermediate=None,identity=None):
            torch.manual_seed(seed);np.random.seed(seed);random.seed(seed)
            head=PairedAnswerModel(len(vocab)+2,len(answers)).cuda()
            if label!="balanced":
                checkpoint=torch.load(prior/f"{seed}-grid4/best.pt",weights_only=True)
                head.load_state_dict(checkpoint["state_dict"])
            if projection is not None:
                projection=copy.deepcopy(projection).cuda().eval()
                for param in projection.parameters():param.requires_grad_(label=="encoder_projection")
            params=[dict(params=head.parameters(),lr=.001 if label=="balanced" else .0001)]
            if label=="encoder_projection":params.append(dict(params=projection.parameters(),lr=.00001))
            optimizer=torch.optim.AdamW(params,weight_decay=.01)
            def forward(ids,q):
                if projection is None:
                    f=features[ids]
                else:
                    x=intermediate[ids].flatten(0,1)
                    residual=identity[ids].flatten(0,1)
                    z=torch.relu(projection(x)+residual)
                    f=nn.functional.adaptive_avg_pool2d(z,(4,4)).flatten(2).transpose(1,2)
                    f=f.reshape(len(ids),2,16,2048)
                return head(f[:,0],f[:,1],q)
            def evaluate(ids=va[0]):
                head.eval();pred=[]
                with torch.inference_mode(),torch.autocast("cuda",dtype=torch.bfloat16):
                    for j in range(0,len(val),256):
                        pred.extend(forward(ids[j:j+256],va[1][j:j+256]).argmax(-1).tolist())
                return metrics(pred,val,answers),pred
            run=a.out/f"{seed}-{label}";run.mkdir();history=[];best=-1;stale=0
            tick=time.perf_counter();torch.cuda.reset_peak_memory_stats()
            def record(epoch,score,pred,loss=None):
                nonlocal best,stale
                history.append(dict(epoch=epoch,loss=loss,**score))
                save(run/"history.json",history)
                if score["oa"]>best:
                    best=score["oa"];stale=0
                    torch.save(dict(head={k:v.detach().cpu() for k,v in head.state_dict().items()},
                      projection={k:v.detach().cpu() for k,v in projection.state_dict().items()} if projection is not None else None,
                      epoch=epoch),run/"best.pt")
                    save(run/"validation-predictions.json",[dict(**r,prediction=answers[p]) for r,p in zip(val,pred)])
                else:stale+=1
                print(seed,label,epoch,round(score["oa"],5),round(score["aa"],5),flush=True)
            if label!="balanced":record(0,*evaluate())
            for epoch in range(1,36 if label=="balanced" else 6):
                head.train();order=torch.randperm(len(train),device="cuda");losses=[]
                for j in range(0,len(order),128):
                    ix=order[j:j+128];ids,q,y=[t[ix] for t in tr];optimizer.zero_grad(set_to_none=True)
                    with torch.autocast("cuda",dtype=torch.bfloat16):
                        losses_each=nn.functional.cross_entropy(forward(ids,q),y,reduction="none")
                        loss=(losses_each*lossweights[ix]).mean() if label=="balanced" else losses_each.mean()
                    loss.backward()
                    nn.utils.clip_grad_norm_([p for group in optimizer.param_groups for p in group["params"]],1)
                    optimizer.step();losses.append(loss.item());budget()
                record(epoch,*evaluate(),float(np.mean(losses)))
                if label=="balanced" and stale>=7:break
            bestck=torch.load(run/"best.pt",weights_only=True);head.load_state_dict(bestck["head"])
            if projection is not None:projection.load_state_dict(bestck["projection"])
            score,pred=evaluate();shuf,sp=evaluate(shuffled)
            assert [answers[p] for p in pred]==[r["prediction"] for r in json.loads((run/"validation-predictions.json").read_text())]
            save(run/"shuffled-predictions.json",[dict(id=r["id"],prediction=answers[p]) for r,p in zip(val,sp)])
            summary[f"{seed}-{label}"]=dict(validation=score,shuffled=shuf,best_epoch=bestck["epoch"],
               seconds=time.perf_counter()-tick,peak_bytes=torch.cuda.max_memory_allocated(),checkpoint_sha256=sha(run/"best.pt"))
            save(a.out/"summary.json",summary)
            del head,optimizer,projection;torch.cuda.empty_cache()
        if a.reuse_balanced:
            import shutil
            previous=json.loads((a.reuse_balanced/"manifest.json").read_text())
            assert previous["balanced"]==manifest["balanced"]
            assert previous["labels_sha256"]==manifest["labels_sha256"]
            previous_summary=json.loads((a.reuse_balanced/"summary.json").read_text())
            for seed in old["seeds"]:
                key=f"{seed}-balanced"
                assert sha(a.reuse_balanced/key/"best.pt")==previous_summary[key]["checkpoint_sha256"]
                shutil.copytree(a.reuse_balanced/key,a.out/key)
                summary[key]=previous_summary[key]
            save(a.out/"summary.json",summary)
        else:
            for seed in old["seeds"]:execute(seed,"balanced")
        # Cache the input to the final bottleneck projection and its unchanged skip.
        model=resnet50(weights=None);model.load_state_dict(torch.load(encpath,weights_only=True))
        model=model.eval().cuda();block=model.layer4[-1];captured={}
        handles=[block.register_forward_pre_hook(lambda mod,args:captured.update(identity=args[0].detach())),
                 block.conv3.register_forward_pre_hook(lambda mod,args:captured.update(intermediate=args[0].detach()))]
        encoder=nn.Sequential(*list(model.children())[:-2])
        transform=transforms.Compose([transforms.Resize((256,256),interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
        ins=[];skips=[];maxdiff=0;source_hashes=json.loads((prior/"input-hashes.json").read_text())
        for begin in range(0,len(names)*2,24):
            batch=[]
            for i in range(begin,min(begin+24,len(names)*2)):
                path=rgb/("im1" if i%2==0 else "im2")/names[i//2]
                assert sha(path)==source_hashes[names[i//2]][i%2]
                with Image.open(path) as im:batch.append(transform(im.convert("RGB")))
            with torch.inference_mode(),torch.autocast("cuda",dtype=torch.float16):
                actual=encoder(torch.stack(batch).cuda())
                reconstructed=block.relu(block.bn3(block.conv3(captured["intermediate"]))+captured["identity"])
                maxdiff=max(maxdiff,float((actual-reconstructed).abs().max()))
            ins.append(captured["intermediate"].cpu().half());skips.append(captured["identity"].cpu().half())
            budget()
            if begin%960==0:print("INTERMEDIATE",begin,flush=True)
        assert maxdiff==0
        for h in handles:h.remove()
        projection=nn.Sequential(copy.deepcopy(block.conv3),copy.deepcopy(block.bn3)).cpu().eval()
        assert all(not m._forward_pre_hooks for m in projection.modules())
        intermediate=torch.cat(ins).reshape(len(names),2,512,8,8).cuda()
        identity=torch.cat(skips).reshape(len(names),2,2048,8,8).cuda()
        save(a.out/"reconstruction.json",dict(max_abs_difference=maxdiff,inputs_hash_verified=True,
             note="float16 encoder reconstruction exact; continuation comparisons use same bfloat16 projection path"))
        del model,encoder,block,ins,skips,captured,actual,reconstructed,features,cache
        torch.cuda.empty_cache()
        for seed in old["seeds"]:
            for label in ("continuation","encoder_projection"):execute(seed,label,projection,intermediate,identity)
        save(a.out/"completed.json",dict(seconds=time.monotonic()-start,runs=len(summary),test_evaluated=False))
        print("COMPLETE",flush=True)
    except Exception as exc:
        save(a.out/"failure.json",dict(error=repr(exc),seconds=time.monotonic()-start));raise


if __name__=="__main__":main()
