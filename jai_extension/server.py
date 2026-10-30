"""Attach new routes and native panels to an explicitly supplied SATQuery baseline."""
import importlib.util
import os
import sys
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .flood_bridge import BridgeError, FloodBridge, MIME
from .terrain import TerrainStore
from pydantic import BaseModel, StrictBool

WEB = Path(__file__).parent / "web"


class ExtensionOrigin:
    """Validate our configured same-origin port before adapting to baseline's 8767 policy."""
    def __init__(self, app, port):
        self.app, self.port = app, port

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = list(scope["headers"])
            origin = next((v for k, v in headers if k == b"origin"), None)
            allowed = {f"http://127.0.0.1:{self.port}".encode(), f"http://localhost:{self.port}".encode()}
            if origin is not None:
                if origin not in allowed:
                    await JSONResponse({"detail": "Use the local SATQuery extension origin"}, status_code=403)(scope, receive, send)
                    return
                scope = dict(scope, headers=[(k, b"http://127.0.0.1:8767" if k == b"origin" else v) for k, v in headers])
        await self.app(scope, receive, send)


class TerrainRequest(BaseModel):
    confirmed: StrictBool = False


def attach(app, bridge, terrain=None):
    router = APIRouter(prefix="/api/flood")

    @app.exception_handler(BridgeError)
    async def bridge_error(request: Request, error: BridgeError):
        return JSONResponse({"detail": error.message}, status_code=error.status)

    @router.get("/health")
    def health():
        value = bridge.health()
        return JSONResponse(value, status_code=200 if value["available"] else 503)

    @router.get("/runs")
    def runs():
        return bridge.runs()

    @router.get("/runs/{run_id}")
    def detail(run_id: str):
        return bridge.detail(run_id)

    @router.get("/runs/{run_id}/exposure")
    def exposure(run_id: str):
        return bridge.exposure(run_id)

    @router.get("/runs/{run_id}/grid")
    def grid(run_id: str):
        return bridge.grid(run_id)

    @router.get("/runs/{run_id}/candidate.png")
    def candidate(run_id: str):
        raw, source = bridge.candidate(run_id)
        return Response(raw, media_type="image/png", headers={"X-Source-SHA256": source,
                        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

    @router.get("/runs/{run_id}/artifact/{name}")
    def artifact(run_id: str, name: str):
        raw, digest = bridge.verified(run_id, name)
        headers = {"X-Artifact-SHA256": digest, "Cache-Control": "no-store",
                   "X-Content-Type-Options": "nosniff"}
        if not name.endswith(".png"):
            headers["Content-Disposition"] = f'attachment; filename="{name}"'
        return Response(raw, media_type=MIME[name], headers=headers)

    app.include_router(router)
    if terrain is not None:
        trouter = APIRouter(prefix="/api/terrain")

        @trouter.get("/status")
        def terrain_status():
            return terrain.status()

        @trouter.post("/obtain")
        def terrain_obtain(payload: TerrainRequest):
            return terrain.obtain(payload.confirmed)

        @trouter.get("/scenes/{scene_id}")
        def terrain_scene(scene_id: str):
            return terrain.scene(scene_id)

        @trouter.get("/scenes/{scene_id}/raster")
        def terrain_raster(scene_id: str):
            value=terrain.scene(scene_id)
            raw=(terrain.scene_root(scene_id)/"analysis.tif").read_bytes()
            return Response(raw,media_type="image/tiff",headers={"X-Artifact-SHA256":value["hashes"]["analysis.tif"],
                "Content-Disposition":'attachment; filename="copernicus90-syapru-metric.tif"',"X-Content-Type-Options":"nosniff"})

        app.include_router(trouter)
    app.mount("/jai/assets", StaticFiles(directory=WEB), name="jai-assets")
    return app


def create_app():
    bridge = FloodBridge(os.environ.get("FLOODLAB_UPSTREAM", "http://127.0.0.1:8770"))
    baseline = os.environ.get("SATQUERY_BASELINE_ROOT")
    if not baseline:
        raise RuntimeError("Set SATQUERY_BASELINE_ROOT to the approved prior SATQuery installation")
    root = Path(baseline).resolve()
    source = root / "paired_lab/server.py"
    if not source.is_file():
        raise RuntimeError("SATQuery baseline server is missing")
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location("satquery_jai_baseline_server", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    terrain=TerrainStore(os.environ.get("JAI_TERRAIN_ROOT",str(root/".runtime/jai/terrain")))
    app = attach(module.app, bridge, terrain)
    app.add_middleware(ExtensionOrigin, port=int(os.environ.get("JAI_PORT", "8767")))

    # Replace only the home response in this process, leaving baseline source untouched.
    # All existing specialist routes, middleware and static paths retain their handlers.
    @app.get("/", include_in_schema=False)
    def home():
        html = (root / "paired_lab/web/index.html").read_text(encoding="utf-8")
        extra = '<link rel="stylesheet" href="/jai/assets/extension.css"><script defer src="/jai/assets/extension.js"></script><script defer src="/jai/assets/terrain.js"></script>'
        return HTMLResponse(html.replace("</head>", extra + "</head>"))

    route = app.router.routes.pop()
    app.router.routes.insert(0, route)
    return app
