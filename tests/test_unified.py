"""Day 1 regression: admissibility, dispatch, real progress, and failure containment."""
import importlib.util,sys,tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'paired_lab'))
import controller

def optical(**extra):
    return dict(modality='optical',width=256,height=256,count=3,geo=None,**extra)

class RoutingTests(unittest.TestCase):
    def test_six_routes(self):
        cases=[('Describe this image.',[optical()],'vqa'),
               ('Calculate NDVI',[{**optical(),'geo':{'ndvi_supported':True}}],'ndvi'),
               ('What road and building changes occurred?',[optical(),optical()],'temporal'),
               ('Map water',[{**optical(),'count':13},{'modality':'sar','count':2}],'water_map'),
               ('Identify land cover',[{**optical(),'count':10},{'modality':'sar','count':2}],'optical_sar'),
               ('Outline buildings',[optical()],'grounding')]
        for q,records,task in cases:
            with self.subTest(q=q):
                p=controller.plan(q,records);self.assertEqual(p['task'],task)
                self.assertTrue(p['specialist']);self.assertTrue(p['device']);self.assertTrue(p['reason'])
    def test_grounding_categories_and_boxes(self):
        for q,cat in [('Locate aircraft','aircraft'),('Highlight ships','ship'),('Outline sports fields','sports field'),('Where are the stadiums?','stadium'),('Draw bounding boxes around cars','car')]:
            with self.subTest(q=q):self.assertEqual(controller.plan(q,[optical()])['category'],cat)
        self.assertEqual(controller.plan('Draw bounding boxes around cars',[optical()])['mode'],'boxes')
        self.assertEqual(controller.plan('Outline buildings',[optical()])['maturity'],'experimental')
    def test_presence_and_count_do_not_become_grounding(self):
        for q in ['Are there buildings?','How many cars are visible?','Is this rural or urban?']:
            with self.subTest(q=q):self.assertEqual(controller.plan(q,[optical()])['task'],'vqa')
    def test_no_unsupported_grounding_fallback(self):
        for q in ['Outline roads','Outline trees','Outline buildings and cars','Outline buildings near water','Outline buildings and calculate NDVI','Outline red cars','Where did buildings change?']:
            with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,[optical()])
    def test_grounding_size_and_sar_refused(self):
        for r in [{**optical(),'width':32},{**optical(),'width':4000,'height':4000},{**optical(),'modality':'sar'}]:
            with self.subTest(r=r),self.assertRaises(ValueError):controller.plan('Outline buildings',[r])
    def test_temporal_supported_and_unsupported_tasks(self):
        for q in ['What changed between these dates?','Show road changes','Has built-up area increased?','Describe building demolition']:
            with self.subTest(q=q):self.assertEqual(controller.plan(q,[optical(),optical()])['task'],'temporal')
        for q in ['What changed in the forest?','How many buildings changed?','Measure change in hectares','Use SAR to find changes','Describe this image']:
            with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,[optical(),optical()])
    def test_invalid_threshold_and_rgb_ndvi(self):
        for v in [float('nan'),float('inf'),True,'0.5',2]:
            with self.subTest(v=v),self.assertRaises(ValueError):controller.plan('Calculate NDVI',[optical()],v)
        with self.assertRaises(ValueError):controller.plan('Calculate NDVI',[optical()])
    def test_water_contract_routing(self):
        records=[{**optical(),'count':13},{'modality':'sar','count':2}]
        for q in ['Map buildings','What changed in water?','Count water bodies','Water area in square metres']:
            with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,records)

class WorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('unified_server_test',ROOT/'paired_lab/server.py')
        cls.server=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.server)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.out=Path(self.temp.name);self.patcher=patch.object(self.server,'RUNS',self.out);self.patcher.start();self.addCleanup(self.patcher.stop)
        self.source=self.out/'input.upload';self.source.write_bytes(b'original')
        self.record={**optical(),'path':str(self.source),'is_single':True}
        self.plan=controller.plan('Outline buildings',[self.record])
        self.server.jobs['test']={'state':'processing','plan':self.plan,'events':[]};self.server.busy=True
    def test_failed_specialist_never_calls_vqa(self):
        with patch.object(self.server.grounding_bridge,'run',side_effect=ValueError('Model unavailable')),patch.object(self.server.single_bridge,'run') as fallback:
            self.server.work('test',[self.record],'Outline buildings','grounding',{'plan':self.plan})
        self.assertEqual(self.server.jobs['test']['state'],'failed');fallback.assert_not_called();self.assertFalse(self.server.busy)
        self.assertFalse((self.out/'test/evidence.zip').exists())
    def test_stage_history_and_bundle(self):
        def result(*args,progress,**kwargs):
            progress('Detecting actual objects');progress('Detecting actual objects')
            return {'task':'grounding','answer':'test','seconds':.1,'trace':[],'limitations':['test']}
        with patch.object(self.server.grounding_bridge,'run',side_effect=result):
            self.server.work('test',[self.record],'Outline buildings','grounding',{'plan':self.plan})
        job=self.server.jobs['test'];self.assertEqual(job['state'],'complete');self.assertFalse(self.server.busy)
        self.assertEqual(sum(e['stage']=='Detecting actual objects' for e in job['events']),1)
        import zipfile
        with zipfile.ZipFile(self.out/'test/evidence.zip') as z:
            r=json.loads(z.read('result.json'));self.assertEqual(r['execution']['task'],'grounding');self.assertTrue(r['execution_events'])
            self.assertEqual(z.read('input-1.original'),b'original')
    def test_unknown_specialist_fails_closed(self):
        self.server.work('test',[self.record],'anything','unknown',{'plan':self.plan})
        self.assertEqual(self.server.jobs['test']['state'],'failed');self.assertFalse(self.server.busy)

if __name__=='__main__':unittest.main()
