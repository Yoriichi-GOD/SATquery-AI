"""Synthetic API fixtures; genuine-data HTTP checks are recorded separately."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from fastapi import FastAPI
from jai_extension.flood_bridge import BridgeError
from jai_extension.investigation import InvestigationEngine,plan
from jai_extension.server import attach
from jai_extension.terrain_exposure import TerrainExposureStore


class ScientificStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.id='terrain-exposure-test'
        self.directory=self.root/self.id;self.directory.mkdir()
        self.summary={'schema_version':'satquery.terrain-exposure/1','population':'GENUINE_SAVED_OBSERVATION_REPLAY',
            'source_run_id':'fixture','status':'COMPLETE_REPLAY_NOT_SCIENTIFIC_VALIDATION',
            'resolution':{'status':'INSUFFICIENT_RESOLUTION'},'hydrology':{'valid_cells':25,'stream_cells':3,'maximum_fill_m':1},
            'observations':{layer:{'provenance':{'sha256':value}} for layer,value in [('water','a'*64),('debris','b'*64)]}}
        self.receptors={'schema_version':self.summary['schema_version'],'receptors':[]}
        files={'summary.json':json.dumps(self.summary),'receptors.json':json.dumps(self.receptors),
               'graph.json':'{}','relationships.csv':'source_id,receptor_id,status\n'}
        self.manifest={'state':'complete','files':{}}
        for name,text in files.items():
            raw=text.encode();(self.directory/name).write_bytes(raw)
            self.manifest['files'][name]=hashlib.sha256(raw).hexdigest()
        (self.directory/'manifest.json').write_text(json.dumps(self.manifest))
        self.store=TerrainExposureStore(self.root)
        self.run={'id':'fixture','population':'FROZEN_REAL_OBSERVATION','provenance':{'event_time':'2026-08-26'},
            'artifacts':[{'name':'prediction.tif','sha256':'a'*64},{'name':'debris-candidates.tif','sha256':'b'*64}]}

    def test_match_selected_observation_and_no_stale_substitution(self):
        self.assertEqual(self.store.for_flood_run(self.run)['id'],self.id)
        bad=copy.deepcopy(self.run);bad['artifacts'][0]['sha256']='c'*64
        with self.assertRaises(BridgeError) as context:self.store.for_flood_run(bad)
        self.assertEqual(context.exception.status,409)
        bad['id']='another-run'
        with self.assertRaises(BridgeError):self.store.for_flood_run(bad)
    def test_tampered_receptors_and_path_escape_fail(self):
        (self.directory/'receptors.json').write_text('{}')
        with self.assertRaises(BridgeError) as context:self.store.detail(self.id)
        self.assertEqual(context.exception.status,409)
        for identity in ['../elsewhere','terrain-exposure-../elsewhere','file:///etc/passwd']:
            with self.assertRaises(BridgeError):self.store.detail(identity)
        with self.assertRaises(BridgeError):self.store.verified(self.id,'../../secret')
    def test_incomplete_run_not_listed_as_completed(self):
        self.manifest['state']='running';(self.directory/'manifest.json').write_text(json.dumps(self.manifest))
        value=self.store.status();self.assertEqual(value['runs'],[])
        self.assertEqual(value['rejected'][0]['status'],'INCOMPLETE_OR_INVALID')
    def test_routing_and_resolution_abstention_preserve_evidence(self):
        parent=self
        class Bridge:
            def detail(self,run_id):return copy.deepcopy(parent.run)
        engine=InvestigationEngine(Bridge(),None,self.store);trace=[]
        result=engine.execute({'question':'Which buildings have downstream connectivity?','run_id':'fixture'},
                              lambda:None,lambda n,v,s:trace.append(n))
        self.assertEqual(result['state'],'abstained');self.assertEqual(len(result['claims']),3)
        self.assertEqual(trace,['get_run','get_terrain_exposure'])
        self.assertFalse(result['ai_model_used'])
        result=engine.execute({'question':'Show catchments and flow accumulation','run_id':'fixture'},lambda:None,lambda *a:None)
        self.assertEqual(result['state'],'complete')
        self.assertEqual(plan('Predict the flood depth downstream')[0],[])
        empty=TerrainExposureStore(self.root/'missing')
        missing=InvestigationEngine(Bridge(),None,empty).execute(
            {'question':'Show drainage pathways','run_id':'fixture'},lambda:None,lambda *args:None)
        self.assertEqual(missing['state'],'abstained');self.assertEqual(missing['claims'],[])
        self.assertEqual(missing['tool_outputs']['get_terrain_exposure']['status'],'NOT_ASSESSED')
    def test_additive_http_routes_and_verified_download(self):
        from fastapi.testclient import TestClient
        class Bridge:upstream='http://127.0.0.1:1'
        class Terrain:root=self.root/'terrain'
        app=FastAPI();attach(app,Bridge(),Terrain(),exposure_store=self.store)
        with TestClient(app) as client:
            response=client.get('/api/terrain-exposure/runs')
            self.assertEqual(response.status_code,200);self.assertEqual(len(response.json()['runs']),1)
            response=client.get(f'/api/terrain-exposure/runs/{self.id}/artifact/summary.json')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers['x-artifact-sha256'],hashlib.sha256(response.content).hexdigest())
            self.assertEqual(client.get('/api/terrain-exposure/runs/not-a-run').status_code,404)
