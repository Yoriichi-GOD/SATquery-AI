"""Read-only, bounded access to operator-produced scientific replay outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from .flood_bridge import BridgeError

ARTIFACTS = {"summary.json": "application/json", "manifest.json": "application/json",
             "receptors.json": "application/json", "graph.json": "application/json",
             "configuration.json": "application/json", "relationships.csv": "text/csv",
             "nodes.geojson": "application/geo+json", "drainage.geojson": "application/geo+json",
             **{name+".tif": "image/tiff" for name in ["original_dem", "conditioned_dem", "fill_depth",
                "flow_direction_d8", "downstream_index", "contributing_area_m2", "streams",
                "catchment_outlet", "hand_m", "slope_deg", "aspect_deg"]}}


class TerrainExposureStore:
    def __init__(self, root):
        self.root = Path(root)

    def _directory(self, run_id):
        if not re.fullmatch(r"terrain-exposure-[a-z0-9_-]{1,64}", run_id):
            raise BridgeError(404, "Unknown terrain-exposure replay")
        directory = (self.root/run_id).resolve()
        if not directory.is_relative_to(self.root.resolve()) or not directory.is_dir():
            raise BridgeError(404, "Unknown terrain-exposure replay")
        return directory

    def _json(self, path, limit):
        if not path.is_file():
            raise BridgeError(422, "Scientific replay is incomplete")
        if path.stat().st_size > limit:
            raise BridgeError(413, "Scientific metadata exceeds size limit")
        try:
            return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError, UnicodeError):
            raise BridgeError(422, "Invalid scientific replay metadata") from None

    def _manifest(self, directory):
        data = self._json(directory/"manifest.json", 1024*1024)
        if not isinstance(data,dict):
            raise BridgeError(422,"Invalid scientific replay manifest")
        files = data.get("files")
        if (data.get("state") != "complete" or not isinstance(files, dict) or
            not {"summary.json", "receptors.json", "graph.json", "relationships.csv"} <= files.keys() or
            any(Path(k).name != k or k not in ARTIFACTS or not isinstance(v,str) or
                not re.fullmatch("[a-f0-9]{64}", v) for k,v in files.items())):
            raise BridgeError(422, "Incomplete or invalid scientific replay manifest")
        return data

    def verified(self, run_id, name):
        if name not in ARTIFACTS:
            raise BridgeError(404, "Unknown scientific artifact")
        directory = self._directory(run_id)
        manifest = self._manifest(directory)
        path = (directory/name).resolve()
        if not path.is_relative_to(directory) or not path.is_file():
            raise BridgeError(404, "Scientific artifact missing")
        if path.stat().st_size > 256*1024*1024:
            raise BridgeError(413, "Scientific artifact exceeds download limit")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if name != "manifest.json" and digest != manifest["files"].get(name):
            raise BridgeError(409, "Scientific artifact integrity mismatch")
        return raw,digest

    def detail(self, run_id):
        directory = self._directory(run_id)
        # Check caps before reading/hashing metadata intended for interactive use.
        self._json(directory/"summary.json",2*1024*1024)
        self._json(directory/"receptors.json",8*1024*1024)
        raw,summary_hash=self.verified(run_id,"summary.json")
        receptor_raw,receptor_hash=self.verified(run_id,"receptors.json")
        summary=json.loads(raw);receptors=json.loads(receptor_raw)
        if (not isinstance(summary,dict) or not isinstance(receptors,dict) or
            summary.get("schema_version") != "satquery.terrain-exposure/1" or
            summary.get("population") != "GENUINE_SAVED_OBSERVATION_REPLAY" or
            summary.get("status") != "COMPLETE_REPLAY_NOT_SCIENTIFIC_VALIDATION" or
            not isinstance(summary.get("source_run_id"),str) or
            receptors.get("schema_version") != summary["schema_version"] or
            not isinstance(receptors.get("receptors"),list) or len(receptors["receptors"])>10_000):
            raise BridgeError(422,"Unsupported scientific replay schema/population")
        return {"id":run_id,"summary":summary,"receptors":receptors["receptors"],
                "sources":[{"label":"Terrain-conditioned replay summary","url":f"/api/terrain-exposure/runs/{run_id}/artifact/summary.json","sha256":summary_hash},
                           {"label":"Mapped receptor screening attributes","url":f"/api/terrain-exposure/runs/{run_id}/artifact/receptors.json","sha256":receptor_hash}],
                "interpretation":"Potential drainage screening, not dynamic hazard propagation or damage"}

    def status(self):
        runs=[];rejected=[]
        for directory in sorted(self.root.glob("terrain-exposure-*"))[:100]:
            try:
                value=self.detail(directory.name)
                runs.append({"id":value["id"],"source_run_id":value["summary"]["source_run_id"],
                             "resolution":value["summary"]["resolution"],"status":value["summary"]["status"]})
            except (BridgeError,KeyError,TypeError):
                rejected.append({"id":directory.name,"status":"INCOMPLETE_OR_INVALID"})
        return {"runs":runs,"rejected":rejected,"acquisition":"CLI only; no network or local paths accepted by HTTP"}

    def for_flood_run(self, run):
        matches=[item for item in self.status()["runs"] if item["source_run_id"]==run["id"]]
        if len(matches)!=1:
            raise BridgeError(422,"Select exactly one operator-produced terrain-exposure replay for this saved flood run")
        value=self.detail(matches[0]["id"])
        artifacts={a["name"]:a["sha256"] for a in run["artifacts"]}
        for layer,name in [("water","prediction.tif"),("debris","debris-candidates.tif")]:
            if value["summary"]["observations"][layer]["provenance"]["sha256"]!=artifacts.get(name):
                raise BridgeError(409,"Scientific replay does not match the selected frozen observation")
        return value
