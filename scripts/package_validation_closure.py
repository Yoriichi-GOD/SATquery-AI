"""Collect new validation receipts without changing the prior frozen case campaign."""
import argparse,json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.terrain_exposure.io import save_json,sha256

ROOT=Path(__file__).resolve().parents[1]
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)

def package(output):
    out=Path(output)
    if out.exists():raise FileExistsError('Choose a new immutable validation review pack')
    out.mkdir(parents=True);sources=ROOT/'research/datasets/local/validation-20261107';work=ROOT/'.runtime/validation-20261107'
    notes=ROOT.parents[1]/'research-validation-20261107'
    for name in ['validation-closure-20261107.json','worldfloods-blind-20261107.json','nepal-postevent-2m-20261107.json','worldfloods-reserve-20261107.json']:
        copy(ROOT/'research/experiments'/name,out/'protocols'/name)
    wf=sources/'worldfloods-component-v1'
    for name in ['summary.json','metrics.csv','prediction-seal.json','population-seal.json','manifest.json']:
        copy(wf/name,out/'external-water'/name)
    for folder in wf.iterdir():
        if folder.is_dir():
            for name in ['metrics.json','input.source.json','reference.source.json','comparison.png']:
                if (folder/name).is_file():copy(folder/name,out/'external-water'/folder.name/name)
    for p in (work/'independent-v2').iterdir():
        if p.is_file():copy(p,out/'verification/independent-recount'/p.name)
    for name in ['summary.json','manifest.json','drainage-context.png','drainage-context.pdf']:
        copy(work/'delhi-drainage-v1'/name,out/'delhi'/name)
    copy(sources/'delhi-official-v1/acquisition.json',out/'delhi/source-acquisition.json')
    kd=sources/'kedarnath-quality-v1'
    for name in ['quality-rows.json','selection.json','sealed-candidate-ids.json']:
        copy(kd/name,out/'kedarnath'/name)
    for name in ['qa-exclusions.json','rasuwa-2m-access.json']:
        copy(notes/name,out/'sources'/name)
    for name in ['regression-final.log','floodlab-regression.log','baseline-regression.log','validation-unit-final.log',
        'kedarnath-quality.log','delhi-acquisition.log','worldfloods.log','independent-verification.log','independent-verification-v2.log','nepal-2m.log']:
        if (notes/name).is_file():copy(notes/name,out/'verification'/name)
    high=sources/'nepal-postevent2m-v1'
    if (high/'summary.json').is_file():
        for name in ['summary.json','manifest.json','elevation.source.json','input_count.source.json']:
            copy(high/name,out/'nepal-2m'/name)
        terrain_figure(high,out/'nepal-2m')
    rawfiles={p.relative_to(sources).as_posix():sha256(p) for p in sources.rglob('*') if p.is_file()}
    save_json(out/'LOCAL_DATA_MANIFEST.json',{'local_root':'research/datasets/local/validation-20261107','files':rawfiles,
        'license_roles':'Rawofficialdrainageretainedprivate;WorldFloods/ZenodoCCBYNC4;LandsatUSGSpublicdata;perassetreceiptsapply'})
    figures(out)
    print(json.dumps({'review_pack':str(out),'private_source_files':len(rawfiles)}))

def figures(out):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    value=json.loads((out/'external-water/summary.json').read_text());ids=list(value['events'])
    methods=['MNDWI0','NDWI0','MNDWI0_slope15'];labels=['MNDWI >0','NDWI >0','MNDWI +slope≤15°']
    fig,ax=plt.subplots(figsize=(11,4.8),layout='constrained');x=np.arange(len(ids))
    for i,(method,label,color) in enumerate(zip(methods,labels,['#262626','#888888','#b05739'])):
        ax.bar(x+(i-1)*.25,[value['events'][n]['metrics'][method]['iou'] for n in ids],.25,label=label,color=color)
    ax.set_xticks(x,[n.split('_')[0]+'\n'+n.split('_')[1] for n in ids],fontsize=8)
    ax.set_ylim(0,1);ax.set_ylabel('Water IoU, same reference-clear support');ax.legend(fontsize=8)
    ax.set_title('Six preselected WorldFloodsv2 test windows; no training or threshold tuning\nComponent agreement only; curated water labels are not case-specific exposure truth',fontsize=10)
    fig.savefig(out/'external-water/comparison.png',dpi=180);fig.savefig(out/'external-water/comparison.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4.2),layout='constrained')
    totals=value['totals'];x=np.arange(3)
    ax.bar(x-.18,[totals[n]['iou'] for n in methods],.36,color='#333333',label='Micro IoU')
    ax.bar(x+.18,[totals[n]['macro_event_iou'] for n in methods],.36,color='#999999',label='Macro event IoU')
    ax.set_xticks(x,labels);ax.set_ylim(0,1);ax.set_ylabel('Water IoU');ax.legend()
    ax.set_title('1,548,021 evaluated pixels across six fixed windows\nMicro aggregation hides substantial event variation',fontsize=10)
    fig.savefig(out/'external-water/micro-macro.png',dpi=180);fig.savefig(out/'external-water/micro-macro.pdf');plt.close(fig)

def terrain_figure(source,out):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    import rasterio
    fig,axes=plt.subplots(1,3,figsize=(12,4.2),layout='constrained')
    for ax,name,title in zip(axes,['dem-5m.tif','slope-5m.tif','hand-5m.tif'],
        ['Post-event elevation (m WGS84 ellipsoid)','Slope from 5 m analysis (degrees)','Flowpath HAND, 5 m model (m)']):
        with rasterio.open(source/name) as ds:data=ds.read(1,masked=True)
        cmap=plt.get_cmap('terrain' if name.startswith('dem') else 'viridis').copy();cmap.set_bad('#ddd')
        im=ax.imshow(data,cmap=cmap);ax.set_title(title,fontsize=9);ax.axis('off');fig.colorbar(im,ax=ax,shrink=.7)
    fig.suptitle('Native 2 m Nepal post-event DEM; analysis 5 m; quality coverage 89.98%\nGray=unknown. Post-event morphology, not validated prior hazard or damage.',fontsize=10)
    fig.savefig(out/'postevent-terrain.png',dpi=170);fig.savefig(out/'postevent-terrain.pdf');plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();package(a.output)
