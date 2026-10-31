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
DEBRIS_KEYS = ("debris_candidate_pixels", "debris_candidate_m2", "debris_valid_pixels",
               "debris_intersected_buildings", "debris_intersected_road_m")


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
                "exposed_road_m", "exposed_bridge_features", *DEBRIS_KEYS):
        value = result["summary"].get(key)
        if value is not None:
            if not numeric(value):
                raise BridgeError(422, "Invalid numerical summary")
            summary[key] = value
    for key in ("debris_candidate_pixels", "debris_valid_pixels", "debris_intersected_buildings"):
        if key in summary and type(summary[key]) is not int:
            raise BridgeError(422, "Debris counts must be nonnegative integers")
    if ("debris_candidate_pixels" in summary and "debris_valid_pixels" in summary and
            summary["debris_candidate_pixels"] > summary["debris_valid_pixels"]):
        raise BridgeError(422, "Debris candidates exceed valid coverage")
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
        "debris_available": False, "debris_status": "NOT_ASSESSED",
        "limitations": [v[:1500] for v in result.get("limitations", []) if isinstance(v, str)][:25],
    }


class FloodBridge:
    def __init__(self, upstream="http://127.0.0.1:8770", session=None, check=None):
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
        self.check = check or (lambda: None)

    def read(self, path, cap=MAX_JSON):
        self.check()
        try:
            with self.session.get(self.upstream + path, timeout=(2, 8), stream=True,
                                  headers={"Accept-Encoding": "identity"},
                                  allow_redirects=False) as response:
                self.check()
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
                    self.check()
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
        debris_meta = manifest.get("debris")
        if (set(DEBRIS_KEYS) <= item["summary"].keys() and
                {"debris-candidates.tif", "debris-exposure.csv"} <= files.keys()):
            if (not isinstance(debris_meta, dict) or
                    debris_meta.get("sha256") != files["debris-candidates.tif"]):
                raise BridgeError(409, "Debris manifest identity mismatch")
            item["provenance"]["debris"] = {k: debris_meta.get(k) for k in
                ("pre_date", "post_date", "method", "source_hashes", "limitations")}
            evidence = self.debris(run_id, run=item)
            item.update(debris_available=True, debris_status="VERIFIED_CANDIDATES",
                        debris_grid=evidence["grid"], debris_coverage=evidence["coverage"])
        return item

    def exposure(self, run_id):
        raw, digest = self.verified(run_id, "exposure.csv")
        return self.exposure_table(raw, digest, "water")

    @staticmethod
    def exposure_table(raw, digest, layer):
        try:
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
            required = {"id", "kind", "exposed", "observed", "total", "unit", "status"}
            headers = reader.fieldnames or []
            if not required <= set(headers) or len(headers) != len(set(headers)):
                raise ValueError()
            rows, seen = [], set()
            for row in reader:
                if len(rows) >= 10000:
                    raise BridgeError(413, "Exposure table exceeds 10,000 rows")
                clean = {k: row[k] for k in ("id", "kind", "unit", "status")}
                if (any(not isinstance(v, str) or not 1 <= len(v) <= 200 or
                        any(ord(c) < 32 for c in v) for v in clean.values()) or
                        clean["id"] in seen or clean["kind"] not in ("road", "bridge", "building") or
                        clean["status"] not in ("exposed", "not_exposed", "unknown") or
                        clean["unit"] != ("m2" if clean["kind"] == "building" else "m")):
                    raise ValueError()
                seen.add(clean["id"])
                for key in ("exposed", "observed", "total"):
                    clean[key] = float(row[key])
                    if not numeric(clean[key]):
                        raise ValueError()
                tolerance = max(1e-6, clean["total"] * 1e-9)
                expected_status = ("exposed" if clean["exposed"] > 1e-8 else
                                   "not_exposed" if clean["observed"] >= clean["total"] - 1e-8 else "unknown")
                if (clean["exposed"] > clean["observed"] + tolerance or
                        clean["observed"] > clean["total"] + tolerance or
                        clean["status"] != expected_status):
                    raise ValueError()
                rows.append(clean)
        except (ValueError, UnicodeError, KeyError, TypeError, csv.Error):
            raise BridgeError(422, "Invalid exposure table") from None
        return {"rows": rows, "source_sha256": digest, "layer": layer,
                "population": "saved feature intersections; possible exposure, not confirmed damage"}

    def mask(self, run_id, layer="water", files=None):
        """Decode only a hash-verified bounded native categorical grid."""
        import numpy as np
        import rasterio
        from rasterio.io import MemoryFile
        from rasterio.warp import transform_bounds
        name = "debris-candidates.tif" if layer == "debris" else "prediction.tif"
        raw, sha = self.verified(run_id, name, files)
        try:
            with MemoryFile(raw) as memory, memory.open() as ds:
                t = ds.transform
                if (ds.count != 1 or ds.dtypes[0] != "uint8" or ds.crs is None or
                        not ds.crs.is_projected or ds.crs.linear_units != "metre" or
                        not 1 <= ds.width * ds.height <= 1_000_000 or ds.nodata != 255 or
                        not all(math.isfinite(v) for v in t) or t.b or t.d or t.a <= 0 or t.e >= 0 or
                        any(h*w > 16*1024*1024 for h,w in ds.block_shapes)):
                    raise ValueError()
                mask = ds.read(1)
                if not np.isin(mask, [0,1,255] if layer == "debris" else [0,1,2,255]).all():
                    raise ValueError()
                grid = {"crs": str(ds.crs), "transform": list(t), "pixel_size": list(ds.res),
                        "bounds": list(ds.bounds), "bbox_wgs84": list(transform_bounds(ds.crs,"EPSG:4326",*ds.bounds)),
                        "width": ds.width, "height": ds.height, "source_sha256": sha}
                stats = {"candidate_pixels": int((mask == (1 if layer == "debris" else 2)).sum()),
                         "valid_pixels": int((mask != 255).sum()), "total_pixels": int(mask.size),
                         "invalid_pixels": int((mask == 255).sum()), "pixel_area_m2": abs(t.a*t.e)}
                return mask, grid, stats, sha
        except (ValueError, TypeError, rasterio.errors.RasterioError):
            raise BridgeError(422, "Invalid categorical candidate raster; layer withheld") from None

    def debris(self, run_id, run=None):
        run = run or self.detail(run_id)
        if run.get("id") != run_id:
            raise BridgeError(409, "Selected debris run changed; evidence withheld")
        files = {a["name"]: a["sha256"] for a in run["artifacts"]}
        if not set(DEBRIS_KEYS) <= run["summary"].keys() or not {"debris-candidates.tif","debris-exposure.csv"} <= files.keys():
            return {"run_id": run_id, "debris_available": False, "status": "NOT_ASSESSED", "rows": [],
                    "summary": {}, "reason": "Complete verified debris evidence is absent; no zero measurement inferred."}
        mask, grid, coverage, sha = self.mask(run_id, "debris", files)
        raw, csv_sha = self.verified(run_id, "debris-exposure.csv", files)
        exposure = self.exposure_table(raw, csv_sha, "debris")
        s = run["summary"]
        buildings = sum(r["kind"] == "building" and r["exposed"] > 0 for r in exposure["rows"])
        roads = sum(r["exposed"] for r in exposure["rows"] if r["kind"] in ("road","bridge"))
        if (coverage["candidate_pixels"] != s["debris_candidate_pixels"] or
                coverage["valid_pixels"] != s["debris_valid_pixels"] or
                not math.isclose(coverage["candidate_pixels"]*coverage["pixel_area_m2"],s["debris_candidate_m2"],abs_tol=.01) or
                buildings != s["debris_intersected_buildings"] or
                not math.isclose(roads,s["debris_intersected_road_m"],abs_tol=.01)):
            raise BridgeError(409, "Debris summary, mask or intersection table disagree")
        return {"run_id":run_id,"debris_available":True,"status":"VERIFIED_CANDIDATES",
                "summary":{k:s[k] for k in DEBRIS_KEYS},"grid":grid,"coverage":coverage,
                "rows":exposure["rows"],"source_sha256":csv_sha,
                "source_hashes":{"debris-candidates.tif":sha,"debris-exposure.csv":csv_sha},
                "artifacts":[a for a in run["artifacts"] if a["name"] in ("debris-candidates.tif","debris-exposure.csv","result.json","manifest.json")],
                "provenance":run.get("provenance",{}).get("debris",{}),
                "semantics":"Fixed vegetation-to-bare + NDVI loss + SAR-change proxy; not a validated debris classifier.",
                "limitations":["Water and debris coverage differ; do not sum infrastructure intersections.",
                                "Intersections indicate possible exposure, not confirmed damage, closure or safety.",
                                "EMSR927 is a class-mismatched checking reference, not debris accuracy."]}

    def debris_candidate(self, run_id):
        from PIL import Image
        import numpy as np
        evidence = self.debris(run_id)
        if not evidence["debris_available"]:
            raise BridgeError(404, "Debris is NOT_ASSESSED for this run")
        files = evidence["source_hashes"]
        mask, grid, coverage, sha = self.mask(run_id,"debris",files)
        rgba = np.zeros((*mask.shape,4),dtype="uint8")
        for value, colour in [(0,(25,30,33,255)),(1,(191,116,74,255)),(255,(110,110,110,255))]:
            rgba[mask == value] = colour
        out=io.BytesIO();Image.fromarray(rgba).save(out,format="PNG")
        return out.getvalue(),sha

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
        mask, grid, coverage, sha = self.mask(run_id)
        return grid
