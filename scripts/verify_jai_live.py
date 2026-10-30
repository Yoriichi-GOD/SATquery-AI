"""Bounded receipt against the real running services; no acquisition or model calls."""
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "http://127.0.0.1:8768"
RUN = "event-fe47db331390"
session = requests.Session()
session.trust_env = False
checks = []


def get(path, expected=200, **kwargs):
    start = time.perf_counter()
    response = session.get(BASE + path, timeout=20, **kwargs)
    checks.append({"path": path, "status": response.status_code, "expected": expected,
                   "seconds": round(time.perf_counter() - start, 4), "bytes": len(response.content)})
    assert response.status_code == expected, (path, response.status_code, response.text[:150])
    return response


get("/")
get("/api/status")
get("/api/samples")
get("/api/flood/health")
listing = get("/api/flood/runs").json()
detail = get(f"/api/flood/runs/{RUN}").json()
assert detail["summary"]["new_water_m2"] == 95600
assert detail["summary"]["exposed_buildings"] == 2
assert detail["summary"]["connectivity_status"] == "NOT_ASSESSED"
assert "potentially_cut_off" not in detail["summary"]
for artifact in detail["artifacts"]:
    response = get(artifact["url"])
    assert hashlib.sha256(response.content).hexdigest() == artifact["sha256"]
    assert response.headers["X-Artifact-SHA256"] == artifact["sha256"]
get(f"/api/flood/runs/{RUN}/candidate.png")
get(f"/api/flood/runs/{RUN}/grid")
get(f"/api/flood/runs/{RUN}/exposure")
get("/api/flood/runs/missing", 404)
get(f"/api/flood/runs/{RUN}/artifact/.env.local", 404)
get("/api/status", 403, headers={"Origin": "https://example.com"})
get("/api/status", headers={"Origin": BASE})
data = {"recorded_utc": datetime.now(timezone.utc).isoformat(), "population": "FROZEN_REAL_OBSERVATION",
        "run_id": RUN, "platform": platform.platform(), "listing_count": len(listing["runs"]),
        "scope": "HTTP and byte-integrity smoke; individual request times, not a p50/p95 benchmark; no scientific accuracy claim",
        "checks": checks}
out = Path(__file__).resolve().parents[1] / ".runtime/jai/receipts" / ("live-flood-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, indent=2))
print(f"{len(checks)} HTTP checks passed; {len(detail['artifacts'])} saved artifact hashes matched")
