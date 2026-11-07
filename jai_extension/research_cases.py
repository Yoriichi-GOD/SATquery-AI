"""Read-only, hash-checked four-case research measurements. No acquisition endpoint."""
import hashlib,json
from pathlib import Path
from fastapi import APIRouter,HTTPException
from fastapi.responses import Response

CASES=('nepal','kedarnath','varanasi','sangam-vihar')

class CaseResearchStore:
    def __init__(self,root):self.root=Path(root).resolve()
    def read(self,case,name='summary.json'):
        if case not in CASES or name not in {'summary.json','sources.json','case-panels.png'}:raise HTTPException(404,'Unknown case artifact')
        manifest=self.root/'RELEASE_MANIFEST.json'
        if not manifest.is_file():raise HTTPException(503,'Research measurements have not been provisioned')
        key=f'cases/{case}/{name}';files=json.loads(manifest.read_text())['files']
        if key not in files:raise HTTPException(404,'Case artifact unavailable')
        path=(self.root/key).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():raise HTTPException(409,'Research artifact missing')
        if path.stat().st_size>8*1024*1024:raise HTTPException(413,'Research artifact exceeds size limit')
        raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!=files[key]:raise HTTPException(409,'Research artifact checksum mismatch')
        return raw,digest

def router(store):
    api=APIRouter(prefix='/api/research/cases')
    @api.get('')
    def catalogue():
        items=[]
        for case in CASES:
            raw,digest=store.read(case);value=json.loads(raw)
            items.append({'case_id':case,'boundary_role':value['boundary_role'],'bbox':value['bbox'],
                'accuracy_metrics':value['accuracy_metrics'],'sha256':digest,
                'detail':f'/api/research/cases/{case}','image':f'/api/research/cases/{case}/panels.png'})
        return {'population':'ACQUIRED_CASE_WINDOWS_MEASURED_NOT_INDEPENDENTLY_VALIDATED','cases':items}
    @api.get('/{case}')
    def detail(case:str):
        raw,digest=store.read(case)
        return Response(raw,media_type='application/json',headers={'X-Artifact-SHA256':digest,'Cache-Control':'no-store'})
    @api.get('/{case}/sources')
    def sources(case:str):
        raw,digest=store.read(case,'sources.json')
        return Response(raw,media_type='application/json',headers={'X-Artifact-SHA256':digest,'Cache-Control':'no-store'})
    @api.get('/{case}/panels.png')
    def panels(case:str):
        raw,digest=store.read(case,'case-panels.png')
        return Response(raw,media_type='image/png',headers={'X-Artifact-SHA256':digest,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})
    return api
