"""Independently score saved validation predictions and paired scene uncertainty."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def score(rows):
    c=np.array([r["prediction"]==r["answer"] for r in rows])
    by={t:float(c[[i for i,r in enumerate(rows) if r["type"]==t]].mean())
        for t in sorted({r["type"] for r in rows})}
    return dict(oa=float(c.mean()),aa=float(np.mean(list(by.values()))),by_type=by)


def scene_interval(gains, scenes):
    """Gains shape seeds x questions. Resample scenes, average matched seeds."""
    unique=sorted(set(scenes));groups={s:np.where(scenes==s)[0] for s in unique}
    sums=np.array([gains[:,groups[s]].sum(axis=1) for s in unique])
    counts=np.array([len(groups[s]) for s in unique])
    rng=np.random.default_rng(20261020);samples=[]
    for _ in range(1000):
        ix=rng.integers(0,len(unique),len(unique))
        samples.append(float((sums[ix].sum(axis=0)/counts[ix].sum()).mean())*100)
    return list(map(float,np.percentile(samples,[2.5,97.5])))


def main():
    p=argparse.ArgumentParser();p.add_argument("run",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--data",type=Path,default=Path("/root/satquery/cdvqa"));a=p.parse_args()
    assert (a.run/"completed.json").is_file(),"All predeclared runs must finish"
    assert not a.out.exists(),"Analysis outputs must be new"
    m=json.loads((a.run/"manifest.json").read_text())
    saved=json.loads((a.run/"summary.json").read_text())
    # Independent join back to official validation records, not just run-to-run agreement.
    for kind in ("images","questions","answers"):
        file=a.data/f"Val_{kind}.json"
        assert hashlib.sha256(file.read_bytes()).hexdigest()==m["labels_sha256"][file.name]
    images={r["id"]:r["file_name"] for r in json.loads((a.data/"Val_images.json").read_text())["images"]}
    refs={r["id"]:r["answer"] for r in json.loads((a.data/"Val_answers.json").read_text())["answers"]}
    questions=json.loads((a.data/"Val_questions.json").read_text())["questions"]
    canonical=[(r["id"],images[r["img_id"]],r["question"],r["type"],refs[r["answers_ids"][0]])
               for r in questions if r["active"]]
    results=[];all_gains=[]
    for seed in m["seeds"]:
        data={}
        for label in m["variants"]:
            folder=a.run/f"{seed}-{label}"
            rows=json.loads((folder/"validation-predictions.json").read_text())
            signature=[(r["id"],r["image"],r["question"],r["type"],r["answer"]) for r in rows]
            assert signature==canonical
            assert len(rows)==16441 and len({r["id"] for r in rows})==16441
            metrics=score(rows)
            recorded=saved[f"{seed}-{label}"]
            assert abs(metrics["oa"]-recorded["validation"]["oa"])<1e-12
            assert abs(metrics["aa"]-recorded["validation"]["aa"])<1e-12
            history=json.loads((folder/"history.json").read_text())
            best=max(history,key=lambda h:h["oa"])
            assert best["epoch"]==recorded["best_epoch"]
            assert best["oa"]==metrics["oa"]
            assert hashlib.sha256((folder/"best.pt").read_bytes()).hexdigest()==recorded["checkpoint_sha256"]
            data[label]=dict(metrics=metrics,correct=np.array([r["prediction"]==r["answer"] for r in rows],dtype=float))
        scenes=np.array([r[1] for r in canonical])
        gains=data["grid8"]["correct"]-data["grid4"]["correct"];all_gains.append(gains)
        base,new=data["grid4"]["metrics"],data["grid8"]["metrics"]
        delta_by={t:100*(new["by_type"][t]-base["by_type"][t]) for t in base["by_type"]}
        results.append(dict(seed=seed,metrics={k:v["metrics"] for k,v in data.items()},
                            oa_gain_pp=100*float(gains.mean()),
                            aa_gain_pp=100*(new["aa"]-base["aa"]),by_type_gain_pp=delta_by,
                            scene_bootstrap_95ci_pp=scene_interval(gains[None,:],scenes),
                            grid4_gain_over_question_only_pp=100*(base["oa"]-data["question_only"]["metrics"]["oa"]),
                            grid8_gain_over_question_only_pp=100*(new["oa"]-data["question_only"]["metrics"]["oa"]),
                            regression_guard_pass=all(v>=-1 for v in delta_by.values()) and new["aa"]-base["aa"]>=-.01))
    ci=scene_interval(np.stack(all_gains),scenes)
    passed=ci[0]>0 and all(r["oa_gain_pp"]>0 and r["regression_guard_pass"] for r in results)
    report=dict(scope="Validation-selected development evidence; not test or unseen acceptance",
                seeds=results,mean_gain_pp=float(np.mean([r["oa_gain_pp"] for r in results])),
                mean_seed_scene_bootstrap_95ci_pp=ci,
                uncertainty_limit="Conditional on validation-selected checkpoints; seeds reported separately; does not remove selection optimism",
                quality_screen_pass=passed,serving_promoted=False,
                decision="Eligible for further predeclared evaluation, not deployment" if passed else "Do not promote grid8 under frozen guardrails",
                manifest_sha256=hashlib.sha256((a.run/"manifest.json").read_bytes()).hexdigest())
    a.out.mkdir(parents=True);(a.out/"comparison.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
