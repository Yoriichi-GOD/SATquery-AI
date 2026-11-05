"""Mask-aware optical similarity diagnostic with held-out visible-feature residuals.

No source is warped or overwritten. AROSICS was reviewed as a future local-shift
alternative; this implementation reuses the existing OpenCV dependency and SIFT approach.
Optical-to-SAR registration is explicitly unavailable, not passed through this estimator.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from research.terrain_exposure.io import read_raster, sha256, save_json


def audit(a, b, valid_a, valid_b, grid_a, grid_b, *, modalities=("optical", "optical"), max_shift_px=1.5):
    result = {"status": "UNAVAILABLE", "physical_registration": "UNVERIFIED", "corrected_raster_created": False,
              "method": "SIFT mutual ratio matches; train-only RANSAC similarity; held-out residuals",
              "modalities": list(modalities), "grid_a": grid_a.describe(), "grid_b": grid_b.describe(),
              "threshold_pixels": max_shift_px, "absolute_geolocation": "NOT_VALIDATED",
              "vertical_datum": "Not inferred from image grids", "resampling": "None; diagnostics only"}
    if modalities != ("optical", "optical"):
        return {**result, "reason": "CROSS_SENSOR_METHOD_NOT_AVAILABLE"}
    if grid_a != grid_b:
        return {**result, "reason": "GRID_OR_RESOLUTION_MISMATCH; explicitly prepare compatible diagnostic grids first"}
    a, b = np.asarray(a, float), np.asarray(b, float)
    va, vb = np.asarray(valid_a, bool), np.asarray(valid_b, bool)
    if a.shape != grid_a.shape or b.shape != grid_b.shape or va.shape != a.shape or vb.shape != b.shape:
        raise ValueError("Registration image/mask dimensions differ")
    va, vb = va & np.isfinite(a), vb & np.isfinite(b)
    result.update(valid_a_fraction=float(va.mean()), valid_b_fraction=float(vb.mean()), common_valid_fraction=float((va & vb).mean()))
    if min(va.sum(), vb.sum()) < 256:
        return {**result, "reason": "INSUFFICIENT_VALID_SUPPORT"}
    import cv2
    cv2.setNumThreads(1)
    cv2.setRNGSeed(42)
    # Erode masks so feature patches do not straddle cloud/NoData boundaries.
    kernel = np.ones((9,9),np.uint8)
    ma = cv2.erode(va.astype("uint8"), kernel, borderType=cv2.BORDER_CONSTANT, borderValue=0)
    mb = cv2.erode(vb.astype("uint8"), kernel, borderType=cv2.BORDER_CONSTANT, borderValue=0)
    values = np.concatenate([a[va], b[vb]])
    lo, hi = np.percentile(values, [1,99])
    if hi-lo < 1e-8:
        return {**result, "reason": "LOW_TEXTURE"}
    def grayscale(image, mask):
        return np.where(mask, np.clip((np.nan_to_num(image)-lo)/(hi-lo)*255,0,255),0).astype("uint8")
    detector = cv2.SIFT_create(nfeatures=3000)
    ka, da = detector.detectAndCompute(grayscale(a, va), ma*255)
    kb, db = detector.detectAndCompute(grayscale(b, vb), mb*255)
    result.update(keypoints_a=len(ka), keypoints_b=len(kb))
    if da is None or db is None:
        return {**result, "reason": "INSUFFICIENT_DISTINCT_FEATURES"}
    matcher = cv2.BFMatcher()
    def ratio_matches(left, right):
        return {m.queryIdx: m.trainIdx for pair in matcher.knnMatch(left,right,k=2) if len(pair)==2
                for m,n in [pair] if m.distance < .7*n.distance}
    forward, backward = ratio_matches(da,db), ratio_matches(db,da)
    matches = sorted((i,j) for i,j in forward.items() if backward.get(j)==i)
    # SIFT can emit multiple scales at one physical point. Do not count those as independent ties.
    unique, seen = [], set()
    for i,j in matches:
        key=tuple(round(v,1) for v in (*ka[i].pt,*kb[j].pt))
        if key not in seen:
            unique.append((i,j));seen.add(key)
    result["matches"] = len(unique)
    if len(unique) < 20:
        return {**result, "reason": "INSUFFICIENT_TRUSTWORTHY_TIE_POINTS"}
    x=np.array([ka[i].pt for i,j in unique],np.float32)
    y=np.array([kb[j].pt for i,j in unique],np.float32)
    # Fixed split before model fitting; hold-out points never select the transformation.
    held=np.arange(len(x))%4==0
    model,inliers=cv2.estimateAffinePartial2D(x[~held],y[~held],method=cv2.RANSAC,
        ransacReprojThreshold=1.5,maxIters=3000,confidence=.99,refineIters=10)
    if model is None or inliers is None or inliers.sum()<10 or inliers.mean()<.5:
        return {**result, "reason": "UNSTABLE_TRANSFORMATION"}
    points=x[~held][inliers.ravel().astype(bool)]
    hull_area=float(cv2.contourArea(cv2.convexHull(points)))
    fraction=hull_area/(a.shape[0]*a.shape[1])
    quadrants=set((int(p[0]>=a.shape[1]/2),int(p[1]>=a.shape[0]/2)) for p in points)
    result.update(training_inliers=int(inliers.sum()), training_matches=int((~held).sum()), held_out_matches=int(held.sum()),
                  inlier_hull_fraction=fraction, inlier_quadrants=len(quadrants), estimated_a_to_b_affine=model.tolist())
    if fraction<.03 or len(quadrants)<3:
        return {**result, "reason": "INSUFFICIENT_SPATIAL_TIE_POINT_DISTRIBUTION"}
    displacement=y[held]-x[held]
    predicted=x[held]@model[:,:2].T+model[:,2]
    residual=y[held]-predicted
    raw=np.linalg.norm(displacement,axis=1)
    post=np.linalg.norm(residual,axis=1)
    metres=np.sqrt((residual[:,0]*grid_a.transform.a)**2+(residual[:,1]*grid_a.transform.e)**2)
    rotation=math.degrees(math.atan2(model[1,0],model[0,0]))
    scale=math.hypot(model[0,0],model[1,0])
    trustworthy=(post<=1.5)
    result.update(pre_correction_displacement_median_px=float(np.median(raw)),
                  pre_correction_displacement_p95_px=float(np.percentile(raw,95)),
                  estimated_translation_xy_px=model[:,2].tolist(), estimated_rotation_deg=rotation,
                  estimated_scale=scale, post_fit_held_out_residual_median_px=float(np.median(post)),
                  post_fit_held_out_residual_p95_px=float(np.percentile(post,95)),
                  post_fit_held_out_residual_median_m=float(np.median(metres)),
                  held_out_within_1_5_px_fraction=float(trustworthy.mean()),
                  tie_points=[{"a_xy":p.tolist(),"b_xy":q.tolist(),"held_out":bool(h)} for p,q,h in zip(x,y,held)])
    if abs(rotation)>5 or not .95<=scale<=1.05 or trustworthy.mean()<.7:
        return {**result,"reason":"TRANSFORMATION_OR_HELD_OUT_RESIDUAL_REJECTED"}
    result.update(status="MISALIGNED" if np.median(raw)>max_shift_px else "PARTIALLY_VERIFIED",
                  physical_registration="RELATIVE_SHARED_VISIBLE_FEATURES_ONLY", reason="NO_AUTOMATIC_CORRECTION",
                  limitations=["Tie points are image correspondences, not surveyed ground control",
                               "Post-fit residuals are diagnostic; no corrected satellite product was generated",
                               "Physical optical/SAR alignment and absolute geolocation remain unverified",
                               "Changed, cloudy or low-texture areas may lack trustworthy matches"])
    return result


def nepal_audit(flood_root, output):
    root=Path(flood_root)
    run=root/"artifacts/runs/event-fe47db331390"
    manifest=json.loads((run/"manifest.json").read_text())
    dates=[manifest["debris"]["pre_date"],manifest["debris"]["post_date"]]
    arrays=[];valids=[];grids=[];sources=[]
    for date in dates:
        p=root/"data/automatic/event-fe47db331390/optical"/date/"default.tif"
        expected=manifest["debris"]["source_hashes"][date]
        if sha256(p)!=expected:
            raise ValueError("Optical source hash mismatch")
        # Band contract comes from the retained seven-band acquisition request:
        # B02, B03, B04, B08, B11, SCL, dataMask. Never infer from TIFF headers alone.
        import rasterio
        request_path=p.parent/"request.json"
        request=json.loads(request_path.read_text())
        if not all(band in json.dumps(request) for band in ["B02","B03","B04","SCL","dataMask"]):
            raise ValueError("Retained optical request does not support band contract")
        with rasterio.open(p) as src:
            if src.count!=7:
                raise ValueError("Unexpected Nepal optical bands")
            data=src.read()
            mask=np.isfinite(data).all(0)&(data[6]==1)&np.isin(data[5],[4,5,6])
        _,_,grid,meta=read_raster(p)
        arrays.append(data[:3].mean(0));valids.append(mask);grids.append(grid)
        sources.append({**meta,"date":date,"request_sha256":sha256(request_path),"sensor":"Sentinel-2 L2A",
                        "quality_mask":"dataMask=1; SCL in 4,5,6; finite all seven bands"})
    result=audit(*arrays,*valids,*grids)
    result.update(population="GENUINE_SAVED_OPTICAL_PAIR",sources=sources,
                  cross_sensor={"status":"UNAVAILABLE","reason":"Optical-to-SAR matching not validated"})
    save_json(output,result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flood-root",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    if Path(args.output).exists():
        raise FileExistsError("Do not overwrite registration evidence")
    result=nepal_audit(args.flood_root,args.output)
    print(json.dumps({k:v for k,v in result.items() if k not in {"tie_points","sources"}},indent=2))


if __name__=="__main__":main()
