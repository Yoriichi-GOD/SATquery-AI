"""Strict metric raster contracts and content-addressed scientific outputs."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from pyproj import CRS


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class Grid:
    shape: tuple[int, int]
    transform: Affine
    crs: str

    def __post_init__(self):
        crs = CRS.from_user_input(self.crs)
        if not crs.is_projected or not crs.axis_info or any(
                axis.unit_name not in ("metre", "meter") for axis in crs.axis_info[:2]):
            raise ValueError("A projected metric CRS is required")
        t = self.transform
        if not np.isfinite(tuple(t)).all() or t.b != 0 or t.d != 0 or t.a <= 0 or t.e >= 0:
            raise ValueError("A finite north-up metric transform is required")
        if len(self.shape) != 2 or min(self.shape) < 1 or np.prod(self.shape) > 1_000_000:
            raise ValueError("Grid must contain 1 to 1,000,000 cells")

    @property
    def area(self):
        return self.transform.a * -self.transform.e

    def centre(self, index):
        r, c = divmod(int(index), self.shape[1])
        return self.transform * (c + 0.5, r + 0.5)

    def describe(self):
        return {"shape": list(self.shape), "transform": list(self.transform)[:6], "crs": self.crs,
                "cell_area_m2": self.area, "cell_size_m": [self.transform.a, -self.transform.e]}


def read_raster(path, band=1):
    with rasterio.open(path) as src:
        if src.crs is None or not 1 <= band <= src.count:
            raise ValueError("Missing CRS or raster band")
        grid = Grid(src.shape, src.transform, src.crs.to_string())
        data = src.read(band)
        valid = (src.read_masks(band) > 0) & np.isfinite(data)
        metadata = {"filename": Path(path).name, "sha256": sha256(path), "grid": grid.describe(),
                    "band": band, "nodata": None if src.nodata is None or not np.isfinite(src.nodata) else src.nodata,
                    "descriptions": list(src.descriptions), "tags": src.tags()}
    return data, valid, grid, metadata


def candidate_raster(path, positives, valid_codes):
    data, valid, grid, metadata = read_raster(path)
    # NoData is not background. Unrecognized classes are rejected, not silently ignored.
    if not np.isin(data[valid], valid_codes).all():
        raise ValueError("Unexpected candidate-mask classes")
    valid &= np.isin(data, valid_codes)
    return np.isin(data, positives) & valid, valid, grid, metadata


def write_raster(path, data, grid, valid=None):
    data = np.asarray(data, dtype="float64")
    if data.shape != grid.shape:
        raise ValueError("Output array/grid mismatch")
    support = np.isfinite(data) if valid is None else np.asarray(valid, bool) & np.isfinite(data)
    with rasterio.open(path, "w", driver="GTiff", height=grid.shape[0], width=grid.shape[1],
                       count=1, dtype="float64", crs=grid.crs, transform=grid.transform,
                       nodata=-9999.0, compress="deflate") as dst:
        dst.write(np.where(support, data, -9999.0), 1)


def resolution_status(cell_m, required_feature_width_m=None):
    if required_feature_width_m is None:
        return {"status": "COARSE_CONTEXT_ONLY", "reason": "No surveyed target scale provided"}
    if not np.isfinite(required_feature_width_m) or required_feature_width_m <= 0:
        raise ValueError("Positive target feature width required")
    # Two cells is a declared minimum sampling gate, not proof of hydrological adequacy.
    return {"status": "INSUFFICIENT_RESOLUTION" if 2 * cell_m > required_feature_width_m else "SCALE_GATE_PASSED",
            "required_feature_width_m": required_feature_width_m, "minimum_cells_across_feature": 2,
            "warning": "Sampling gate alone does not validate drains, elevations or flow."}
