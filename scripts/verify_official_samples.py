"""Independent verification of downloaded official sample artifacts."""
import argparse,json,hashlib,zipfile,sys
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'paired_lab')]
import geo,inputs,sar_single

def run(archives,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);archives=Path(archives);checks=[]
 def record(name,details):checks.append({'check':name,'status':'PASS',**details})
 def refuse(name,fn):
  try:fn()
  except ValueError as e:record(name,{'refusal':str(e)})
  else:raise AssertionError(name+' did not refuse')
 for name,expected in [('cartosat-mx.zip','2614599a9a22d56fa12da238e40040f8d57f3526c03e19e9596e49c2c228ddb1'),('eos04-frs2.zip','f3bc18aa114030325803fb60778821b7835d0cd4773ed77c4fd3964ea5e08752')]:
  p=archives/name
  with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
  assert digest==expected
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
  record(name+' integrity',{'sha256':digest,'bytes':p.stat().st_size})
 cart=ROOT/'paired_lab/evidence/compliance-20260926/cartosat-labelled.tif'
 manifest=json.loads(cart.with_suffix('.json').read_text())
 with zipfile.ZipFile(archives/'cartosat-mx.zip') as z,rasterio.open(cart) as ds:
  for i,member in enumerate(manifest['source_members'],1):
   with rasterio.open('/vsizip/'+str((archives/'cartosat-mx.zip').resolve())+'/'+member) as src:
    w=Window(*manifest['window']);assert np.array_equal(ds.read(i),src.read(1,window=w));assert ds.transform==src.window_transform(w);assert ds.crs==src.crs
 record('Cartosat native values and grid preserved',{'samples_compared':4*512*512})
 im,meta=geo.ingest(cart.read_bytes(),out/'cartosat-ingested.tif');im.save(out/'cartosat-preview.png');assert not meta['ndvi_supported']
 record('Cartosat RGB ingestion',{'bands':meta['bands'],'width':meta['width'],'height':meta['height']})
 refuse('Cartosat DN refused for NDVI',lambda:geo.analyse(cart,out/'invalid-ndvi'))
 caldir=ROOT/'paired_lab/evidence/official-20260927';report=json.loads((caldir/'calibration.json').read_text());rows=[]
 with rasterio.open(caldir/'beta0-linear.tif') as linear,rasterio.open(caldir/'beta0-db.tif') as db:
  for i,b in enumerate(report['bands'],1):
   with rasterio.open('/vsizip/'+str((archives/'eos04-frs2.zip').resolve())+'/'+b['member']) as src:
    w=Window(*report['window']);dn=src.read(1,window=w).astype('float64')
    # Independent calculation in power-of-e form; production uses power-of-ten.
    expected=(dn*dn-b['noise_bias'])*np.exp(-b['beta0_constant_db']*np.log(10)/10)
    expected[dn==0]=np.nan;actual=linear.read(i)
    np.testing.assert_allclose(actual,expected,rtol=1e-6,atol=1e-8,equal_nan=True)
    valid=expected>0;expected_db=np.full(expected.shape,np.nan);expected_db[valid]=np.log(expected[valid])*10/np.log(10)
    np.testing.assert_allclose(db.read(i),expected_db,rtol=1e-6,atol=1e-5,equal_nan=True)
    assert linear.transform==src.window_transform(w) and linear.crs==src.crs
    assert np.array_equal(np.isnan(db.read(i)),~valid)
    rows.append({'polarization':b['polarization'],'samples':dn.size,'max_linear_absolute_error':float(np.nanmax(abs(actual-expected))),'max_db_absolute_error':float(np.nanmax(abs(db.read(i)-expected_db))),'nonpositive':int(np.sum(expected<=0))})
 record('EOS-04 saved calibration independently recomputed',{'bands':rows,'total_samples':4*512*512,'linear_tolerance':'rtol 1e-6, atol 1e-8','db_tolerance':'rtol 1e-6, atol 1e-5'})
 refuse('EOS-04 four-band invalid dB raster refused by model ingestion',lambda:inputs.inspect(caldir/'beta0-db.tif','sar'))
 refuse('EOS-04 explicitly refused by Sentinel SAR specialist',lambda:sar_single.validate({'modality':'sar','sensor':'EOS-04','units':'dB'}))
 optical=inputs.inspect(cart,'optical');sar=inputs.inspect(archives/'eos04-frs2-native-crop.tif','sar')
 refuse('Unrelated official pair refused for water mapping',lambda:inputs.validate([optical,sar],'water_map'))

 result={'checks':checks,'passed':len(checks),'scope':'Official sample functional/numerical regression; not held-out accuracy evaluation'}
 (out/'checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('archives');p.add_argument('out');a=p.parse_args();run(a.archives,a.out)
