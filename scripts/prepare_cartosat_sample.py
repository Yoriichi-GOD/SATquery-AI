"""Prepare the verified NRSC Cartosat-2E sample for optical display/VQA.
This is an explicit sample preparation tool, not a general sensor importer.
"""
import argparse, hashlib, json, zipfile
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window

EXPECTED='2614599a9a22d56fa12da238e40040f8d57f3526c03e19e9596e49c2c228ddb1'
REFERENCE='https://bhuvan-app3.nrsc.gov.in/nhai_gci/files/NRSC_NH-GCI_FinalReport_09Dec2025.pdf'

def prepare(archive, output):
    archive=Path(archive).resolve();output=Path(output)
    with archive.open('rb') as source:
        digest=hashlib.file_digest(source,'sha256').hexdigest()
    if digest!=EXPECTED:raise ValueError('Only the verified official Cartosat-2E sample archive is supported.')
    arrays=[];members=[];baseline=None
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('Corrupt sample archive.')
        for i in range(1,5):
            candidates=[n for n in z.namelist() if Path(n).name.upper()==f'BAND{i}.TIF']
            if len(candidates)!=1:raise ValueError('Expected exactly one TIFF for each official band.')
            member=candidates[0];members.append(member)
            with rasterio.open('/vsizip/'+archive.as_posix()+'/'+member) as ds:
                signature=(ds.crs,ds.transform,ds.width,ds.height,ds.count,ds.dtypes,ds.nodata)
                if baseline is None:
                    baseline=signature;window=Window(ds.width//2-256,ds.height//2-256,512,512)
                    profile=ds.profile.copy();profile.update(count=4,width=512,height=512,transform=ds.window_transform(window),compress='deflate')
                if signature!=baseline:raise ValueError('Band grids or data types differ.')
                arrays.append(ds.read(1,window=window))
    output.parent.mkdir(parents=True,exist_ok=True)
    with rasterio.open(output,'w',**profile) as dst:
        dst.write(np.stack(arrays))
        for i,name in enumerate(['blue','green','red','nir'],1):dst.set_band_description(i,name)
        dst.update_tags(sensor='CARTOSAT-2E',units='DN',acquired='2020-05-16',source_item='205132611',source_archive_sha256=digest,attribution='NRSC Bhoonidhi public sample',band_reference=REFERENCE,calibration_version='native DN; no radiometric conversion')
    with rasterio.open(output) as ds:
        if not np.array_equal(ds.read(),np.stack(arrays)):raise AssertionError('Native values changed.')
    manifest={'source_archive_sha256':digest,'source_members':members,'window':list(window.flatten()),'band_reference':REFERENCE,'reference_table':'Table 4, printed page 6 / PDF page 30','bands':['blue','green','red','nir'],'preparation':'Native central 512 pixel window; stack and label only. No resampling or calibration.','output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'scope':'Optical display/VQA input preparation only. No sensor accuracy or calibrated NDVI claim.'}
    output.with_suffix('.json').write_text(json.dumps(manifest,indent=2))
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('output');a=p.parse_args();print(json.dumps(prepare(a.archive,a.output),indent=2))
