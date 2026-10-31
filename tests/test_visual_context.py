import hashlib,io,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from PIL import Image
from jai_extension.visual_context import VisualContext
from jai_extension.flood_bridge import BridgeError

class LocalOpticalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.grid={'crs':'EPSG:32645','width':3,'height':3,'transform':list(from_origin(10,40,10,10))}
        with MemoryFile() as m:
            with m.open(driver='GTiff',count=7,width=3,height=3,dtype='float32',crs=self.grid['crs'],transform=from_origin(10,40,10,10)) as ds:
                a=np.ones((7,3,3),dtype='float32')*.15;a[6]=1;a[6,0,0]=0;ds.write(a)
            self.raw=m.read()
        p=self.root/'data/automatic/r/optical/2026-08-22/default.tif';p.parent.mkdir(parents=True);p.write_bytes(self.raw);self.path=p
        self.run={'id':'r','provenance':{'debris':{'pre_date':'2026-08-22','source_hashes':{'2026-08-22':hashlib.sha256(self.raw).hexdigest()}}}}
        self.bridge=type('Bridge',(),{'grid':lambda s,r:self.grid})()
        self.v=VisualContext(self.bridge,self.root)
    def test_true_rgb_preview_and_invalid_mask_preserve_source(self):
        a,meta=self.v.optical(self.run,'pre');self.assertEqual(a.shape,(3,3,4));self.assertTrue((a[0,0,:3]==110).all());self.assertTrue((a[1,1,:3]==127).all())
        self.assertEqual(self.path.read_bytes(),self.raw);self.assertEqual(meta['date'],'2026-08-22')
    def test_tampered_or_absent_source_unavailable(self):
        self.path.write_bytes(self.raw+b'changed')
        with self.assertRaises(BridgeError) as cm:self.v.optical(self.run,'pre')
        self.assertEqual(cm.exception.status,404)
    def test_no_unapproved_root_means_unavailable(self):
        with self.assertRaises(BridgeError) as cm:VisualContext(self.bridge).optical(self.run,'pre')
        self.assertEqual(cm.exception.status,404)
    def test_grid_mismatch_withheld(self):
        self.grid['width']=4
        with self.assertRaises(BridgeError) as cm:self.v.optical(self.run,'pre')
        self.assertEqual(cm.exception.status,422)
    def test_date_path_injection_refused(self):
        self.run['provenance']['debris']['pre_date']='../../secret'
        with self.assertRaises(BridgeError):self.v.optical(self.run,'pre')

if __name__=='__main__':unittest.main()
