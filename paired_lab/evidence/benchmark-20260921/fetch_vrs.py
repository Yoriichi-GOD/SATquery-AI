from pathlib import Path
import io,requests,zipfile,json,random,hashlib,time
O=Path(__file__).resolve().parent
class Remote(io.RawIOBase):
 def __init__(self,url,size):self.url=url;self.size=size;self.pos=0
 def seekable(self):return True
 def tell(self):return self.pos
 def seek(self,n,whence=0):
  self.pos=n if whence==0 else self.pos+n if whence==1 else self.size+n
  return self.pos
 def read(self,n=-1):
  n=min(n if n>=0 else self.size-self.pos,self.size-self.pos)
  if n<=0:return b''
  # Distinct request URL avoids cached redirects binding a different Range.
  r=requests.get(self.url+'?download=true&range_start='+str(self.pos),headers={'Range':f'bytes={self.pos}-{self.pos+n-1}'},timeout=90)
  r.raise_for_status()
  if r.status_code!=206 or len(r.content)!=n:raise ValueError('Server did not honor bounded range request')
  self.pos+=n;return r.content
d=json.loads((O/'vrs-source.json').read_text());size=next(r['size'] for r in json.loads((O/'vrs-files.json').read_text()) if r['path']=='Images_val.zip')
with zipfile.ZipFile(Remote(d['base']+'Images_val.zip',size)) as z:
 mapping={Path(n).name:n for n in z.namelist() if n.endswith('.png')};cases=json.loads((O/'vrs-captions.json').read_text());random.Random(20260921).shuffle(cases);selected=[];seen=set();dest=O/'vrs-inputs';dest.mkdir(exist_ok=True)
 for c in cases:
  scene=c['image_id'].split('_')[0]
  if scene in seen or c['image_id'] not in mapping:continue
  seen.add(scene);selected.append(c)
  if len(selected)==12:break
 (O/'vrs-manifest.json').write_text(json.dumps({'revision':d['revision'],'seed':20260921,'cases':selected,'scope':'12 official evaluation captions with distinct filename scene prefixes; frozen before inference. Upstream checkpoint exposure unknown; exploratory description evaluation.'},indent=2))
 for c in selected:
  p=dest/c['image_id'];p.write_bytes(z.read(mapping[c['image_id']]));c['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();print(c['image_id'],flush=True)
 (O/'vrs-input-hashes.json').write_text(json.dumps(selected,indent=2))
