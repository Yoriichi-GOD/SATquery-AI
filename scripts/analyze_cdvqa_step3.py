"""Independent official-validation joins and matched step-3 comparisons."""
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np

def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,required=True);p.add_argument("--run",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    sys.path.insert(0,str(a.repo/"scripts"))
    from analyze_cdvqa_grid import score,scene_interval
    from experiment_cdvqa_grid import rows,sha
    assert (a.run/"completed.json").is_file()
    assert not a.out.exists()
    manifest=json.loads((a.run/"manifest.json").read_text())
    summary=json.loads((a.run/"summary.json").read_text())
    data=Path("/root/satquery/cdvqa")
    for kind in ("images","questions","answers"):
        file=data/f"Val_{kind}.json";assert sha(file)==manifest["labels_sha256"][file.name]
    official=rows(data,"Val")
    assert len(official)==16441
    canonical=[(r["id"],r["image"],r["question"],r["type"],r["answer"]) for r in official]
    scenes=np.array([r["image"] for r in official]);prior=Path("/root/satquery/experiments/grid-20261020-v1")
    records={};allmetrics={}
    for seed in manifest["seeds"]:
        for label in ("grid4","balanced","continuation","encoder_projection"):
            folder=(prior if label=="grid4" else a.run)/f"{seed}-{label}"
            predictions=json.loads((folder/"validation-predictions.json").read_text())
            assert [(r["id"],r["image"],r["question"],r["type"],r["answer"]) for r in predictions]==canonical
            assert len({r["id"] for r in predictions})==16441
            met=score(predictions);records[(seed,label)]=np.array([r["answer"]==r["prediction"] for r in predictions],dtype=float)
            allmetrics[f"{seed}-{label}"]=met
            if label!="grid4":
                s=summary[f"{seed}-{label}"]
                assert met["oa"]==s["validation"]["oa"] and abs(met["aa"]-s["validation"]["aa"])<1e-12
                history=json.loads((folder/"history.json").read_text())
                assert max(history,key=lambda r:r["oa"])["epoch"]==s["best_epoch"]
                assert sha(folder/"best.pt")==s["checkpoint_sha256"]
                shuffled=json.loads((folder/"shuffled-predictions.json").read_text())
                assert [r["id"] for r in shuffled]==[r["id"] for r in official]
                sm=score([dict(**r,prediction=p["prediction"]) for r,p in zip(official,shuffled)])
                assert sm["oa"]==s["shuffled"]["oa"]
    comparisons={}
    for baseline,candidate in (("grid4","balanced"),("continuation","encoder_projection")):
        gains=[];details=[]
        for seed in manifest["seeds"]:
            gain=records[(seed,candidate)]-records[(seed,baseline)];gains.append(gain)
            b,c=[allmetrics[f"{seed}-{l}"] for l in (baseline,candidate)]
            delta={t:100*(c["by_type"][t]-b["by_type"][t]) for t in b["by_type"]}
            details.append(dict(seed=seed,oa_delta_pp=100*gain.mean(),aa_delta_pp=100*(c["aa"]-b["aa"]),
              per_type_delta_pp=delta,ci95_pp=scene_interval(gain[None,:],scenes),
              guard_pass=c["aa"]-b["aa"]>=-.01 and all(v>=-1 for v in delta.values())))
        interval=scene_interval(np.stack(gains),scenes)
        comparisons[candidate]=dict(baseline=baseline,details=details,
          mean_oa_delta_pp=float(np.mean(gains)*100),ci95_pp=interval,
          passes=interval[0]>0 and all(r["oa_delta_pp"]>0 and r["guard_pass"] for r in details))
    result=dict(metrics=allmetrics,comparisons=comparisons,serving_promoted=False,
      limitation="Validation-selected checkpoints; intervals conditional on selection. Three seeds are not independent scene samples. No unseen accuracy claim.",
      manifest_sha256=sha(a.run/"manifest.json"))
    a.out.mkdir(parents=True);(a.out/"comparison.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(comparisons,indent=2))
if __name__=="__main__":main()
