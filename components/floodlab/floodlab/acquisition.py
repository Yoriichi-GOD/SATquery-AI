"""Authenticated provider access. Credentials stay in memory and never enter provenance."""
from pathlib import Path
import json,hashlib,time
import requests
TOKEN_URL='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
PROCESS_URL='https://sh.dataspace.copernicus.eu/api/v1/process'
class Provider:
 def __init__(self,config):
  self.config=Path(config);self.token=None;self.expires=0
 def authenticate(self):
  if self.token and time.monotonic()<self.expires:return
  values={}
  for line in self.config.read_text().splitlines():
   if '=' in line and not line.lstrip().startswith('#'):
    k,v=line.split('=',1);values[k.strip()]=v.strip().strip('\"').strip("'")
  if not all(values.get(k) for k in ('CDSE_CLIENT_ID','CDSE_CLIENT_SECRET')):raise ValueError('Copernicus API credentials are not configured')
  r=requests.post(TOKEN_URL,data={'grant_type':'client_credentials','client_id':values['CDSE_CLIENT_ID'],'client_secret':values['CDSE_CLIENT_SECRET']},timeout=30,allow_redirects=False)
  if r.status_code!=200:raise RuntimeError(f'Copernicus authentication HTTP {r.status_code}; credentials withheld')
  d=r.json();self.token=d['access_token'];self.expires=time.monotonic()+max(0,int(d.get('expires_in',300))-30)
 def process(self,request,destination,max_bytes=100_000_000):
  destination=Path(destination)
  if destination.exists():raise ValueError('Destination exists; preserve acquired evidence')
  self.authenticate()
  r=requests.post(PROCESS_URL,json=request,headers={'Authorization':'Bearer '+self.token,'Accept':'application/tar'},stream=True,timeout=(20,180),allow_redirects=False)
  if r.status_code!=200:raise RuntimeError(f'Copernicus processing HTTP {r.status_code}; no result accepted')
  destination.parent.mkdir(parents=True,exist_ok=True);temp=destination.with_suffix('.part');size=0
  try:
   with temp.open('wb') as f:
    for chunk in r.iter_content(1024*1024):
     size+=len(chunk)
     if size>max_bytes:raise ValueError('Processing response exceeds bounded download size')
     f.write(chunk)
   temp.replace(destination)
  finally:r.close()
  provenance={'provider':PROCESS_URL,'request':request,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'bytes':size,'content_type':r.headers.get('Content-Type')}
  destination.with_suffix('.provenance.json').write_text(json.dumps(provenance,indent=2))
  return {'bytes':size,'sha256':provenance['sha256']}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('request');p.add_argument('destination');a=p.parse_args();base=Path(__file__).resolve().parents[1]
 print(json.dumps(Provider(base/'.env.local').process(json.loads(Path(a.request).read_text()),a.destination)))
