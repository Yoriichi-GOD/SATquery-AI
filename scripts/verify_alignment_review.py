"""Close preprocessing audit without inventing correspondence measurements."""
import hashlib,json,shutil
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds,Window
R=Path("/mnt/c/Users/nrgen/.codex/scratch/SATquery AI")
P=Path("/root/satquery/acquisition/s1s2-water-7-v2")
E=R/".runtime/alignment-20261020"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((E/"manifest.json").read_text())
for name,want in manifest["inputs"].items():assert sha(P/"crop"/name)==want
with rasterio.open(P/"crop/optical-13band.tif") as ds:
    optical=ds.read();bounds=ds.bounds;crs=ds.crs
checks={}
for index,band in [(1,"B02"),(2,"B03"),(3,"B04"),(7,"B08")]:
    with rasterio.open(next(P.glob("*_"+band+".jp2"))) as ds:
        assert ds.crs==crs
        w=from_bounds(*bounds,transform=ds.transform)
        assert np.allclose([w.col_off,w.row_off,w.width,w.height],np.round([w.col_off,w.row_off,w.width,w.height]))
        raw=ds.read(1,window=w.round_offsets().round_lengths()).astype("float32")
        raw[raw==0]=np.nan
    np.testing.assert_allclose(raw,optical[index],atol=0,rtol=0,equal_nan=True)
    checks[band]="native 10m crop equals prepared band exactly"
with rasterio.open(P/"sentinel12_s1_7_img.tif") as ds:raw=ds.read(window=Window(5120,5120,512,512)).astype("float32")/100
with rasterio.open(P/"crop/sar-db.tif") as ds:prepared=ds.read()
np.testing.assert_array_equal(raw,prepared)
checks["SAR"]="prepared dB equals original scaled values divided by 100 exactly"
for sensor in ("s1","s2"):
    with rasterio.open(P/f"sentinel12_{sensor}_7_valid.tif") as ds:raw=ds.read(1,window=Window(5120,5120,512,512))
    with rasterio.open(P/"crop"/f"{sensor}-reference-valid.tif") as ds:prepared=ds.read(1)
    np.testing.assert_array_equal(raw,prepared)
    assert set(np.unique(raw))<={0,1}
    checks[sensor+"_valid"]="exact mask crop; binary encoding preserved"
reasons=[
 "Field boundaries visible optically; no unambiguous stable corner correspondence in SAR.",
 "Land-cover patches and isolated scatterers lack a unique shared ground point.",
 "Distinctive dark feature is plausibly water; excluded as a stable-landmark control.",
 "Field geometry visible optically but SAR correspondence cannot be localized reliably.",
 "Distinctive shared dark shape is plausibly water; nearby bright scatterer is not a verified ground point.",
 "Optical field intersections do not yield a unique SAR point at this resolution."
]
review={"reviewer":"assistant visual diagnostic; not independent human adjudication",
 "regions":[{"region":i+1,"origin_col_row":origin,"accepted":False,"reason":reason,
             "optical_point":None,"sar_point":None} for i,(origin,reason) in enumerate(zip(manifest["regions"],reasons))],
 "accepted_landmarks":0,"required_landmarks":6,"rmse_m":None,"median_m":None,"p95_m":None,
 "gate":"NOT_ESTABLISHED","interpretation":"Insufficient reliable correspondences, not proof of misregistration",
 "next":"Independent reviewer to identify six distributed static ground points, or declare this pilot unsuitable for alignment validation. Do not substitute water boundaries or unvalidated correlation peaks.",
 "acceptance_inference":"not run because prerequisite is unresolved"}
(E/"landmark-review.json").write_text(json.dumps(review,indent=2))
freeze=json.loads((R/"docs/EVALUATION_FREEZE_20261020.json").read_text())
for name,want in freeze["files_sha256"].items():assert sha(R/name)==want
stats=json.loads((E/"preprocessing.json").read_text())
text=f"""# Pilot alignment and preprocessing review - 2026-10-20

## Decision

Preprocessing checks pass for the acquired pilot. Physical alignment is **NOT ESTABLISHED**. Six distributed regions were visually reviewed; zero stable control-point pairs were accepted. Median, p95 and RMSE remain null. This is insufficient evidence, not proof that the pair is misregistered.

The conditional next step (freeze an acceptance sample and run three modality comparisons) was not triggered. No model inference, scoring, training, thresholds or serving changes.

## Direct checks

- Native 10-metre B02, B03, B04 and B08 crops exactly equal the prepared optical bands; this independently checks coordinate/window and band placement.
- Prepared SAR exactly equals stored source values divided by 100.
- Both validity masks exactly equal the original source crops, preserving binary encoding.
- Original input hashes and all 22 frozen reference files remain unchanged.
- SAR clipping fractions under the current preprocessing limits: {stats["sar"]}.
- Optical fraction above the current upper clipping limit: {stats["optical_clip_fraction"]}.
- Lower-resolution optical bands were bilinearly resampled. This preserves the declared workflow but is not evidence that all source-dataset preprocessing matches the training distribution.

## Visual review

Regions 1, 2, 4 and 6 contain optically visible field geometry but insufficiently unique SAR ground-point correspondences. Regions 3 and 5 contain distinctive dark features plausibly associated with water; these were excluded under the static-ground control rule. Bright SAR returns were not assumed to be building centres.

The six regions cover top and bottom rows at left, middle and right positions. Panels include original RGB, raw VV and a display-only median-filtered view; the extra display filter never changes inference inputs. Review is by the assistant, not independent human adjudication. No points or warp were fitted.

## Source preprocessing

The [authors' SNAP recipe](https://github.com/MWieland/s1s2_water/blob/main/prepare/preproc_s1_snap.xml) specifies orbit correction, thermal-noise removal, sigma-band calibration, 3x3 median filtering, external-DEM terrain correction at 10 m with bilinear interpolation, dB conversion and reprojection. A hash-pinned copy is saved with this review. The image is already preprocessed: applying another filter to inference data would be an unregistered change.

Band/unit compatibility is verified; full equivalence to Sen1Floods11 processing has not been established. Provider cloud QA is automated; dataset validity masks combine invalid causes and are not independent cloud-only truth.

## Required evidence to advance

Obtain at least six spatially distributed, uniquely corresponding static ground landmarks, with source hashes, pixel coordinates, projected metre coordinates, uncertainty and reviewer identity. Keep them independent of any warp fitting. If this scene cannot supply those controls, mark it unsuitable for this alignment check and select another development pilot using an explicit metadata/feature criterion. Do not change acceptance selection based on accuracy.

There is no justified residual cutoff in the current protocol. Before accepting landmark measurements, record a task-resolution-based tolerance and localization uncertainty rather than choosing a cutoff after seeing residuals.

## Artifacts and verification

`.runtime/alignment-20261020/manifest.json`, `landmark-review.json`, `preprocessing.json`, `checks.json`, `regions-1.png`, `regions-2.png`.

The panel script initially encountered a missing optional SciPy dependency before writing outputs; its display filter was implemented with existing NumPy instead. No packages were installed. Real-pixel equality and source-preservation assertions passed. These checks establish only the properties listed above.
"""
(R/"docs/ALIGNMENT_REVIEW_20261020.md").write_text(text,encoding="utf-8")
checks.update(frozen_reference_files=22,input_hashes_unchanged=True,alignment_gate="NOT_ESTABLISHED",model_inference=False,
 source_recipe_sha256=sha(E/"preproc_s1_snap.xml"),review_sha256=sha(E/"landmark-review.json"))
(E/"checks.json").write_text(json.dumps(checks,indent=2))
shutil.copyfile(Path(__file__).parent/"inspect_alignment.py",R/"scripts/inspect_alignment.py")
shutil.copyfile(Path(__file__),R/"scripts/verify_alignment_review.py")
print(json.dumps(checks,indent=2))
