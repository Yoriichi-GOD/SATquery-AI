"""Measure existing validation input metadata; never infer cloud/physical alignment."""
import argparse,csv,hashlib,json
from datetime import datetime
from pathlib import Path
import numpy as np
import rasterio

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def landmark_residuals(points):
    """Independent corresponding points in the SAME projected metre CRS."""
    a=np.asarray(points,dtype=float)
    if a.ndim!=2 or a.shape[1]!=4 or len(a)<3 or not np.isfinite(a).all():
        raise ValueError("At least three finite [optical_x,y,sar_x,y] metre points required")
    delta=a[:,2:]-a[:,:2]
    norms=np.linalg.norm(delta,axis=1)
    return {"count":len(a),"median_m":float(np.median(norms)),
            "p95_m":float(np.percentile(norms,95)),"rmse_m":float(np.sqrt(np.mean(norms**2))),
            "mean_dx_m":float(delta[:,0].mean()),"mean_dy_m":float(delta[:,1].mean())}

def grid_error(a,b,width,height):
    points=[(0,0),(width,0),(0,height),(width,height)]
    return max(float(np.linalg.norm(np.asarray((~a)*(b*p))-np.asarray(p))) for p in points)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args();d=args.data
    args.out.mkdir(parents=True,exist_ok=False)
    manifest={"version":1,"scope":"Existing validation input quality only; no scores, training or fresh acceptance",
      "script_sha256":sha(Path(__file__)),"metadata_sha256":sha(d/"event-metadata.geojson"),
      "split_sha256":{s:sha(d/(s+".csv")) for s in ("train","valid","test","bolivia")},
      "rules":{"cloud":"Unknown without a verified mask; finite or bright does not mean clear or cloudy",
       "alignment":"Grid corner discrepancy in pixels is metadata only; physical residual requires independent landmarks",
       "dates":"Absolute whole-day gap from event metadata; not per-chip acquisition authentication",
       "freshness":"All local split members exposed by training, selection or historical evaluation",
       "coverage":"Sensor finite fractions are input availability only, not clear-sky or scored coverage"}}
    (args.out/"manifest.json").write_text(json.dumps(manifest,indent=2))
    events={f["properties"]["location"]:f["properties"] for f in json.loads((d/"event-metadata.geojson").read_text())["features"]}
    splits={s:[r[0].removesuffix("_S1Hand.tif") for r in csv.reader((d/(s+".csv")).open())] for s in manifest["split_sha256"]}
    rows=[]
    for name in splits["valid"]:
        event=name.rsplit("_",1)[0];m=events.get(event)
        arrays=[];meta=[];hashes={}
        for layer in ("S1Hand","S2Hand"):
            path=d/layer/(name+"_"+layer+".tif");hashes[layer]=sha(path)
            with rasterio.open(path) as ds:
                arrays.append(np.isfinite(ds.read(masked=True).astype("float32").filled(np.nan)).all(0))
                meta.append((ds.transform,ds.crs,ds.width,ds.height,ds.count))
        same=meta[0][1:4]==meta[1][1:4]
        gap=abs((datetime.strptime(m["s1_date"],"%Y/%m/%d")-datetime.strptime(m["s2_date"],"%Y/%m/%d")).days) if m else None
        rows.append(dict(sample=name,event=event,s1_date=m["s1_date"] if m else None,s2_date=m["s2_date"] if m else None,
          gap_days=gap,s1_finite_fraction=float(arrays[0].mean()),s2_finite_fraction=float(arrays[1].mean()),
          shared_finite_fraction=float((arrays[0]&arrays[1]).mean()) if same else None,
          same_grid_crs_shape=same,grid_corner_error_pixels=grid_error(meta[0][0],meta[1][0],meta[0][2],meta[0][3]) if same else None,
          optical_bands=meta[1][4],cloud_fraction=None,physical_alignment_rmse_m=None,sha256=hashes))
    split_events={s:sorted(set(n.rsplit("_",1)[0] for n in names)) for s,names in splits.items()}
    result={"rows":rows,"split_counts":{s:len(n) for s,n in splits.items()},"split_events":split_events,
      "train_validation_event_overlap":sorted(set(split_events["train"])&set(split_events["valid"])),
      "fresh_local_candidates":0,"freshness_scope":"Only enumerated Sen1Floods11 local splits; not every disk or external dataset",
      "event_gaps_days":{r["event"]:r["gap_days"] for r in rows},
      "unmatched_metadata_events":sorted(set(r["event"] for r in rows if r["gap_days"] is None)),
      "cloud_measured_count":0,"physical_alignment_measured_count":0}
    (args.out/"measurements.json").write_text(json.dumps(result,indent=2))
    with (args.out/"review-queue.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["sample","event","gap_days","cloud_mask_path","cloud_mask_provenance","landmarks_path","projected_crs","reviewer","status"])
        writer.writeheader()
        for r in rows:writer.writerow({**{k:r[k] for k in ("sample","event","gap_days")},"status":"needs_quality_evidence"})
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},indent=2))

if __name__=="__main__":main()
