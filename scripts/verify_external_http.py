"""Bounded local HTTP readiness checks with synthetic fixtures, never a scientific benchmark."""
import argparse,json,tempfile,time
from pathlib import Path
import numpy as np
import rasterio
import requests
from rasterio.transform import from_origin


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base',default='http://127.0.0.1:8768');parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    from urllib.parse import urlsplit
    origin=urlsplit(args.base)
    if origin.scheme!='http' or origin.hostname not in ('127.0.0.1','localhost','::1') or origin.username or origin.password or origin.query or origin.fragment or origin.path not in ('','/'):
        raise ValueError('Readiness checks accept an explicit loopback HTTP origin only.')
    if args.output.exists():raise ValueError('Choose a new receipt path; existing evidence is immutable.')
    base=args.base.rstrip('/')+'/api/datasets';session=requests.Session();checks=[];retained=[]
    def check(name,condition,detail=None):
        if not condition:raise AssertionError(name+': '+str(detail))
        checks.append(dict(check=name,result='PASS',detail=detail))
    def call(method,path,expected=200,**kwargs):
        response=session.request(method,base+path,timeout=60,**kwargs)
        if response.status_code!=expected:raise AssertionError(str(response.status_code)+' '+response.text[:500])
        return response.json()
    def wait(job):
        for _ in range(600):
            value=call('GET','/jobs/'+job['id'])
            if value['state'] in ('COMPLETE','EVALUATED','EVALUATION_NOT_POSSIBLE','PROCESSING_FAILED','CANCELLED','INTERRUPTED'):return value
            time.sleep(.1)
        raise RuntimeError('HTTP fixture operation timed out')
    def create(name):
        value=call('POST','',expected=201,json=dict(name='SYNTHETIC HTTP QA · '+name));retained.append(value['id']);return value['id']
    def upload(did,path):
        row=call('POST','/'+did+'/files',expected=201,json=dict(name=path.name,size=path.stat().st_size,role='input'));offset=0
        with path.open('rb') as stream:
            while chunk:=stream.read(1024**2):
                call('PUT','/'+did+'/files/'+row['id']+'/content?offset='+str(offset),data=chunk);offset+=len(chunk)
        call('POST','/'+did+'/files/'+row['id']+'/finish');return row['id']
    foreign=session.get(base,headers={'Origin':'http://untrusted.example'},timeout=10)
    check('foreign browser origin refused',foreign.status_code==403)
    did=create('bounded chunk rollback');fid=call('POST','/'+did+'/files',expected=201,json=dict(name='partial.txt',size=9*1024**2,role='metadata'))['id']
    call('PUT','/'+did+'/files/'+fid+'/content?offset=0',data=b'prefix')
    wrong=call('PUT','/'+did+'/files/'+fid+'/content?offset=0',expected=409,data=b'wrong')
    check('wrong resume offset refused',wrong['code']=='OFFSET_MISMATCH')
    oversized=call('PUT','/'+did+'/files/'+fid+'/content?offset=6',expected=413,data=b'x'*(8*1024**2+1))
    check('oversized chunk refused',oversized['code']=='CHUNK_LIMIT')
    inventory=call('GET','/'+did);check('failed chunk did not advance received bytes',inventory['files'][0]['received']==6)
    call('POST','/'+did+'/cancel-upload');check('partial upload cancel recorded',call('GET','/'+did)['files'][0]['state']=='CANCELLED')
    restarted=call('POST','/'+did+'/files/'+fid+'/restart');check('incomplete file explicitly restarts',restarted['received']==0 and restarted['state']=='UPLOADING')
    call('POST','/'+did+'/cancel-upload')
    with tempfile.TemporaryDirectory(prefix='satquery-http-fixture-') as temporary:
        folder=Path(temporary);bad=folder/'disguised.tif';bad.write_bytes(b'not a TIFF')
        did=create('corrupt TIFF refusal');fid=upload(did,bad);job=wait(call('POST','/'+did+'/inspect',expected=202,json={'full_scan':True}))
        file=call('GET','/'+did)['files'][0];check('corrupt TIFF retained as explicit failure',job['state']=='COMPLETE' and file['error']['code']=='NOT_A_TIFF')
        refused=wait(call('POST','/'+did+'/analyze',expected=202,json=dict(specialist='water_map',inputs=[fid])))
        check('incompatible specialist refused before inference',refused['state']=='PROCESSING_FAILED' and refused['result']['failures'][0]['code']=='INCOMPATIBLE_INPUT')
        manifest=session.get(base+'/jobs/'+refused['id']+'/export/model_manifest.json',timeout=10).json()
        check('no incompatible checkpoint loaded',manifest['status']=='not executed')
        source=folder/'known-ndvi.tif';values=np.stack([np.full((32,32),.1),np.full((32,32),.7)]).astype('float32')
        with rasterio.open(source,'w',driver='GTiff',width=32,height=32,count=2,dtype='float32',crs='EPSG:32645',transform=from_origin(300000,3100000,10,10)) as ds:
            ds.write(values);ds.set_band_description(1,'red');ds.set_band_description(2,'nir');ds.update_tags(reflectance_units='surface_reflectance',purpose='SYNTHETIC numerical software QA; not satellite observations.')
        did=create('prediction-only arithmetic');fid=upload(did,source);wait(call('POST','/'+did+'/inspect',expected=202,json={'full_scan':True}))
        run=wait(call('POST','/'+did+'/analyze',expected=202,json=dict(specialist='ndvi',inputs=[fid],threshold=.5)))
        check('supported numerical execution returned actual result',run['result']['analysis_result']['statistics']['selected_pixels']==1024)
        check('no labels never becomes an accuracy score',run['state']=='EVALUATION_NOT_POSSIBLE' and not any(k in run['result']['metrics'] for k in ('accuracy','IoU','F1')))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    receipt=dict(scope='Synthetic HTTP correctness and failure tests; no scientific performance claim.',checks=checks,passed=len(checks),retained_private_datasets=retained)
    args.output.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
