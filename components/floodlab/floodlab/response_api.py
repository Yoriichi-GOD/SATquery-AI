"""Additive response routes; no client paths, external acquisition or model calls."""
from fastapi import APIRouter,HTTPException
from fastapi.responses import Response
from pydantic import BaseModel,Field
from .response_store import ARTIFACTS

class ScenarioRequest(BaseModel):
    restore_way_ids:list[str]=Field(default_factory=list,max_length=64)

def router(store):
    api=APIRouter(prefix='/api/response')
    def calculate(run_id,ways):
        try:return store.calculate(run_id,ways)
        except FileNotFoundError as e:raise HTTPException(404,str(e))
        except ValueError as e:raise HTTPException(422,str(e))
        except RuntimeError as e:raise HTTPException(409,str(e))
    @api.get('/runs/{run_id}')
    def baseline(run_id:str):return calculate(run_id,[])
    @api.post('/runs/{run_id}/scenarios')
    def scenario(run_id:str,request:ScenarioRequest):return calculate(run_id,request.restore_way_ids)
    @api.get('/runs/{run_id}/scenarios/{scenario_id}/{name}')
    def artifact(run_id:str,scenario_id:str,name:str):
        try:raw,sha=store.artifact(run_id,scenario_id,name)
        except FileNotFoundError as e:raise HTTPException(404,str(e))
        except ValueError as e:raise HTTPException(409,str(e))
        return Response(raw,media_type=ARTIFACTS[name],headers={'X-Artifact-SHA256':sha,'Cache-Control':'no-store',
            'Content-Disposition':f'attachment; filename="{name}"','X-Content-Type-Options':'nosniff'})
    return api
