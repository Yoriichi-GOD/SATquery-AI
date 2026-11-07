"""Post-freeze agreement against UNOSAT and EMSR event-reference layers.

Optional development dependency: Fiona 1.10.1 to read the UNOSAT FileGDB.
The UNOSAT product is preliminary and not field-validated ground truth.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import platform

import fiona
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize
from shapely.geometry import shape
from shapely.ops import transform

from floodlab.evaluate import binary_metrics
from floodlab.pipeline import digest

ROOT = Path(__file__).resolve().parents[1]
UNOSAT_GDB = ROOT / "evaluation_only/references/FL20260826NPL.gdb"
UNOSAT_ARCHIVE = ROOT / "evaluation_only/references/FL20260826NPL.gdb.zip"
UNOSAT_EXTENT_LAYER = "UNOSAT_Multisensors_20260826_20260828_AnalysisExtent"
UNOSAT_FLOOD_LAYER = "UNOSAT_Multisensor_20260826_20260828_FloodExtent"
AREAS = {
    "syapru_besi": {
        "run": "nepal-syapru-004",
        "gpkg": ROOT / "evaluation_only/emsr/EMSR927_AOI01_GRA_PRODUCT_v1.gpkg",
        "version": "v1",
    },
    "timure": {
        "run": "event-02163045d752",
        "gpkg": ROOT / "evaluation_only/emsr/EMSR927_AOI02_GRA_PRODUCT_v2.gpkg",
        "version": "v2",
    },
}
OUTPUT = ROOT / "evaluation_only/results/unosat-reference-agreement.json"


def read_projected(path: Path, layer: str, target_crs):
    with fiona.open(path, layer=layer) as src:
        source_crs = src.crs_wkt or src.crs
        if not source_crs:
            raise ValueError(f"Missing CRS: {path.name}:{layer}")
        projector = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        geoms, props = [], []
        for feature in src:
            if feature["geometry"]:
                geoms.append(transform(projector.transform, shape(feature["geometry"])))
                props.append(dict(feature["properties"]))
        return geoms, props


def burn(geoms, shape_hw, affine):
    if not geoms:
        raise ValueError("Reference layer has no usable geometries")
    return rasterize(
        ((geom, 1) for geom in geoms),
        out_shape=shape_hw,
        transform=affine,
        fill=0,
        dtype="uint8",
        all_touched=False,
    ).astype(bool)


def grid(run_dir):
    with rasterio.open(run_dir / "prediction.tif") as ds:
        return ds.crs, ds.shape, ds.transform


def verify_and_mark_frozen(run_dir: Path):
    freeze_path = run_dir / "freeze.json"
    frozen = json.loads(freeze_path.read_text(encoding="utf-8"))
    for filename, expected in frozen["files"].items():
        if digest(run_dir / filename) != expected:
            raise ValueError(f"Frozen output hash mismatch: {run_dir.name}/{filename}")
    if not frozen.get("evaluation_started"):
        frozen["evaluation_started"] = True
        temp = freeze_path.with_suffix(".tmp")
        temp.write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
        temp.replace(freeze_path)
    return frozen


def score_area(name, cfg, frozen, analysis_geoms, flood_geoms):
    run_dir = ROOT / "artifacts/runs" / cfg["run"]
    target_crs, shape_hw, affine = grid(run_dir)
    aoi_path, version = cfg["gpkg"], cfg["version"]
    aoi_geoms, _ = read_projected(aoi_path, f"areaOfInterestA_{version}", target_crs)
    event_geoms, event_props = read_projected(aoi_path, f"observedEventA_{version}", target_crs)
    footprint_geoms, footprint_props = read_projected(aoi_path, f"imageFootprintA_{version}", target_crs)
    post_footprints = [g for g, p in zip(footprint_geoms, footprint_props) if p.get("or_src_id") == 2]
    if not post_footprints:
        raise ValueError(f"No post-event EMSR footprint for {name}")

    aoi_mask = burn(aoi_geoms, shape_hw, affine)
    analysis_mask = burn(analysis_geoms, shape_hw, affine)
    flood_mask = burn(flood_geoms, shape_hw, affine)
    landslide_mask = burn(event_geoms, shape_hw, affine)
    post_footprint_mask = burn(post_footprints, shape_hw, affine)
    with rasterio.open(run_dir / "prediction.tif") as water_ds, rasterio.open(run_dir / "debris-candidates.tif") as debris_ds:
        if (water_ds.crs != debris_ds.crs or water_ds.transform != debris_ds.transform
                or water_ds.width != debris_ds.width or water_ds.height != debris_ds.height):
            raise ValueError(f"Prediction grids differ: {name}")
        water, debris = water_ds.read(1), debris_ds.read(1)
    if water.shape != aoi_mask.shape:
        raise ValueError(f"Reference grid does not match {name}")

    water_valid = (water != 255) & aoi_mask & analysis_mask
    debris_valid = (debris != 255) & aoi_mask & post_footprint_mask
    water_metrics = binary_metrics(water == 2, flood_mask, water_valid)
    debris_metrics = binary_metrics(debris == 1, landslide_mask, debris_valid)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    return {
        "aoi": name,
        "run": cfg["run"],
        "event_date": manifest.get("event_time"),
        "sentinel1_pre": manifest.get("pre", {}).get("datetime"),
        "sentinel1_post": manifest.get("post", {}).get("datetime"),
        "fixed_rule": manifest.get("analysis"),
        "freeze_hashes_verified": True,
        "evaluation_started_marked_in_freeze": True,
        "water_prediction_sha256": frozen["files"]["prediction.tif"],
        "debris_prediction_sha256": frozen["files"]["debris-candidates.tif"],
        "emsr_reference_sha256": digest(aoi_path),
        "water_comparison": {
            "reference_layer": UNOSAT_FLOOD_LAYER,
            "reference_positive_pixels": int((flood_mask & water_valid).sum()),
            "candidate_positive_pixels": int(((water == 2) & water_valid).sum()),
            "valid_pixels": int(water_valid.sum()),
            "aoi_pixels": int(aoi_mask.sum()),
            "valid_coverage_percent_of_aoi": 100.0 * int(water_valid.sum()) / max(1, int(aoi_mask.sum())),
            **water_metrics,
        },
        "debris_proxy_diagnostic": {
            "reference_layer": f"observedEventA_{version}",
            "reference_class": "6-Mass Movement / Landslide",
            "prediction_class": "vegetation-to-bare plus SAR-change candidates; not a debris classifier",
            "valid_pixels": int(debris_valid.sum()),
            "aoi_pixels": int(aoi_mask.sum()),
            **debris_metrics,
            "interpretation": "Class-mismatched post-freeze agreement only; not debris accuracy.",
        },
    }


def pooled(metric_name, areas):
    keys = ("tp", "fp", "fn", "tn", "valid_pixels")
    counts = {key: sum(area[metric_name].get(key, 0) or 0 for area in areas) for key in keys}
    tp, fp, fn, tn = (counts[k] for k in ("tp", "fp", "fn", "tn"))
    ratio = lambda a, b: a / b if b else None
    return {
        "pooled_disjoint_aoi_counts": counts,
        "metrics": {
            "iou": ratio(tp, tp + fp + fn),
            "f1": ratio(2 * tp, 2 * tp + fp + fn),
            "precision": ratio(tp, tp + fp),
            "recall": ratio(tp, tp + fn),
        },
    }


def main():
    if OUTPUT.exists():
        raise FileExistsError(f"Preserving existing evaluation result: {OUTPUT}")
    if not UNOSAT_GDB.exists() or not UNOSAT_ARCHIVE.exists():
        raise FileNotFoundError("UNOSAT evaluation-only reference is incomplete")

    # Verify all frozen outputs and lock each run for evaluation before opening reference layers.
    frozen = {
        name: verify_and_mark_frozen(ROOT / "artifacts/runs" / cfg["run"])
        for name, cfg in AREAS.items()
    }
    target_crs, _, _ = grid(ROOT / "artifacts/runs/nepal-syapru-004")
    with fiona.open(UNOSAT_GDB, layer=UNOSAT_EXTENT_LAYER) as src:
        extent_crs = src.crs_wkt or src.crs
        extent_source = [shape(f["geometry"]) for f in src if f["geometry"]]
    with fiona.open(UNOSAT_GDB, layer=UNOSAT_FLOOD_LAYER) as src:
        flood_crs = src.crs_wkt or src.crs
        flood_features = [f for f in src if f["geometry"]]
    extent_projector = Transformer.from_crs(extent_crs, target_crs, always_xy=True)
    flood_projector = Transformer.from_crs(flood_crs, target_crs, always_xy=True)
    extent_geoms = [transform(extent_projector.transform, g) for g in extent_source]
    flood_geoms = [transform(flood_projector.transform, shape(f["geometry"])) for f in flood_features]
    field_validation_values = sorted({str(f["properties"].get("FieldValidation")) for f in flood_features})

    areas = [
        score_area(name, cfg, frozen[name], extent_geoms, flood_geoms)
        for name, cfg in AREAS.items()
    ]
    archive_hash = digest(UNOSAT_ARCHIVE)
    result = {
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Post-freeze external map agreement; not field-validated ground truth or event-generalization accuracy.",
        "reference": {
            "organization": "United Nations Satellite Centre (UNOSAT)",
            "product": "4259 / FL20260826NPL",
            "url": "https://unosat.org/products/4259/",
            "archive_url": "https://unosat.org/static/unosat_filesystem/4259/FL20260826NPL.gdb.zip",
            "archive_sha256": archive_hash,
            "flood_layer": UNOSAT_FLOOD_LAYER,
            "analysis_extent_layer": UNOSAT_EXTENT_LAYER,
            "field_validation_values": field_validation_values,
            "source_assessment": "Preliminary satellite-derived mudflow/rockflow and flood impact mapping; not field validated.",
            "masking": "Official AOI polygon AND UNOSAT analysis extent AND valid prediction pixels; 10 m grid; pixel-centre rasterization.",
        },
        "aois": areas,
        "pooled_disjoint_aoi_counts": {
            "water_comparison": pooled("water_comparison", areas),
            "debris_proxy_diagnostic": pooled("debris_proxy_diagnostic", areas),
        },
        "limitations": [
            "One event and two nearby AOIs; this is not geographic or event-generalization evidence.",
            "UNOSAT describes its product as preliminary and not field-validated; agreement is not ground-truth accuracy.",
            "FloodExtent is an external mapped event extent, not a class-pure water-only label; event-scale flow/mudflow may be included.",
            "Different sensors, acquisition times, mapping method, resolution and boundaries can create disagreement.",
            "Debris proxy is compared with EMSR landslide polygons only as a class-mismatched diagnostic; debris accuracy remains unvalidated.",
            "The analysis mask excludes invalid predictions and areas outside the reference product coverage.",
        ],
        "runtime": {"python": platform.python_version(), "fiona": fiona.__version__, "rasterio": rasterio.__version__},
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
