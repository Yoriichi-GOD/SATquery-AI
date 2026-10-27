import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from test_unified import controller
import cdvqa_bridge as bridge

class CDVQAIntegrationTests(unittest.TestCase):
    def records(self):
        return [dict(cdvqa_rgb=True,modality='optical',shape=[256,256]) for _ in range(2)]

    def test_explicit_supported_dispatch(self):
        self.assertEqual(controller.plan('Did the areas of buildings change?',self.records())['task'],'cdvqa')

    def test_unsupported_and_compound_refused(self):
        for q in ['Describe everything that changed','Did the areas of buildings change and count cars?','Predict tomorrow']:
            with self.subTest(q=q),self.assertRaises(ValueError):controller.plan(q,self.records())

    def test_mixed_modes_refused(self):
        with self.assertRaises(ValueError):controller.plan('Did the areas of buildings change?',self.records()[:1]+[dict(modality='optical')])

    def test_alignment_and_dimensions_required(self):
        for value in [False,None,'true',1]:
            with self.subTest(value=value),self.assertRaises(ValueError):bridge.validate(self.records(),value)
        records=self.records();records[1]['shape']=[128,256]
        with self.assertRaises(ValueError):bridge.validate(records,True)

    def test_missing_checkpoint_actionable(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(bridge,'CDVQA',Path(tmp)):
            with self.assertRaisesRegex(ValueError,'preflight'):bridge.available()

    def test_rgb_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.png'
            Image.new('L',(64,64)).save(path)
            with self.assertRaises(ValueError):bridge.inspect_rgb(path)
            Image.new('RGB',(64,64)).save(path)
            self.assertTrue(bridge.inspect_rgb(path)['cdvqa_rgb'])

if __name__=='__main__':unittest.main()
