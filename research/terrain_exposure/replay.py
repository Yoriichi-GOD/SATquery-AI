"""Read-only genuine saved-data replay. Reference labels are never opened here."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import time

import numpy as np
import rasterio
from rasterio.transform import array_bounds
from rasterio.warp import reproject, Resampling
from affine import Affine
from shapely.geometry import shape

from .graph import Observation, Receptor, build_graph, export_graph
from .hydrology import derive
from .io import Grid, read_raster, candidate_raster, write_raster, sha256, canonical_hash, save_json


def metric_dem(source, target_grid, resolution, buffer_m):
    left, bottom, right, top = array_bounds(*target_grid.shape, target_grid.transform)
    left, bottom = math.floor((left-buffer_m)/resolution)*resolution, math.floor((bottom-buffer_m)/resolution)*resolution
    right, top = math.ceil((right+buffer_m)/resolution)*resolution, math.ceil((top+buffer_m)/resolution)*resolution
    grid = Grid((round((top-bottom)/resolution), round((right-left)/resolution)),
                Affine(resolution, 0, left, 0, -resolution, top), target_grid.crs)
    values = np.full(grid.shape, np.nan, dtype="float64")
    with rasterio.open(source) as src:
        if src.crs is None or src.count != 1 or src.width*src.height > 2_000_000:
            raise ValueError("Unexpected retained DEM source")
        native = src.read(1, masked=True).astype("float64").filled(np.nan)
        reproject(native, values, src_transform=src.transform, src_crs=src.crs,
                  dst_transform=grid.transform, dst_crs=grid.crs, src_nodata=np.nan,
                  dst_nodata=np.nan, resampling=Resampling.bilinear)
    return values, np.isfinite(values), grid


def verify_freeze(run):
    frozen = json.loads((run/"freeze.json").read_text())
    for name, expected in frozen["files"].items():
        if Path(name).name != name or sha256(run/name) != expected:
            raise ValueError("Frozen Nepal artifact mismatch: " + name)
    return frozen


def load_nepal(flood_root, terrain_source, config):
    root = Path(flood_root)
    run = root/"artifacts/runs"/config["run_id"]
    frozen = verify_freeze(run)
    if sha256(terrain_source) != config["terrain_source_sha256"]:
        raise ValueError("Terrain source hash does not match declared public example")
    manifest = json.loads((run/"manifest.json").read_text())
    if manifest.get("synthetic") is not False or manifest["event_time"] != config["event_time"]:
        raise ValueError("Wrong saved event or synthetic data")
    observations = []
    for layer, filename, times, method in [
        ("water", "prediction.tif", [manifest["pre"]["datetime"], manifest["post"]["datetime"]], "Frozen VV threshold and temporal drop heuristic"),
        ("debris", "debris-candidates.tif", [manifest["debris"]["pre_date"], manifest["debris"]["post_date"]], manifest["debris"]["method"])]:
        candidate, valid, grid, provenance = candidate_raster(run/filename, config[layer]["positive_codes"], config[layer]["valid_codes"])
        provenance.update(dataset="Retained Sentinel observations / existing Flood Lab candidate mask",
                          frozen_artifact_sha256=frozen["files"][filename], license="Contains modified Copernicus Sentinel data 2026")
        observations.append(Observation(layer, candidate, valid, grid, provenance, times, method))
    if observations[0].grid != observations[1].grid:
        raise ValueError("Water/debris native grids differ; do not silently align them")
    collection = json.loads((run/"layers.geojson").read_text())
    provenance = {"filename": "layers.geojson", "sha256": sha256(run/"layers.geojson"),
                  "dataset": "Historical OpenStreetMap", "license": "ODbL", "url": "https://www.openstreetmap.org/copyright"}
    receptors = []
    for feature in collection["features"]:
        kind = feature["properties"].get("kind")
        if kind not in {"building", "road", "bridge", "settlement", "infrastructure"}:
            continue
        receptors.append(Receptor(str(feature["id"]), kind, shape(feature["geometry"]), "EPSG:4326",
                                  provenance, feature["properties"].get("snapshot") or manifest["osm_snapshot"]))
    z, valid, dem_grid = metric_dem(terrain_source, observations[0].grid,
                                   config["dem_resolution_m"], config["dem_buffer_m"])
    dem_provenance = {"sha256": sha256(terrain_source), "dataset": config.get("terrain_product", "Copernicus GLO-90 DSM / AWS 2021 release"),
                      "source_url": config["terrain_source_url"], "license": config["terrain_license"],
                      "vertical_datum": config["vertical_datum"], "observation_time": "Historical DSM; exact acquisition dates unavailable",
                      "resampling": f"Bilinear to metric {config['dem_resolution_m']}m grid; NoData retained", "buffer_m": config["dem_buffer_m"]}
    return z, valid, dem_grid, observations, receptors, dem_provenance


def environment():
    packages = {}
    for name in ["numpy", "rasterio", "pyproj", "shapely", "fiona", "opencv-python-headless", "matplotlib"]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "NOT_INSTALLED"
    return {"python": platform.python_version(), "platform": platform.platform(),
            "processor": platform.processor(), "packages": packages, "device": "CPU", "training": False}


def replay(flood_root, terrain_source, config_path, output):
    started = time.perf_counter()
    config = json.loads(Path(config_path).read_text())
    if Path(output).exists():
        raise FileExistsError("Choose a new immutable output directory")
    z, valid, grid, observations, receptors, provenance = load_nepal(flood_root, terrain_source, config)
    hydro = derive(z, valid, grid, config["stream_area_m2"], config["conditioning"])
    graph = build_graph(hydro, observations, receptors, provenance, target_width_m=config["required_feature_width_m"])
    graph = export_graph(graph, hydro, output)
    output = Path(output)
    write_raster(output/"original_dem.tif", z, grid, valid)
    save_json(output/"configuration.json", config)
    summary = {"schema_version": graph["schema_version"], "population": "GENUINE_SAVED_OBSERVATION_REPLAY",
               "case_id": config["case_id"], "source_run_id": config["run_id"], "status": "COMPLETE_REPLAY_NOT_SCIENTIFIC_VALIDATION",
               "hydrology": hydro.summary, "graph": graph["summary"], "observations": graph["observations"],
               "resolution": graph["resolution"], "limitations": graph["limitations"]+config["limitations"],
               "configuration_sha256": canonical_hash(config), "graph_content_sha256": graph["content_sha256"],
               "seconds": time.perf_counter()-started, "environment": environment(),
               "independent_reference_used": False, "recorded_utc": datetime.now(timezone.utc).isoformat()}
    save_json(output/"summary.json", summary)
    save_json(output/"manifest.json", {"schema_version": graph["schema_version"], "state": "complete",
        "files": {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()},
        "config_sha256": canonical_hash(config), "original_sources": {"terrain": provenance,
            **{o.layer: o.provenance for o in observations}, "infrastructure": receptors[0].provenance}})
    return summary


def verify_output(output):
    root = Path(output)
    manifest = json.loads((root/"manifest.json").read_text())
    if manifest.get("state") != "complete":
        raise ValueError("Run incomplete")
    for name, expected in manifest["files"].items():
        if Path(name).name != name or sha256(root/name) != expected:
            raise ValueError("Output artifact hash mismatch: " + name)
    graph = json.loads((root/"graph.json").read_text())
    identity = graph.pop("content_sha256")
    if canonical_hash(graph) != identity:
        raise ValueError("Graph canonical hash mismatch")
    graph["content_sha256"] = identity
    return manifest, graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--flood-root", required=True)
    parser.add_argument("--terrain-source", required=True)
    parser.add_argument("--config", default="research/cases/nepal.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(replay(args.flood_root, args.terrain_source, args.config, args.output), indent=2))


if __name__ == "__main__":
    main()
