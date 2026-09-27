"""Calibrate a native central crop of the verified public EOS-04 FRS2 sample."""
import sys,json,hashlib,zipfile,argparse
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paired_lab.eos04_calibration import beta0

def prepare(archive,out):
 archive=Path(archive).resolve();out=Path(out);out.mkdir(parents=True,exist_ok=True)
 with archive.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
 if digest!='f3bc18aa114030325803fb60778821b7835d0cd4773ed77c4fd3964ea5e08752':raise ValueError('Only the verified official FRS2 archive is supported.')
 rows=[];linear=[];db=[];signature=None
 with zipfile.ZipFile(archive) as z:
  if z.testzip():raise ValueError('Archive CRC failure.')
  name=next(n for n in z.namelist() if n.upper().endswith('BAND_META.TXT'))
  text=z.read(name).decode();tags=dict(line.split('=',1) for line in text.splitlines() if '=' in line)
  (out/'BAND_META.txt').write_text(text)
  for pol in ['HH','HV','VH','VV']:
   member=next(n for n in z.namelist() if Path(n).name.lower()==f'imagery_{pol.lower()}.tif')
   with rasterio.open('/vsizip/'+archive.as_posix()+'/'+member) as ds:
    current=(ds.crs,ds.transform,ds.width,ds.height)
    if signature is None:signature=current
    if signature!=current:raise ValueError('Polarization grids differ.')
    window=Window(ds.width//2-256,ds.height//2-256,512,512)
    dn=ds.read(1,window=window);k=float(tags['Calibration_Constant_Beta0_'+pol]);n=float(tags['Image_Noise_Bias_'+pol])
    a,b=beta0(dn,k,n)
    # Native zero samples are not treated as positive measured returns.
    a[dn==0]=np.nan;b[dn==0]=np.nan
    linear.append(a);db.append(b)
    # Independently recompute a positive pixel in scalar arithmetic.
    valid=np.argwhere((dn>0)&np.isfinite(b))
    y,x=valid[0];expected=(float(dn[y,x])**2-n)/(10**(k/10))
    assert abs(float(a[y,x])-expected)<1e-12
    rows.append({'polarization':pol,'member':member,'beta0_constant_db':k,'noise_bias':n,'native_zero_pixels':int((dn==0).sum()),'nonpositive_corrected_pixels':int(((a<=0)&np.isfinite(a)).sum()),'positive_pixels':int(np.isfinite(b).sum()),'db_percentiles_2_50_98':np.nanpercentile(b,[2,50,98]).tolist(),'scalar_check':{'pixel':[int(y),int(x)],'dn':int(dn[y,x]),'beta0':expected}})
    profile=ds.profile.copy();profile.update(count=4,width=512,height=512,transform=ds.window_transform(window),dtype='float32',nodata=np.nan,compress='deflate')
 for name,data,units in [('beta0-linear.tif',linear,'linear signed beta0'),('beta0-db.tif',db,'dB beta0; nonpositive power invalid')]:
  with rasterio.open(out/name,'w',**profile) as dst:
   dst.write(np.asarray(data,dtype='float32'))
   for i,pol in enumerate(['HH','HV','VH','VV'],1):dst.set_band_description(i,pol)
   dst.update_tags(sensor='EOS-04',product_id='237516861',units=units,source_sha256=digest,formula='(DN^2 - Image_Noise_Bias) / 10^(Calibration_Constant_Beta0/10)',scope='Calibration only; not Sentinel model input; no semantic inference')
 report={'source_sha256':digest,'reference':'https://bhoonidhi.nrsc.gov.in/bhoonidhi_resources/help/docs/EOS-04_Handbook.pdf','reference_pages':'printed 66-68 / PDF 77-79','window':list(window.flatten()),'bands':rows,'outputs':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ['beta0-linear.tif','beta0-db.tif']},'limits':['Beta0 is not sigma0. No terrain flattening, speckle filtering or semantic inference performed.','Native-zero exclusion is an explicit conservative policy; original sample has no TIFF nodata tag.','Signed nonpositive linear power retained; dB undefined there.','Independent numerical checks do not validate physical calibration against field reference targets.']}
 (out/'calibration.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('out');a=p.parse_args();prepare(a.archive,a.out)
