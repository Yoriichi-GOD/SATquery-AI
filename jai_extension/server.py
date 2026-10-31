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
from .geo_context import GeoContext
from .investigation import InvestigationEngine,JobManager,REGISTRY
from .visual_context import VisualContext
from pydantic import BaseModel, StrictBool, Field, FiniteFloat
from typing import Optional

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


class ProfileRequest(BaseModel):
    start: tuple[FiniteFloat,FiniteFloat]
    end: tuple[FiniteFloat,FiniteFloat]
    samples: int = Field(default=128,ge=2,le=512,strict=True)


class InvestigationRequest(BaseModel):
    question: str = Field(min_length=3,max_length=1200)
    run_id: Optional[str] = Field(default=None,pattern=r'^[A-Za-z0-9_-]{1,100}$')
    scene_id: Optional[str] = Field(default=None,pattern=r'^terrain-[a-f0-9]{16}$')
    profile: Optional[ProfileRequest] = None


def attach(app, bridge, terrain=None, visual_root=None):
    router = APIRouter(prefix="/api/flood")
    visuals = VisualContext(bridge, visual_root)

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

    @router.get("/runs/{run_id}/visual-context")
    def visual_context(run_id: str):
        return visuals.catalogue(run_id)

    @router.get("/runs/{run_id}/visual/{kind}.png")
    def visual_preview(run_id: str, kind: str):
        import json
        raw, hashes = visuals.preview(run_id, kind)
        return Response(raw,media_type="image/png",headers={"X-Source-Hashes":json.dumps(hashes),
                        "Cache-Control":"no-store","X-Content-Type-Options":"nosniff"})

    @router.get("/runs/{run_id}/grid")
    def grid(run_id: str):
        return bridge.grid(run_id)

    @router.get("/runs/{run_id}/debris")
    def debris(run_id: str):
        return bridge.debris(run_id)

    @router.get("/runs/{run_id}/debris-candidate.png")
    def debris_candidate(run_id: str):
        raw, source = bridge.debris_candidate(run_id)
        return Response(raw, media_type="image/png", headers={"X-Source-SHA256": source,
                        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

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
        geo=GeoContext(bridge,terrain)
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

        @trouter.post('/scenes/{scene_id}/transect')
        def transect(scene_id:str,payload:ProfileRequest):
            return geo.transect(scene_id,payload.start,payload.end,payload.samples)

        app.include_router(trouter)
        context=APIRouter(prefix='/api/context')

        @context.get('/coverage')
        def coverage(run_id:str,scene_id:str):
            return geo.coverage(run_id,scene_id)

        app.include_router(context)
        manager=JobManager(terrain.root.parent/'investigations',lambda check:InvestigationEngine(FloodBridge(bridge.upstream,check=check),terrain))
        app.state.jai_investigations=manager
        app.add_event_handler('shutdown',manager.close)
        investigations=APIRouter(prefix='/api/investigations')

        @investigations.get('/tools')
        def tool_registry():return {'mode':'DETERMINISTIC_TOOL_WORKFLOW','ai_model_used':False,'tools':REGISTRY,'network_acquisition':'not permitted by this workflow'}

        @investigations.post('',status_code=202)
        def investigate(payload:InvestigationRequest):return manager.submit(payload.model_dump())

        @investigations.get('/{job_id}')
        def investigation_status(job_id:str):return manager.get(job_id)

        @investigations.get('/{job_id}/download')
        def investigation_download(job_id:str):
            value=manager.get(job_id)
            return JSONResponse(value,headers={'Content-Disposition':f'attachment; filename="{job_id}.json"','X-Content-Type-Options':'nosniff','Cache-Control':'no-store'})

        @investigations.get('/{job_id}/tools/{tool_name}')
        def investigation_tool_output(job_id:str,tool_name:str):
            value,sha=manager.tool_output(job_id,tool_name)
            return JSONResponse(value,headers={'X-Output-SHA256':sha,'X-Content-Type-Options':'nosniff'})

        @investigations.post('/{job_id}/cancel')
        def investigation_cancel(job_id:str):return manager.cancel(job_id)

        app.include_router(investigations)
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
    app = attach(module.app, bridge, terrain, os.environ.get("FLOODLAB_BASELINE_ROOT"))
    app.add_middleware(ExtensionOrigin, port=int(os.environ.get("JAI_PORT", "8767")))

    # Replace only the home response in this process, leaving baseline source untouched.
    # All existing specialist routes, middleware and static paths retain their handlers.
    @app.get("/", include_in_schema=False)
    def home():
        html = (root / "paired_lab/web/index.html").read_text(encoding="utf-8")
        # Content-derived versions prevent stale UI contracts after an update.
        import hashlib
        css_version = hashlib.sha256((WEB/'earth.css').read_bytes()).hexdigest()[:12]
        js_version = hashlib.sha256((WEB/'earth.js').read_bytes()).hexdigest()[:12]
        extra = f'<link rel="stylesheet" href="/jai/assets/earth.css?v={css_version}"><script defer src="/jai/assets/earth.js?v={js_version}"></script>'
        return HTMLResponse(html.replace("</head>", extra + "</head>"),headers={"Cache-Control":"no-store"})

    route = app.router.routes.pop()
    app.router.routes.insert(0, route)
    return app
