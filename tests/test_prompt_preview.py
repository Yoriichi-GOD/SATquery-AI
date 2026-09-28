"""Input UX regression: safe routing, preview isolation, whole-scene paraphrases."""
import io, unittest, hashlib, ast
from pathlib import Path
from unittest.mock import Mock
import numpy as np
from PIL import Image
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from test_unified import controller, optical
from scene_description import is_scene_description
from input_preview import render
ROOT=Path(__file__).resolve().parents[1]
class PromptTests(unittest.TestCase):
    def test_recorded_context_questions(self):
        for q in ['What kind of area surrounds the harbor?', 'Where is the angular bridge situated in the image?', 'Where is the roundabout located in the image?']:
            with self.subTest(q=q):self.assertEqual(controller.plan(q,[optical()])['task'],'vqa')
    def test_guards_remain(self):
        for q in ['Measure the area surrounding the harbor','Where is the bridge located in the image and predict flood spread?', 'Where is the bridge located in the image in coordinates?', 'What kind of area surrounds the harbor and measure it?']:
            with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,[optical()])
        self.assertEqual(controller.plan('Outline buildings',[optical()])['task'],'grounding')
    def test_generic_rgb_pair_clarifies(self):
        for q in ['Compare these two images','Analyze these images.']:
            with self.subTest(q=q),self.assertRaisesRegex(ValueError,'Choose what to compare'):controller.plan(q,[optical(),optical()])
    def test_scene_paraphrases_use_detailed_description(self):
        for q in ['Analyze this image','Please analyse the scene in detail.']:
            self.assertTrue(is_scene_description(q))
            self.assertEqual(controller.plan(q,[optical()])['task'],'vqa')
        for q in ['Analyze water depth','Analyze this image and predict changes','Analyze these two images']:
            self.assertFalse(is_scene_description(q))
    def test_comparison_recovery_does_not_invent_missing_dates(self):
        from recovery import detail
        d=detail('Choose what to compare. Compatible RGB dates required.')
        self.assertIn('suggested questions',d['next_steps'][0]);self.assertNotIn('invent dates',d['next_steps'][0])
    def test_suggestions_validate_without_execution(self):
        tree=ast.parse((ROOT/'paired_lab/server.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='suggested_queries')
        prepare=Mock(side_effect=lambda p: None if p['query']=='Describe this image.' else (_ for _ in ()).throw(ValueError('incompatible')))
        scope={'prepare':prepare};exec(compile(ast.Module(body=[fn],type_ignores=[]),'suggestions','exec'),scope)
        self.assertEqual(scope['suggested_queries']({'images':['x']}),['Describe this image.'])
        self.assertTrue(all(c.args[0]['images']==['x'] for c in prepare.call_args_list))
        self.assertEqual(scope['suggested_queries'](None),[])
class PreviewTests(unittest.TestCase):
    def raster(self,count=3,width=1200,height=600):
        with MemoryFile() as m:
            with m.open(driver='GTiff',count=count,width=width,height=height,dtype='float32',nodata=-9999,transform=from_origin(0,10,1,1)) as ds:
                data=np.tile(np.linspace(0,1,width,dtype='float32'),(count,height,1));data[:,0,0]=-9999;ds.write(data)
                if count==3:ds.descriptions=('red','green','blue')
            return m.read()
    def test_bounded_rgb_and_original_unchanged(self):
        raw=self.raster();before=hashlib.sha256(raw).hexdigest();png,label=render(raw)
        self.assertEqual(Image.open(io.BytesIO(png)).size,(900,450));self.assertIn('Labelled RGB',label)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),before)
    def test_sar_and_unlabelled_multiband(self):
        raw=self.raster(count=4,width=20,height=20)
        self.assertIn('SAR band 1',render(raw,'sar')[1]);self.assertIn('RGB bands unavailable',render(raw)[1])
    def test_invalid_inputs(self):
        with self.assertRaises(Exception):render(b'not a raster')
        with self.assertRaises(ValueError):render(b'','unknown')
