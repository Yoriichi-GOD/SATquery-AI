from io import BytesIO
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from affine import Affine
from research.datasets.acquire import download,discover
from research.cases.urban import tiles,ingest_built_up
from research.terrain_exposure.io import Grid


class Response(BytesIO):
    def __init__(self,body,status=200,headers=None):
        super().__init__(body);self.status=status;self.headers=headers or {'ETag':'v1'}


class AcquisitionTests(unittest.TestCase):
    def test_verified_public_download_and_cache_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.tif';expected=hashlib.sha256(b'abcdef').hexdigest()
            with patch('research.datasets.acquire.urlopen',return_value=Response(b'abcdef')):
                receipt=download('https://example.org/source',p,expected_sha256=expected,license_url='https://example.org/license')
            self.assertEqual(receipt['sha256'],expected)
            self.assertEqual(download('https://example.org/source',p,license_url='https://example.org/license')['sha256'],expected)
            p.write_bytes(b'tampered')
            with self.assertRaises(ValueError):download('https://example.org/source',p,license_url='https://example.org/license')
    def test_resume_range_and_version_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.tif';p.with_suffix('.tif.part').write_bytes(b'abc')
            p.with_suffix('.tif.part.json').write_text(json.dumps({'url':'https://example.org/source','etag':'v1'}))
            with patch('research.datasets.acquire.urlopen',return_value=Response(b'def',206,{'ETag':'v1','Content-Range':'bytes 3-5/6'})) as mock:
                download('https://example.org/source',p,license_url='https://example.org/license')
            self.assertEqual(p.read_bytes(),b'abcdef')
            self.assertEqual(mock.call_args.args[0].get_header('Range'),'bytes=3-')
    def test_stac_truncation_and_download_bounds(self):
        raw=json.dumps({'type':'FeatureCollection','features':[],'links':[{'rel':'next'}]}).encode()
        with patch('research.datasets.acquire.urlopen',return_value=Response(raw)):
            self.assertTrue(discover([77,28,78,29],'2025-01-01/2025-02-01')['truncated'])
        with self.assertRaises(ValueError):discover([78,28,77,29],'2025-01-01')
        with self.assertRaises(ValueError):download('http://example.org','x',license_url='license')
        self.assertEqual(len(tiles([82.95,25.22,83.08,25.38])),2)
    def test_categorical_transition_requires_classes_and_order(self):
        grid=Grid((2,2),Affine(10,0,300000,0,-10,3100000),'EPSG:32645')
        a=np.array([[0,6],[0,0]],dtype='uint8');b=np.array([[6,6],[0,0]],dtype='uint8')
        def read(name):return (a if name=='before' else b),np.ones((2,2),bool),grid,{'sha256':'a'*64 if name=='before' else 'b'*64}
        with patch('research.cases.urban.read_raster',side_effect=read):
            obs=ingest_built_up('before','after',6,'2020-01-01','2025-01-01')
            self.assertEqual(obs.candidate.sum(),1)
            with self.assertRaises(ValueError):ingest_built_up('before','after',6,'2025-01-01','2020-01-01')
