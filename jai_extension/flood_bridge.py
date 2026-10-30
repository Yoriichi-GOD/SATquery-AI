"""Bounded, read-only access to a configured loopback Flood Lab service."""
from __future__ import annotations

import csv
import hashlib
import io
import ipaddress
import json
import math
import re
from urllib.parse import urlsplit

import requests

RUN_ID = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
MIME = {
    "result.json": "application/json", "manifest.json": "application/json",
    "freeze.json": "application/json", "connectivity.json": "application/json",
    "sensitivity.json": "application/json", "graph.json": "application/json",
    "topology-audit.json": "application/json", "layers.geojson": "application/geo+json",
    "exposure.csv": "text/csv", "debris-exposure.csv": "text/csv",
    "prediction.tif": "image/tiff", "debris-candidates.tif": "image/tiff",
    "pre.png": "image/png", "post.png": "image/png",
    "report-en.html": "text/html", "report-ne.html": "text/html",
}
MAX_FILE = 16 * 1024 * 1024
MAX_JSON = 2 * 1024 * 1024


class BridgeError(Exception):
    def __init__(self, status: int, message: str):
        self.status, self.message = status, message
        super().__init__(message)


def parse_json(raw: bytes):
    try:
        return json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError):
        raise BridgeError(422, "Invalid upstream JSON metadata") from None


def check_id(run_id: str):
    if not RUN_ID.fullmatch(run_id):
        raise BridgeError(404, "Unknown saved run")


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def normalize(result):
    if not isinstance(result, dict):
        raise BridgeError(422, "Invalid run metadata")
    run_id = result.get("run_id", "")
    if not isinstance(run_id, str):
        raise BridgeError(422, "Invalid run identifier")
    check_id(run_id)
    if type(result.get("synthetic")) is not bool or not isinstance(result.get("summary"), dict):
        raise BridgeError(422, "Run lacks population or summary metadata")
    summary = {}
    for key in ("valid_pixels", "total_pixels", "new_water_pixels", "new_water_m2",
                "water_in_both_pixels", "mapped_buildings", "exposed_buildings",
                "exposed_road_m", "exposed_bridge_features", "debris_candidate_m2"):
        value = result["summary"].get(key)
        if value is not None:
            if not numeric(value):
                raise BridgeError(422, "Invalid numerical summary")
            summary[key] = value
    assessed = result["summary"].get("connectivity_assessed") is True
    summary["connectivity_status"] = "ASSESSED_WITH_ASSUMPTIONS" if assessed else "NOT_ASSESSED"
    if assessed:
        value = result["summary"].get("potentially_cut_off")
        if numeric(value):
            summary["potentially_cut_off"] = value
    return {
        "id": run_id, "event_name": str(result.get("event_name", run_id))[:300],
        "population": "SYNTHETIC_SOFTWARE_TEST" if result["synthetic"] else "FROZEN_REAL_OBSERVATION",
        "state": "SAVED", "summary": summary,
        "limitations": [v[:1500] for v in result.get("limitations", []) if isinstance(v, str)][:25],
    }


class FloodBridge:
    def __init__(self, upstream="http://127.0.0.1:8770", session=None):
        parsed = urlsplit(upstream)
        try:
            is_loopback = ipaddress.ip_address(parsed.hostname or "").is_loopback
            port = parsed.port
        except ValueError:
            is_loopback, port = False, None
        if (parsed.scheme != "http" or not is_loopback or not port or parsed.username or
                parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
            raise ValueError("Flood upstream must be a literal loopback HTTP origin with a port")
        self.upstream = upstream.rstrip("/")
        self.session = session or requests.Session()
        self.session.trust_env = False

    def read(self, path, cap=MAX_JSON):
        try:
            with self.session.get(self.upstream + path, timeout=(2, 8), stream=True,
                                  headers={"Accept-Encoding": "identity"},
                                  allow_redirects=False) as response:
                if response.status_code == 404:
                    raise BridgeError(404, "Saved run or artifact not found")
                if response.status_code != 200:
                    raise BridgeError(503, "Flood Lab is unavailable")
                if response.headers.get("content-encoding", "identity") != "identity":
                    raise BridgeError(422, "Compressed upstream responses are not accepted")
                declared = response.headers.get("content-length")
                if declared and (not declared.isdigit() or int(declared) > cap):
                    raise BridgeError(413, "Artifact exceeds transfer limit")
                chunks, size = [], 0
                for block in response.iter_content(65536):
                    size += len(block)
                    if size > cap:
                        raise BridgeError(413, "Artifact exceeds transfer limit")
                    chunks.append(block)
                return b"".join(chunks)
        except requests.RequestException:
            raise BridgeError(503, "Flood Lab is unavailable; start the local service on port 8770") from None

    def health(self):
        try:
            payload = parse_json(self.read("/api/health"))
            if not isinstance(payload, dict) or payload.get("service") != "satquery-flood-lab":
                raise BridgeError(422, "Unexpected upstream service")
            return {"available": True, "service": "satquery-flood-lab", "mode": "read-only saved evidence"}
        except BridgeError as error:
            if error.status != 503:
                raise
            return {"available": False, "service": "satquery-flood-lab", "detail": error.message}

    def runs(self):
        payload = parse_json(self.read("/api/runs"))
        if not isinstance(payload, list) or len(payload) > 200:
            raise BridgeError(422, "Invalid or excessive saved-run listing")
        items, rejected = [], 0
        seen = set()
        for result in payload:
            try:
                item = normalize(result)
                if item["id"] in seen:
                    raise BridgeError(422, "Duplicate run identifier")
                seen.add(item["id"])
                item["integrity"] = "NOT_YET_CHECKED"
                items.append(item)
            except BridgeError:
                rejected += 1
        return {"runs": items, "rejected_metadata": rejected, "mode": "SAVED"}

    def freeze(self, run_id):
        check_id(run_id)
        raw = self.read(f"/runs/{run_id}/freeze.json")
        payload = parse_json(raw)
        files = payload.get("files") if isinstance(payload, dict) else None
        if (not isinstance(files, dict) or not 1 <= len(files) <= 50 or
                any(not isinstance(k, str) or k not in MIME or k == "freeze.json" or
                    not isinstance(v, str) or not SHA.fullmatch(v) for k, v in files.items()) or
                not {"result.json", "manifest.json"} <= files.keys()):
            raise BridgeError(422, "Invalid frozen artifact manifest")
        return files, raw

    def verified(self, run_id, name, files=None):
        check_id(run_id)
        if name not in MIME:
            raise BridgeError(404, "Artifact is not allowlisted")
        if files is None:
            files, freeze_raw = self.freeze(run_id)
            if name == "freeze.json":
                return freeze_raw, hashlib.sha256(freeze_raw).hexdigest()
        expected = files.get(name)
        if expected is None:
            raise BridgeError(404, "Artifact is absent from the frozen run")
        raw = self.read(f"/runs/{run_id}/{name}", MAX_JSON if name.endswith(".json") else MAX_FILE)
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise BridgeError(409, "Saved evidence hash mismatch; artifact withheld")
        if name.endswith(".png") and not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise BridgeError(422, "Invalid PNG artifact")
        if name.endswith(".tif") and raw[:4] not in (b"II*\0", b"MM\0*", b"II+\0", b"MM\0+"):
            raise BridgeError(422, "Invalid TIFF artifact")
        return raw, actual

    def detail(self, run_id):
        files, freeze_raw = self.freeze(run_id)
        result = parse_json(self.verified(run_id, "result.json", files)[0])
        manifest = parse_json(self.verified(run_id, "manifest.json", files)[0])
        item = normalize(result)
        if item["id"] != run_id or not isinstance(manifest, dict) or manifest.get("synthetic") is not result["synthetic"]:
            raise BridgeError(422, "Run/manifest identity or population mismatch")
        item.update(integrity="RESULT_AND_MANIFEST_VERIFIED",
                    freeze_sha256=hashlib.sha256(freeze_raw).hexdigest(),
                    integrity_basis="Local saved freeze map; not a signed external authenticity certificate",
                    artifacts=[{"name": name, "sha256": digest, "mime": MIME[name],
                                "url": f"/api/flood/runs/{run_id}/artifact/{name}"}
                               for name, digest in sorted(files.items())],
                    provenance={"event_time": manifest.get("event_time"),
                                "osm_snapshot": manifest.get("osm_snapshot"),
                                "method": "Fixed VV water/drop thresholds; unvalidated event heuristic",
                                "analysis": {k: v for k, v in manifest.get("analysis", {}).items()
                                             if k in ("water_db", "drop_db", "tile_size", "min_exposed_road_m")},
                                "inputs": [{k: manifest.get(role, {}).get(k) for k in
                                            ("source", "scene_id", "datetime", "units", "bands", "terrain_corrected", "sha256")}
                                           for role in ("pre", "post")]})
        return item

    def exposure(self, run_id):
        raw, digest = self.verified(run_id, "exposure.csv")
        try:
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            required = {"id", "kind", "exposed", "observed", "total", "unit", "status"}
            if not required <= set(reader.fieldnames or []):
                raise ValueError()
            rows = []
            for row in reader:
                if len(rows) >= 10000:
                    raise BridgeError(413, "Exposure table exceeds 10,000 rows")
                clean = {k: row[k][:200] for k in ("id", "kind", "unit", "status")}
                for key in ("exposed", "observed", "total"):
                    clean[key] = float(row[key])
                    if not numeric(clean[key]):
                        raise ValueError()
                rows.append(clean)
        except (ValueError, UnicodeError, KeyError, TypeError):
            raise BridgeError(422, "Invalid exposure table") from None
        return {"rows": rows, "source_sha256": digest, "population": "saved feature intersections"}

    def candidate(self, run_id):
        from PIL import Image
        import numpy as np
        import rasterio
        from rasterio.io import MemoryFile
        raw, digest = self.verified(run_id, "prediction.tif")
        try:
            with MemoryFile(raw) as memory, memory.open() as ds:
                if ds.count != 1 or ds.width * ds.height > 1_000_000:
                    raise ValueError()
                mask = ds.read(1)
                if not np.isin(mask, [0, 1, 2, 255]).all():
                    raise ValueError()
            rgba = np.zeros((*mask.shape, 4), dtype=np.uint8)
            for value, colour in [(0, (19, 29, 40, 255)), (1, (51, 153, 230, 255)),
                                  (2, (255, 194, 81, 255)), (255, (115, 115, 115, 255))]:
                rgba[mask == value] = colour
            out = io.BytesIO()
            Image.fromarray(rgba).save(out, format="PNG")
            return out.getvalue(), digest
        except (ValueError, rasterio.errors.RasterioError):
            raise BridgeError(422, "Invalid categorical candidate raster") from None

    def grid(self, run_id):
        import rasterio
        from rasterio.io import MemoryFile
        from rasterio.warp import transform_bounds
        raw, digest = self.verified(run_id, "prediction.tif")
        try:
            with MemoryFile(raw) as memory, memory.open() as ds:
                return {"crs": str(ds.crs), "pixel_size": list(ds.res), "bounds": list(ds.bounds),
                        "bbox_wgs84": list(transform_bounds(ds.crs, "EPSG:4326", *ds.bounds)),
                        "width": ds.width, "height": ds.height, "source_sha256": digest}
        except (ValueError, rasterio.errors.RasterioError):
            raise BridgeError(422, "Invalid raster georeferencing") from None
