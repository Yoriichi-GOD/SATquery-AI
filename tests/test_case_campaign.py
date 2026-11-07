import tempfile,unittest
from pathlib import Path
import numpy as np
import rasterio
from affine import Affine
from research.cases.process_campaign import transitions,landsat_clear,index,roi,metric_grid,warp,declared_terrain_files,validate_inventory
from research.datasets.cog import public_url,native_window,acquire
from research.evaluation.evidence_contract import check

class CaseCampaignTests(unittest.TestCase):
    def test_stale_or_missing_required_registration_refused(self):
        cfg={'bbox':[1,1,2,2]};a={'case_id':'varanasi','protocol_sha256':'correct','assets':[]}
        with self.assertRaisesRegex(ValueError,'identity'):validate_inventory('varanasi',cfg,{},a,'changed')
        with self.assertRaisesRegex(ValueError,'not registered'):validate_inventory('varanasi',cfg,{},a,'correct')
    def test_unregistered_buffer_cannot_enter_measurement(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'dem30-buffer.tif').write_bytes(b'not a registered input')
            (root/'dem30-28-85.tif').write_bytes(b'registered')
            records=[{'state':'ACQUIRED','label':'dem30-28-85','file':'dem30-28-85.tif'}]
            self.assertEqual(declared_terrain_files(root,records),[root/'dem30-28-85.tif'])
    def test_stock_flow_and_unknown_support(self):
        a=np.array([[7,2,7],[0,1,5]]);b=np.array([[2,7,7],[7,1,7]])
        v=a!=0;r=transitions(a,b,v,100)
        self.assertEqual(r['common_pixels'],5)
        self.assertEqual(r['gross_built_gain_ha'],.02)
        self.assertEqual(r['gross_built_loss_ha'],.01)
        self.assertEqual(r['net_built_difference_ha'],.01)
        self.assertEqual(sum(r['transition_pixels'].values()),5)
    def test_unexpected_class_refused(self):
        with self.assertRaises(ValueError):transitions(np.array([[3]]),np.array([[7]]),np.ones((1,1),bool),100)
    def test_cloud_shadow_snow_saturation_excluded(self):
        qa=np.array([[0,1,2,4,8,16,32,64,128,0]])
        sat=np.array([[0,0,0,0,0,0,0,0,0,1]])
        self.assertEqual(landsat_clear(qa,sat,np.ones(qa.shape,bool)).tolist(),[[True,False,False,False,False,False,False,True,True,False]])
    def test_index_zero_denominator_unknown(self):
        value=index(np.array([[1.,0.]]),np.array([[3.,0.]]),np.ones((1,2),bool))
        self.assertAlmostEqual(value[0,0],-.5);self.assertTrue(np.isnan(value[0,1]))
    def test_source_token_stripped_and_external_refused(self):
        url='https://landsateuwest.blob.core.windows.net/landsat-c2/x.TIF?sig=SECRET'
        self.assertNotIn('SECRET',public_url(url))
        with self.assertRaises(ValueError):public_url('https://example.org/x.tif')
    def test_clamped_window_and_no_coverage(self):
        t=Affine(10,0,0,0,-10,100)
        w=native_window((-20,-20,50,120),t,10,10)
        self.assertEqual(tuple(w.flatten()),(0,0,5,10))
        with self.assertRaises(ValueError):native_window((200,200,300,300),t,10,10)
    def test_warp_respects_mask(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.tif';g=metric_grid({'bbox':[77.25,28.49,77.251,28.491],'crs':'EPSG:32643'},30)
            with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
                with rasterio.open(p,'w',driver='GTiff',height=g.shape[0],width=g.shape[1],count=1,dtype='uint8',crs=g.crs,transform=g.transform) as dst:
                    dst.write(np.ones(g.shape,'uint8'),1);m=np.ones(g.shape,'uint8')*255;m[0,0]=0;dst.write_mask(m)
            result=warp([p],g);self.assertTrue(np.isnan(result[0,0]));self.assertEqual(result[1,1],1)
    def test_cached_tamper_fails_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.tif';p.write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'lacks provenance'):
                acquire('https://copernicus-dem-30m.s3.amazonaws.com/x.tif',[1,1,2,2],p,license_url='x',product='x')
    def test_unknown_is_not_zero_and_wrong_interpretation_refused(self):
        self.assertEqual(check({'fact_id':'missing','value':0},{},{}),'UNKNOWN_FACT')
        self.assertEqual(check({'fact_id':'f1','value':0},{'f1':{'value':None}},{}),'UNAVAILABLE_EVIDENCE')
        fact={'value':10,'kind':'conditional_measurement'}
        self.assertEqual(check({'fact_id':'area','kind':'confirmed_damage'},{'area':fact},{}),'UNSUPPORTED_INTERPRETATION')

if __name__=='__main__':unittest.main()
