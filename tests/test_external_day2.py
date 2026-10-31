"""Day 2 regressions: readiness agreement, restart boundaries and downloaded evidence."""
import json,stat,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import rasterio
from test_external_data import raster,protocol
from paired_lab.external_data.common import DataError,digest,write_json
from paired_lab.external_data.contracts import REGISTRY,preflight
from paired_lab.external_data.store import DatasetStore,inspect_dataset
from paired_lab.external_data.runner import run,verify


class Day2Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.store=DatasetStore(self.root/'datasets',reserve=0)
        self.assets={k:dict(status='checks_passed_inference_unverified',assets=[]) for k in REGISTRY}
    def tearDown(self):self.temp.cleanup()
    def add(self,path,role='input',did=None):
        did=did or self.store.create('Synthetic Day 2 regression')['id'];self.store.import_local(did,path,role)
        return inspect_dataset(self.store,did)
    def test_cdvqa_unequal_rgb_dimensions_blocked_before_model(self):
        first=raster(self.root/'a.tif',np.ones((3,32,32),dtype='uint8'),['red','green','blue'])
        value=self.add(first)
        second=raster(self.root/'b.tif',np.ones((3,32,64),dtype='uint8'),['red','green','blue'])
        value=self.add(second,did=value['id'])
        report=preflight(value,assets=self.assets,declarations={'aligned_ordered':True,'question':'How many buildings have changed?'})
        cdvqa=next(v for v in report['specialists'] if v['specialist']=='cdvqa')
        self.assertFalse(cdvqa['eligible']);self.assertIn('pair.dimensions',[v['parameter'] for v in cdvqa['blocking_reasons']])
    def test_scaled_terrain_cannot_be_treated_as_native_metres(self):
        source=raster(self.root/'dem.tif',np.arange(64,dtype='float32').reshape(1,8,8),['elevation'],dict(units='m'))
        with rasterio.open(source,'r+') as ds:ds.scales=(.1,);ds.offsets=(100,)
        value=self.add(source);choice=next(v for v in preflight(value,assets=self.assets)['specialists'] if v['specialist']=='terrain')
        self.assertFalse(choice['eligible']);self.assertTrue(any(v['parameter'].endswith('native_vertical_calibration') for v in choice['blocking_reasons']))
    def test_cdvqa_accepts_explicit_rgb_colour_interpretation_without_invented_band_names(self):
        sources=[]
        for name in ('before','after'):
            source=raster(self.root/(name+'.tif'),np.ones((3,32,32),dtype='uint8'),['red','green','blue'])
            with rasterio.open(source,'r+') as ds:
                for i in ds.indexes:ds.set_band_description(i,'')
            sources.append(source)
        value=self.add(sources[0]);value=self.add(sources[1],did=value['id'])
        from paired_lab.cdvqa_bridge import CONTRACT
        report=preflight(value,assets=self.assets,declarations={'aligned_ordered':True,'question':CONTRACT['supported_questions'][0]})
        choice=next(v for v in report['specialists'] if v['specialist']=='cdvqa')
        self.assertTrue(choice['eligible'],choice['blocking_reasons'])
    def test_incomplete_upload_restart_cleans_only_temporary_bytes(self):
        value=self.store.create('Restart');row=self.store.register_file(value['id'],'a.txt',3)
        _,part=self.store.upload_target(value['id'],row['id'],0);part.write_bytes(b'ab')
        self.store.cancel_uploads(value['id']);self.store.restart_file(value['id'],row['id'])
        _,part=self.store.upload_target(value['id'],row['id'],0);part.write_bytes(b'abc');self.store.finish_file(value['id'],row['id'])
        self.assertEqual(self.store.get(value['id'])['files'][0]['received'],3)
        with self.assertRaisesRegex(DataError,'Completed originals'):self.store.restart_file(value['id'],row['id'])
        self.assertEqual((self.store.directory(value['id'])/row['path']).read_bytes(),b'abc')
    def test_worker_cannot_start_during_upload_chunk(self):
        from paired_lab.external_data.service import Service
        service=Service(self.root/'service')
        try:
            value=service.store.create('busy');service.store.upload_lock.acquire()
            with self.assertRaisesRegex(DataError,'upload chunk'):service.submit(value['id'],'inspect',{})
            service.store.upload_lock.release()
            with self.assertRaisesRegex(DataError,'incomplete uploads'):service.submit(value['id'],'inspect',{})
        finally:
            if service.store.upload_lock.locked():service.store.upload_lock.release()
            service.close()
    def exported(self):
        value=self.add(raster(self.root/'p.tif'),'prediction')
        value=self.add(raster(self.root/'r.tif'),'reference',did=value['id'])
        spec=protocol();spec['dataset_revision']=value['revision']
        params=dict(prediction_id=value['files'][0]['id'],reference_id=value['files'][1]['id'],protocol=spec)
        with patch('paired_lab.external_data.runner.asset_inventory',return_value={}):result=run(self.store,value['id'],self.root/'export',params)
        self.assertEqual(result['state'],'EVALUATED');return self.root/'export'
    def test_downloaded_zip_recomputes_metrics(self):
        output=self.exported();checked=verify(output/'evidence.zip')
        self.assertTrue(checked['metrics_recomputed']);self.assertEqual(checked['verified_input'],'downloaded ZIP')
    def test_export_zip_traversal_and_links_refused(self):
        for name,mode in [('../escape',stat.S_IFREG),('link',stat.S_IFLNK)]:
            path=self.root/('bad-'+str(mode)+'.zip');entry=zipfile.ZipInfo(name);entry.external_attr=(mode|0o644)<<16;entry.create_system=3
            with zipfile.ZipFile(path,'w') as z:z.writestr(entry,'bad')
            with self.assertRaises(DataError):verify(path)
        self.assertFalse((self.root/'escape').exists())
    def test_export_reference_source_hash_is_checked(self):
        output=self.exported();manifest=json.loads((output/'dataset_manifest.json').read_text());manifest['files'][1]['sha256']='0'*64
        write_json(output/'dataset_manifest.json',manifest)
        checks=(output/'checksums.sha256').read_text().splitlines()
        checks=[digest(output/'dataset_manifest.json')+'  dataset_manifest.json' if line.endswith('  dataset_manifest.json') else line for line in checks]
        (output/'checksums.sha256').write_text('\n'.join(checks)+'\n')
        with self.assertRaisesRegex(DataError,'reference bytes'):verify(output)


if __name__=='__main__':unittest.main()
