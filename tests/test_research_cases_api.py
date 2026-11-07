import hashlib,json,tempfile,unittest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jai_extension.research_cases import CASES,CaseResearchStore,router

class CaseAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);files={}
        for case in CASES:
            folder=self.root/'cases'/case;folder.mkdir(parents=True)
            values={'summary.json':json.dumps({'case_id':case,'boundary_role':'SYNTHETIC_FIXTURE','bbox':[1,1,2,2],'accuracy_metrics':'NOT_ASSESSED'}).encode(),
                'sources.json':b'{"inputs":[]}', 'case-panels.png':b'\x89PNG\r\n\x1a\nFIXTURE'}
            for name,raw in values.items():
                p=folder/name;p.write_bytes(raw);files[p.relative_to(self.root).as_posix()]=hashlib.sha256(raw).hexdigest()
        (self.root/'RELEASE_MANIFEST.json').write_text(json.dumps({'files':files}))
        app=FastAPI();app.include_router(router(CaseResearchStore(self.root)));self.client=TestClient(app)
    def tearDown(self):self.client.close();self.tmp.cleanup()
    def test_all_four_cases_and_no_accuracy_claim(self):
        r=self.client.get('/api/research/cases');self.assertEqual(r.status_code,200);self.assertEqual(len(r.json()['cases']),4)
        r=self.client.get('/api/research/cases/kedarnath');self.assertEqual(r.json()['accuracy_metrics'],'NOT_ASSESSED')
        self.assertEqual(r.headers['X-Artifact-SHA256'],hashlib.sha256(r.content).hexdigest())
    def test_tampering_rejected(self):
        (self.root/'cases/nepal/summary.json').write_text('{}')
        self.assertEqual(self.client.get('/api/research/cases/nepal').status_code,409)
    def test_image_sources_and_unknown_id(self):
        self.assertEqual(self.client.get('/api/research/cases/varanasi/panels.png').headers['content-type'],'image/png')
        self.assertEqual(self.client.get('/api/research/cases/varanasi/sources').json(),{'inputs':[]})
        self.assertEqual(self.client.get('/api/research/cases/unknown').status_code,404)
    def test_missing_provisioning_unavailable(self):
        (self.root/'RELEASE_MANIFEST.json').unlink()
        self.assertEqual(self.client.get('/api/research/cases').status_code,503)
