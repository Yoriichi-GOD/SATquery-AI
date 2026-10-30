"""Synthetic correctness/security tests. These are not model accuracy benchmarks."""
import hashlib
import json
import stat
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
import rasterio
from rasterio.transform import from_origin
from paired_lab.external_data.common import DataError, digest
from paired_lab.external_data.contracts import REGISTRY, preflight
from paired_lab.external_data.metrics import evaluate, table_metrics
from paired_lab.external_data.raster import inspect_raster
from paired_lab.external_data.store import DatasetStore, inspect_dataset


def raster(path,values=None,bands=None,tags=None,crs='EPSG:32645',transform=None,nodata=None):
    values=np.array([[[0,1,1],[0,1,0]]],dtype='uint8') if values is None else values
    if values.ndim==2:values=values[None]
    with rasterio.open(path,'w',driver='GTiff',width=values.shape[2],height=values.shape[1],count=values.shape[0],dtype=values.dtype,
        crs=crs,transform=transform if transform is not None else from_origin(300000,3100000,10,10),nodata=nodata) as ds:
        ds.write(values)
        for i,name in enumerate(bands or ['mask']*values.shape[0],1):ds.set_band_description(i,name)
        ds.update_tags(**(tags or {}))
    return path


def protocol(task='segmentation'):
    return dict(task=task,dataset_revision='synthetic-test-only',scene_ids=['fixture'],split='evaluation',
        reference_provenance='Hand-constructed software fixture; not independent scientific ground truth',license='test fixture',
        training_exposure='not applicable',excluded_case_ids=[],classes={'0':'non_water','1':'water'},
        prediction_class_mapping={'0':0,'1':1},reference_class_mapping={'0':0,'1':1},ignore_values=[255])


class ExternalDataTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.store=DatasetStore(self.root/'private',reserve=0)

    def tearDown(self):self.temp.cleanup()

    def imported(self,path,role='input'):
        value=self.store.create('Synthetic fixture')
        self.store.import_local(value['id'],path,role)
        return inspect_dataset(self.store,value['id'])

    def test_streamed_hash_matches_known_bytes(self):
        path=self.root/'source.txt';path.write_bytes(b'abc')
        self.assertEqual(digest(path),'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')

    def test_tiff_metadata_and_multiband_statistics(self):
        values=np.arange(3*32*24,dtype='uint16').reshape(3,32,24)
        path=raster(self.root/'multi.tif',values,['red','green','blue'])
        result=self.imported(path);record=result['files'][0]
        self.assertEqual(record['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(record['raster']['statistics'][2]['max'],2303)
        self.assertEqual(record['raster']['common_valid_pixels'],768)
        self.assertTrue(record['raster']['all_blocks_read'])

    def test_large_metadata_inspection_is_not_specialist_compatibility(self):
        path=raster(self.root/'large.tif',np.zeros((1,1200,1300),dtype='uint8'))
        result=self.imported(path)
        report=preflight(result,assets={k:dict(status='checks_passed_inference_unverified') for k in REGISTRY})
        self.assertFalse(report['eligible_specialists'])
        self.assertEqual(result['files'][0]['raster']['max_read_window'],[256,256,1])

    def test_disguised_and_truncated_tiffs_retained_as_failures(self):
        for name,raw in [('fake.tif',b'not a TIFF'),('broken.tif',b'II*\0'+b'\0'*10)]:
            with self.subTest(name=name):
                path=self.root/name;path.write_bytes(raw);value=self.imported(path)
                self.assertEqual(value['state'],'INSPECTED_WITH_FAILURES')
                self.assertEqual(value['files'][0]['state'],'REJECTED')
                self.assertTrue((self.store.directory(value['id'])/value['files'][0]['path']).exists())

    def test_nan_nodata_denominator(self):
        values=np.array([[[1,np.nan],[np.inf,-9999]]],dtype='float32')
        path=raster(self.root/'invalid.tif',values,nodata=-9999)
        result=inspect_raster(path)
        self.assertEqual(result['common_valid_pixels'],1)
        self.assertEqual(result['statistics'][0]['nan'],1)
        self.assertEqual(result['statistics'][0]['infinity'],1)

    def test_missing_crs_and_singular_transform_reported(self):
        from affine import Affine
        path=raster(self.root/'missing.tif',crs=None,transform=Affine(0,0,0,0,0,0))
        value=inspect_raster(path)
        self.assertIsNone(value['crs']);self.assertFalse(value['georeferencing_valid'])
        # GDAL replaces an absent/all-zero transform with identity. Test a retained singular matrix separately.
        path=raster(self.root/'singular.tif',transform=Affine(10,1,300000,20,2,3100000))
        self.assertFalse(inspect_raster(path)['valid_transform'])

    def test_zip_traversal_rejected(self):
        path=self.root/'bad.zip'
        with zipfile.ZipFile(path,'w') as z:z.writestr('../escape.tif',b'abc')
        value=self.store.create('bad zip');self.store.import_local(value['id'],path)
        with self.assertRaisesRegex(DataError,'traversal'):inspect_dataset(self.store,value['id'])
        self.assertFalse((self.root/'escape.tif').exists())

    def test_zip_symlink_rejected(self):
        path=self.root/'link.zip';info=zipfile.ZipInfo('link.tif');info.create_system=3;info.external_attr=(stat.S_IFLNK|0o777)<<16
        with zipfile.ZipFile(path,'w') as z:z.writestr(info,'/etc/passwd')
        value=self.store.create('link');self.store.import_local(value['id'],path)
        with self.assertRaisesRegex(DataError,'links'):inspect_dataset(self.store,value['id'])

    def test_zip_ratio_rejected_before_extracting(self):
        path=self.root/'bomb.zip'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('zeros.tif',b'0'*1024*1024)
        value=self.store.create('ratio');self.store.import_local(value['id'],path)
        with self.assertRaisesRegex(DataError,'ratio'):inspect_dataset(self.store,value['id'])

    def test_valid_zip_preserves_archive_and_member_hashes(self):
        source=raster(self.root/'a.tif');path=self.root/'valid.zip'
        with zipfile.ZipFile(path,'w') as z:z.write(source,'nested/a.tif')
        result=self.imported(path);self.assertEqual(len(result['files']),2)
        self.assertEqual(result['files'][1]['sha256'],digest(source))

    def test_cancel_partial_upload_preserves_completed_original(self):
        value=self.store.create('partial');row=self.store.register_file(value['id'],'a.tif',20)
        _,part=self.store.upload_target(value['id'],row['id'],0);part.write_bytes(b'abc')
        with self.assertRaisesRegex(DataError,'byte 3'):self.store.upload_target(value['id'],row['id'],0)
        self.store.cancel_uploads(value['id']);self.assertFalse(part.exists())

    def test_completed_original_cannot_be_overwritten(self):
        value=self.store.create('immutable');row=self.store.register_file(value['id'],'a.txt',3)
        _,part=self.store.upload_target(value['id'],row['id'],0);part.write_bytes(b'abc');self.store.finish_file(value['id'],row['id'])
        with self.assertRaisesRegex(DataError,'overwritten'):self.store.upload_target(value['id'],row['id'],0)

    def test_cap_and_disk_space(self):
        value=self.store.create('caps')
        with self.assertRaises(DataError):self.store.register_file(value['id'],'big.tif',self.store.cap+1)
        with patch('paired_lab.external_data.common.shutil.disk_usage') as usage:
            usage.return_value.free=1
            with self.assertRaisesRegex(DataError,'free disk'):self.store.register_file(value['id'],'a.tif',100)

    def test_expected_hash_mismatch_retained(self):
        value=self.store.create('hash');row=self.store.register_file(value['id'],'a.txt',3,expected_sha256='0'*64)
        _,part=self.store.upload_target(value['id'],row['id'],0);part.write_bytes(b'abc');self.store.finish_file(value['id'],row['id'])
        result=inspect_dataset(self.store,value['id'])
        self.assertEqual(result['failures'][0]['code'],'DATASET_HASH_MISMATCH')

    def test_inspection_cancellation_and_recovery(self):
        source=raster(self.root/'a.tif');value=self.store.create('cancel');self.store.import_local(value['id'],source)
        def cancel():raise DataError('CANCELLED','Operator cancelled')
        with self.assertRaises(DataError):inspect_dataset(self.store,value['id'],cancel)
        self.assertEqual(self.store.get(value['id'])['state'],'CANCELLED')
        self.assertEqual(inspect_dataset(self.store,value['id'])['state'],'INSPECTED')

    def test_complete_water_mismatch_report_not_first_failure(self):
        values=np.ones((3,64,64),dtype='uint8');path=raster(self.root/'wrong.tif',values,['VH','VV','unknown'],dict(sensor='Sentinel-2 L2A',units='linear'))
        value=self.imported(path);report=preflight(value,assets={k:dict(status='blocked') for k in REGISTRY})
        water=next(r for r in report['specialists'] if r['specialist']=='water_map')
        parameters={r['parameter'].split('.')[-1] for r in water['blocking_reasons']}
        self.assertTrue({'input_count','band_order','sensor_product','units','checkpoint_dimensions','assets'}.issubset(parameters))
        self.assertFalse(water['eligible']);self.assertEqual(len(report['specialists']),10)

    def test_correct_ndvi_contract_eligible_without_fake_accuracy(self):
        path=raster(self.root/'ndvi.tif',np.ones((2,8,8),dtype='float32')*.2,['red','nir'],dict(reflectance_units='surface_reflectance'))
        report=preflight(self.imported(path),assets={k:dict(status='checks_passed_inference_unverified') for k in REGISTRY})
        self.assertIn('ndvi',report['eligible_specialists'])
        ndvi=next(r for r in report['specialists'] if r['specialist']=='ndvi')
        self.assertEqual(next(r for r in ndvi['parameters'] if r['parameter']=='evaluation.ground_truth')['status'],'MISSING')

    def test_known_confusion(self):
        p=raster(self.root/'p.tif',np.array([[1,1,1],[0,0,0]],dtype='uint8'))
        r=raster(self.root/'r.tif',np.array([[1,1,0],[1,0,0]],dtype='uint8'))
        result=evaluate(p,r,protocol());water=result['per_class'][1]
        self.assertEqual([water[k] for k in ['TP','FP','TN','FN']],[2,1,2,1])
        self.assertEqual(water['IoU'],.5);self.assertAlmostEqual(water['F1'],2/3);self.assertEqual(result['denominator'],6)

    def test_perfect_and_all_false_positives_negatives(self):
        r=raster(self.root/'r.tif',np.array([[0,1],[0,1]],dtype='uint8'))
        for i,(values,tp,fp,fn) in enumerate([([[0,1],[0,1]],2,0,0),([[1,1],[1,1]],2,2,0),([[0,0],[0,0]],0,0,2)]):
            p=raster(self.root/f'p{i}.tif',np.array(values,dtype='uint8'));row=evaluate(p,r,protocol())['per_class'][1]
            self.assertEqual((row['TP'],row['FP'],row['FN']),(tp,fp,fn))

    def test_ignore_and_nodata_excluded(self):
        p=raster(self.root/'p.tif',np.array([[0,1],[0,255]],dtype='uint8'),nodata=255)
        r=raster(self.root/'r.tif',np.array([[0,1],[255,1]],dtype='uint8'))
        result=evaluate(p,r,protocol());self.assertEqual(result['denominator'],2);self.assertEqual(result['coverage_fraction'],.5)

    def test_no_valid_pixels_no_zero_accuracy(self):
        p=raster(self.root/'p.tif',np.full((2,2),255,dtype='uint8'),nodata=255);r=raster(self.root/'r.tif')
        r=raster(self.root/'r.tif',np.zeros((2,2),dtype='uint8'))
        with self.assertRaisesRegex(DataError,'undefined'):evaluate(p,r,protocol())

    def test_label_alignment_and_class_mismatch(self):
        p=raster(self.root/'p.tif');r=raster(self.root/'r.tif',transform=from_origin(300010,3100000,10,10))
        with self.assertRaisesRegex(DataError,'must match'):evaluate(p,r,protocol())
        r=raster(self.root/'r.tif',np.full((2,3),9,dtype='uint8'))
        with self.assertRaisesRegex(DataError,'Unmapped'):evaluate(p,r,protocol())

    def test_missing_labels_never_score(self):
        result=evaluate(None,None,{})
        self.assertEqual(result['code'],'COMPATIBLE_GROUND_TRUTH_NOT_PROVIDED');self.assertNotIn('accuracy',result)

    def test_classification_vqa_and_multilabel_protocols(self):
        p=self.root/'p.csv';r=self.root/'r.csv';spec=protocol('classification');spec['scene_ids']=['a','b']
        p.write_text('case_id,label\na,0\nb,1\n');r.write_text('case_id,label\na,1\nb,1\n')
        self.assertEqual(table_metrics(p,r,spec)['accuracy'],.5)
        spec.update(task='vqa',answer_normalization='casefold_whitespace')
        p.write_text('case_id,answer\na, YES \nb,no\n');r.write_text('case_id,answer\na,yes\nb,yes\n')
        self.assertEqual(table_metrics(p,r,spec)['exact_match'],.5)
        spec.update(task='multilabel');p.write_text('case_id,class_name,value\na,0,1\na,1,0\nb,0,0\nb,1,1\n');r.write_text('case_id,class_name,value\na,0,1\na,1,1\nb,0,0\nb,1,1\n')
        self.assertEqual(table_metrics(p,r,spec)['micro']['F1'],.8)

    def test_reference_population_cannot_silently_drop_cases(self):
        p=self.root/'p.csv';r=self.root/'r.csv';p.write_text('case_id,answer\na,yes\n');r.write_text('case_id,answer\na,yes\nb,no\n')
        spec=protocol('vqa');spec.update(answer_normalization='exact',scene_ids=['a','b'])
        with self.assertRaisesRegex(DataError,'No silent dropping'):table_metrics(p,r,spec)

    def test_export_recomputes_metrics_and_detects_tampering(self):
        from paired_lab.external_data.runner import run,verify
        value=self.store.create('Known answer export')
        p=raster(self.root/'p.tif',np.array([[1,1,1],[0,0,0]],dtype='uint8'))
        r=raster(self.root/'r.tif',np.array([[1,1,0],[1,0,0]],dtype='uint8'))
        self.store.import_local(value['id'],p,'prediction');self.store.import_local(value['id'],r,'reference')
        value=inspect_dataset(self.store,value['id']);spec=protocol();spec['dataset_revision']=value['revision']
        params=dict(prediction_id=value['files'][0]['id'],reference_id=value['files'][1]['id'],protocol=spec)
        out=self.root/'immutable'
        with patch('paired_lab.external_data.runner.asset_inventory',return_value={}):result=run(self.store,value['id'],out,params)
        self.assertEqual(result['state'],'EVALUATED');self.assertTrue(verify(out)['metrics_recomputed'])
        with self.assertRaisesRegex(DataError,'never overwritten'):run(self.store,value['id'],out,params)
        with (out/'metrics.json').open('a') as stream:stream.write(' ')
        with self.assertRaisesRegex(DataError,'differs'):verify(out)

    def test_no_label_ndvi_execution_exports_no_accuracy(self):
        from paired_lab.external_data.runner import run,verify
        values=np.array([[[.1,.3],[.2,.2]],[[.7,.3],[.6,.2]]],dtype='float32')
        source=raster(self.root/'ndvi.tif',values,['red','nir'],dict(reflectance_units='surface_reflectance'))
        value=self.imported(source);out=self.root/'prediction-only'
        with patch('paired_lab.external_data.runner.asset_inventory',return_value={'ndvi':dict(status='checks_passed_inference_unverified',assets=[])}):
            result=run(self.store,value['id'],out,dict(specialist='ndvi',threshold=.5))
        self.assertEqual(result['state'],'EVALUATION_NOT_POSSIBLE');self.assertNotIn('accuracy',result['metrics'])
        with rasterio.open(out/'predicted_mask.tif') as ds:self.assertEqual(ds.read(1).tolist(),[[1,0],[1,0]])
        self.assertFalse(verify(out)['metrics_recomputed'])

    def test_changed_dataset_refuses_execution(self):
        from paired_lab.external_data.runner import run
        source=raster(self.root/'data.tif');value=self.imported(source)
        path=self.store.directory(value['id'])/value['files'][0]['path']
        with path.open('ab') as stream:stream.write(b'tamper')
        with patch('paired_lab.external_data.runner.asset_inventory',return_value={}):result=run(self.store,value['id'],self.root/'failure',dict(specialist='water_map'))
        self.assertEqual(result['failures'][0]['code'],'DATASET_HASH_MISMATCH')

    def test_protocol_revision_cannot_be_changed_after_labels(self):
        from paired_lab.external_data.runner import run
        value=self.imported(raster(self.root/'source.tif'))
        with self.assertRaisesRegex(DataError,'revision'):run(self.store,value['id'],self.root/'bad',dict(protocol=protocol()))

    def test_real_isolated_worker_cancel_and_competing_jobs(self):
        from paired_lab.external_data.service import Service
        service=Service(self.root/'service')
        try:
            value=service.store.create('Owned worker cancellation');service.store.import_local(value['id'],raster(self.root/'source.tif'))
            job=service.submit(value['id'],'inspect',{})
            with self.assertRaisesRegex(DataError,'already active'):service.submit(value['id'],'inspect',{})
            for _ in range(100):
                if service.process is not None:break
                time.sleep(.01)
            process=service.process;self.assertIsNotNone(process)
            service.cancel(job['id'])
            for _ in range(200):
                if service.get(job['id'])['state']=='CANCELLED' and service.active is None:break
                time.sleep(.01)
            self.assertEqual(service.get(job['id'])['state'],'CANCELLED');self.assertIsNotNone(process.poll())
        finally:service.close()

    def test_worker_recovery_does_not_report_success(self):
        from paired_lab.external_data.service import Service
        from paired_lab.external_data.common import write_json
        root=self.root/'recovery';folder=root/'jobs'/('a'*32);folder.mkdir(parents=True)
        write_json(folder/'job.json',dict(id='a'*32,state='RUNNING'))
        service=Service(root)
        try:self.assertEqual(service.get('a'*32)['state'],'INTERRUPTED')
        finally:service.close()


if __name__=='__main__':unittest.main()
