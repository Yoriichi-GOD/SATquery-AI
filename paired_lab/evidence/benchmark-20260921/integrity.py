import sys,json,zipfile,io,tempfile,hashlib
from pathlib import Path
import numpy as np,rasterio
from PIL import Image
O=Path(__file__).resolve().parent;R=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI');sys.path.insert(0,str(R/'paired_lab'));import engine,flood,registration,controller,spectral_pair
checks=[]
for row in json.loads((O/'workflow-gates.json').read_text()):
 d=row['run'];r=d.get('result',{});kind=row['kind'];z=zipfile.ZipFile(O/'live-artifacts'/(r['id']+'.zip'));ok=z.testzip() is None
 if kind=='water_map':
  a=np.load(io.BytesIO(z.read('water-scores.npz')));ok&=all(int(((a[m]>=.5)&a['valid']).sum())==r['water_pixels'][m] for m in ['s1','s2','all'])
 elif kind=='temporal':
  a=np.load(io.BytesIO(z.read('scores.npz')));print('temporal export keys',a.files,flush=True)
  mask=a['classes'];ok&=int((mask>0).sum())==r['changed_pixels']
 elif kind=='ndvi':
  with rasterio.open(O/'ndvi-input.tif') as ds:
   names={n.lower():i for i,n in enumerate(ds.descriptions,1)};red=ds.read(names['red']).astype('float64')*ds.scales[names['red']-1]+ds.offsets[names['red']-1];nir=ds.read(names['nir']).astype('float64')*ds.scales[names['nir']-1]+ds.offsets[names['nir']-1];valid=np.isfinite(red)&np.isfinite(nir)&(red>=0)&(nir>=0)&((red+nir)>1e-8)
   if 'scl' in names:valid&=np.isin(ds.read(names['scl']),[4,5,6,7])
   expected=np.full(red.shape,np.nan);expected[valid]=(nir[valid]-red[valid])/(nir[valid]+red[valid]);selected=(expected>=r['statistics']['threshold'])&valid
   with rasterio.MemoryFile(z.read('ndvi.tif')) as mem,mem.open() as result:np.testing.assert_allclose(result.read(1)[valid],expected[valid],rtol=0,atol=1e-12)
   ok&=int(selected.sum())==r['statistics']['selected_pixels'];ok&=abs(selected.sum()*abs(ds.transform.a*ds.transform.e-ds.transform.b*ds.transform.d)-r['statistics']['selected_area_m2'])<1e-6
 checks.append({'kind':kind,'numerical_and_archive_check':bool(ok)})
with tempfile.TemporaryDirectory() as td:
 try:flood.load(checkpoint=Path(td)/'absent.pt');missing=False
 except ValueError:missing=True
checks.append({'missing_water_checkpoint_refused':missing})
sample=next((O/'temporal-examples').glob('*/before.png'));a=np.asarray(Image.open(sample));checks.append({'registration_identical':registration.diagnose(a,a),'registration_shift_8_pixels':registration.diagnose(a,np.roll(a,8,axis=1)),'registration_blank':registration.diagnose(np.zeros_like(a),np.ones_like(a)*20)})
single={'modality':'optical','width':256,'height':256,'count':3};spectral=[{**single,'reflectance_units':'surface_reflectance'}]*2;water=[{**single,'count':13},{'modality':'sar','count':2}];land=[{**single,'count':10},{'modality':'sar','count':2}]
heldout=[('What is the water depth?', [single],'refuse'),('Does this image contain a water area?',[single],'vqa'),('Is a grass area visible?',[single],'vqa'),('Estimate soil moisture',[single],'refuse'),('Compare water and rainfall',spectral,'refuse'),('Compare vegetation and population',spectral,'refuse'),('Map water and crops',water,'refuse'),('Identify building positions',land,'refuse'),('Compare buildings between these images',[single,single],'temporal'),('Measure water volume',water,'refuse'),('Identify land-cover classes',land,'optical_sar'),('Compare NDWI',spectral,'spectral_pair')]
for q,recs,expected in heldout:
 try:actual=controller.plan(q,recs)['task']
 except ValueError:actual='refuse'
 checks.append({'holdout_query':q,'expected':expected,'actual':actual,'pass':expected==actual})
(O/'integrity-results.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))

