import sys,json,time
from pathlib import Path
R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab');sys.path.insert(0,str(R));import engine
from huggingface_hub import model_info,snapshot_download
from safetensors.torch import load_file
import rasterio,timm,numpy as np,torch
report={'selection_rule':'Compare pooled F1 at fixed 0.5 on six validation fixtures only; no threshold fitting. Evaluate test-named fixtures after selection. Tiny one-scene trial does not establish generalisation.','models':{},'rows':[]}
def f1(rows):
    tp=sum(r['tp'] for r in rows);fp=sum(r['fp'] for r in rows);fn=sum(r['fn'] for r in rows);return 2*tp/(2*tp+fp+fn)
old=json.loads((R/'evidence/first-trials/summary.json').read_text())
for kind in ['all','s1','s2']:
    name=f'BIFOLD-BigEarthNetv2-0/resnet50-{kind}-v0.2.0';info=model_info(name)
    folder=snapshot_download(name,revision=info.sha,allow_patterns=['config.json','model.safetensors','README.md'])
    report['models'][kind]={'repo':name,'revision':info.sha,'path':folder}
    order={'all':engine.S1+engine.S2,'s1':engine.S1,'s2':engine.S2}[kind]
    net=timm.create_model('resnet50',pretrained=False,in_chans=len(order),num_classes=19,drop_rate=.15,drop_path_rate=.15)
    state=load_file(str(Path(folder)/'model.safetensors'));prefix='model.vision_encoder.'
    assert all(k.startswith(prefix) for k in state)
    net.load_state_dict({k[len(prefix):]:v for k,v in state.items()},strict=True);net.eval()
    for row in old['optical_sar']:
        if row['split']!='validation':continue
        bands={}
        for filename in ['optical.tif','sar.tif']:
            with rasterio.open(R/'samples'/row['sample']/filename) as ds:bands.update({n:v for n,v in zip(ds.descriptions,ds.read())})
        start=time.perf_counter()
        with torch.inference_mode():scores=net(engine.normalize(bands,order)).sigmoid()[0].numpy()
        p=scores>=.5;g=np.array([c in row['reference_labels'] for c in engine.CLASSES]);m={'tp':int((p&g).sum()),'fp':int((p&~g).sum()),'fn':int((~p&g).sum())}
        report['rows'].append({'sample':row['sample'],'kind':kind,'scores':dict(zip(engine.CLASSES,map(float,scores))),'metrics':m,'seconds':time.perf_counter()-start})
    print(kind,'validation F1',f1([r['metrics'] for r in report['rows'] if r['kind']==kind]),flush=True)
baseline=f1([r['metrics']['all'] for r in old['optical_sar'] if r['split']=='validation']);candidate=f1([r['metrics'] for r in report['rows'] if r['kind']=='all'])
report.update({'baseline_joint_f1':baseline,'candidate_joint_f1':candidate,'promote':candidate>baseline})
(R/'evidence/refinement.json').write_text(json.dumps(report,indent=2));print('DECISION',baseline,candidate,report['promote'],flush=True)
