"""Synthetic integrity/contract regressions, not Nepal accuracy measurements."""
import copy
import hashlib
import io
import json
import unittest
from unittest.mock import patch
import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from fastapi import FastAPI
from jai_extension.flood_bridge import BridgeError,FloodBridge,normalize
from jai_extension.investigation import InvestigationEngine,plan
from jai_extension.server import attach


def raster(values,dtype='uint8'):
    a=np.asarray(values,dtype=dtype)
    with MemoryFile() as m:
        with m.open(driver='GTiff',height=a.shape[0],width=a.shape[1],count=1,dtype=dtype,
                    crs='EPSG:32645',transform=from_origin(335340,3119190,10,10),nodata=255) as ds:
            ds.write(a,1)
        return m.read()


CSV=b'id,kind,exposed,observed,total,unit,status\nb1,building,10,20,20,m2,exposed\nr1,road,30,40,100,m,exposed\nr2,road,0,0,50,m,unknown\n'


class MemoryBridge(FloodBridge):
    def __init__(self):
        super().__init__();self.files={};self.results={}
        for rid,area in [('one',200),('two',200)]:
            summary={'valid_pixels':9,'total_pixels':9,'new_water_pixels':1,'new_water_m2':100,
                     'exposed_buildings':0,'exposed_road_m':0,'connectivity_assessed':False,
                     'debris_candidate_pixels':2,'debris_candidate_m2':area,'debris_valid_pixels':5,
                     'debris_intersected_buildings':1,'debris_intersected_road_m':30}
            result={'run_id':rid,'synthetic':False,'summary':summary,'limitations':[]}
            mask=raster([[1,1,0],[0,0,255],[255,255,255]])
            manifest={'synthetic':False,'event_time':'2026-08-26','debris':{'sha256':hashlib.sha256(mask).hexdigest(),
                      'method':'software fixture proxy','pre_date':'2026-08-22','post_date':'2026-08-27'}}
            self.files[rid]={'result.json':json.dumps(result).encode(),'manifest.json':json.dumps(manifest).encode(),
                             'debris-candidates.tif':mask,'debris-exposure.csv':CSV,'exposure.csv':CSV}
            self.results[rid]=result
        self.refreeze()

    def refreeze(self):
        for rid,files in self.files.items():
            hashes={k:hashlib.sha256(v).hexdigest() for k,v in files.items() if k!='freeze.json'}
            files['freeze.json']=json.dumps({'files':hashes}).encode()

    def read(self,path,cap=16*1024*1024):
        parts=path.split('/')
        if len(parts)!=4 or parts[2] not in self.files or parts[3] not in self.files[parts[2]]:
            raise BridgeError(404,'Missing fixture')
        raw=self.files[parts[2]][parts[3]]
        if len(raw)>cap:raise BridgeError(413,'Fixture limit')
        return raw


class RoadHomeTests(unittest.TestCase):
    def setUp(self):self.b=MemoryBridge()
    def status(self,status,fn,*args):
        with self.assertRaises(BridgeError) as cm:fn(*args)
        self.assertEqual(cm.exception.status,status)
    def change_summary(self,key,value):
        self.b.results['one']['summary'][key]=value
        self.b.files['one']['result.json']=json.dumps(self.b.results['one']).encode();self.b.refreeze()
    def test_missing_debris_is_not_assessed_without_zero(self):
        result=normalize({'run_id':'none','synthetic':False,'summary':{}})
        self.assertFalse(result['debris_available']);self.assertEqual(result['debris_status'],'NOT_ASSESSED')
        self.assertNotIn('debris_candidate_m2',result['summary'])
    def test_separate_coverage_and_native_counts(self):
        run=self.b.detail('one');e=self.b.debris('one')
        self.assertTrue(run['debris_available']);self.assertEqual(e['coverage']['valid_pixels'],5)
        self.assertEqual(run['summary']['valid_pixels'],9);self.assertEqual(e['coverage']['invalid_pixels'],4)
        self.assertEqual(e['rows'][-1]['status'],'unknown');self.assertEqual(e['summary']['debris_intersected_buildings'],1)
    def test_tampered_mask_hash_withheld(self):
        self.b.files['one']['debris-candidates.tif']+=b'x';self.status(409,self.b.detail,'one')
    def test_corrupt_hash_valid_tiff_withheld(self):
        self.b.files['one']['debris-candidates.tif']=b'II*\0broken';self.b.refreeze()
        m=json.loads(self.b.files['one']['manifest.json']);m['debris']['sha256']=hashlib.sha256(self.b.files['one']['debris-candidates.tif']).hexdigest()
        self.b.files['one']['manifest.json']=json.dumps(m).encode();self.b.refreeze()
        self.status(422,self.b.detail,'one')
    def test_categorical_mask_refuses_unknown_classes(self):
        with patch.object(self.b,'verified',return_value=(raster([[7,0,255]]),'a'*64)):
            self.status(422,self.b.mask,'one','debris')
    def test_summary_coverage_mismatch_refused(self):
        self.change_summary('debris_valid_pixels',9);self.status(409,self.b.detail,'one')
    def test_summary_road_total_mismatch_refused(self):
        self.change_summary('debris_intersected_road_m',99);self.status(409,self.b.detail,'one')
    def test_stale_cross_run_snapshot_refused(self):
        old=self.b.detail('one');self.status(409,self.b.debris,'two',old)
    def test_partial_metadata_never_enables_debris(self):
        del self.b.results['one']['summary']['debris_valid_pixels']
        self.b.files['one']['result.json']=json.dumps(self.b.results['one']).encode();self.b.refreeze()
        self.assertFalse(self.b.detail('one')['debris_available']);self.assertFalse(self.b.debris('one')['debris_available'])
    def test_fractional_and_bool_counts_refused(self):
        for value in (2.5,True):
            self.status(422,normalize,{'run_id':'x','synthetic':False,'summary':{'debris_candidate_pixels':value}})
    def test_csv_headers_ids_status_finiteness_and_units(self):
        variants=[CSV.replace(b'id,kind',b'wrong,kind'),CSV.replace(b'r1,road',b'b1,road'),
                  CSV.replace(b',exposed\n',b',safe\n'),CSV.replace(b',30,40',b',nan,40'),
                  CSV.replace(b',30,40',b',60,40'),CSV.replace(b',m,exposed',b',km,exposed')]
        for raw in variants:
            with self.subTest(raw=raw):self.status(422,self.b.exposure_table,raw,'a'*64,'debris')
    def test_png_is_native_and_hash_linked(self):
        from PIL import Image
        raw,sha=self.b.debris_candidate('one')
        with Image.open(io.BytesIO(raw)) as im:
            self.assertEqual(im.size,(3,3));self.assertEqual(im.getpixel((2,2)),(110,110,110,255))
        self.assertEqual(sha,self.b.freeze('one')[0]['debris-candidates.tif'])
    def test_registered_routes_and_source_header(self):
        app=attach(FastAPI(),self.b)
        routes={r.path:r for r in app.routes}
        e=routes['/api/flood/runs/{run_id}/debris'].endpoint('one')
        self.assertEqual(e['summary']['debris_candidate_m2'],200)
        p=routes['/api/flood/runs/{run_id}/debris-candidate.png'].endpoint('one')
        self.assertEqual(p.status_code,200)
        self.assertEqual(p.headers['x-source-sha256'],e['source_hashes']['debris-candidates.tif'])
    def test_debris_question_uses_distinct_actual_tool(self):
        trace=[];engine=InvestigationEngine(self.b,None)
        r=engine.execute({'question':'Which roads intersect water or possible debris surface changes?','run_id':'one'},lambda:None,lambda n,v,s:trace.append(n))
        self.assertEqual(r['state'],'complete');self.assertIn('get_debris_evidence',trace)
        self.assertEqual(r['review_rows_by_layer']['debris'][0]['exposed'],30)
        self.assertIn('debris',r['review_rows_by_layer']);self.assertIn('water',r['review_rows_by_layer'])
        claims={c['field']:c['value'] for c in r['claims']}
        self.assertEqual(claims['/summary/debris_candidate_m2'],200)
        self.assertEqual(claims['/summary/connectivity_assessed'],'NOT_ASSESSED')
    def test_missing_debris_question_abstains(self):
        e=InvestigationEngine(self.b,None)
        for name in ('debris-candidates.tif','debris-exposure.csv'):
            del self.b.files['one'][name]
        self.b.refreeze()
        r=e.execute({'question':'Show possible landslide debris','run_id':'one'},lambda:None,lambda *a:None)
        self.assertEqual(r['state'],'abstained');self.assertEqual(r['claims'],[])
    def test_unsafe_questions_abstain_before_source_access(self):
        for q in ('Which road is safe?','How many buildings destroyed?','Calculate debris risk','Is the village cut off?','Give an evacuation route','Predict landslides'):
            self.assertEqual(plan(q)[0],[],q)
    def test_each_question_uses_selected_run_not_cached_last_run(self):
        self.b.results['two']['summary']['debris_intersected_road_m']=30
        engine=InvestigationEngine(self.b,None)
        for rid in ('one','two'):
            r=engine.execute({'question':'Possible debris intersections','run_id':rid},lambda:None,lambda *a:None)
            self.assertTrue(all('/runs/'+rid+'/' in s['url'] for s in r['sources']))
    def test_changed_debris_snapshot_rejected_in_investigation(self):
        real=self.b.debris
        def changed(*args,**kwargs):
            value=real(*args,**kwargs);value['artifacts'][0]['sha256']='f'*64;return value
        with patch.object(self.b,'debris',side_effect=changed):
            self.status(409,InvestigationEngine(self.b,None).execute,{'question':'debris','run_id':'one'},lambda:None,lambda *a:None)


if __name__=='__main__':unittest.main()
