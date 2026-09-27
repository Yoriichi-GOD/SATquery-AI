import io,json,re,hashlib,random,zipfile
from pathlib import Path
import requests
ROOT=Path('/mnt/c/Users/nrgen/.codex/scratch/SATquery AI')
OUT=ROOT/'paired_lab/evidence/cdvqa-20260927';OUT.mkdir(exist_ok=True)
REV='cc5893123dd32326de38745b65d2ffe45055937b'
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2))
for name in ['Test_images.json','Test_answers.json','README.md','LICENSE']:
    r=requests.get(f'https://raw.githubusercontent.com/YZHJessica/CDVQA/{REV}/{name}',timeout=45);r.raise_for_status();(OUT/name).write_bytes(r.content)
images=json.loads((OUT/'Test_images.json').read_text())['images']
print('Image schema',images[:3],flush=True)
s=requests.Session();t=s.get('https://drive.google.com/uc?export=download&id=1mN8jzCKKK27p3ODGoDgepjiRYGQpB34u',timeout=30).text
params=dict(re.findall(r'name="([^"]+)" value="([^"]*)"',t))
class Remote(io.RawIOBase):
    def __init__(self):
        self.pos=0;self.bytes=0
        r=s.get('https://drive.usercontent.google.com/download',params=params,headers={'Range':'bytes=-65536'},timeout=60)
        r.raise_for_status();assert r.status_code==206
        self.size=int(r.headers['Content-Range'].split('/')[-1]);self.modified=r.headers.get('Last-Modified')
    def seekable(self):return True
    def tell(self):return self.pos
    def seek(self,n,whence=0):self.pos=n if whence==0 else self.pos+n if whence==1 else self.size+n;return self.pos
    def read(self,n=-1):
        n=min(n if n>=0 else self.size-self.pos,self.size-self.pos)
        if n<=0:return b''
        p={**params,'range_start':str(self.pos),'range_end':str(self.pos+n-1)}
        r=s.get('https://drive.usercontent.google.com/download',params=p,headers={'Range':f'bytes={self.pos}-{self.pos+n-1}'},timeout=90)
        r.raise_for_status()
        expected=f'bytes {self.pos}-{self.pos+n-1}/{self.size}'
        if r.status_code!=206 or r.headers.get('Content-Range')!=expected or len(r.content)!=n:raise ValueError('Range mismatch')
        self.pos+=n;self.bytes+=n;return r.content
remote=Remote()
with zipfile.ZipFile(remote) as z:
    inventory=[dict(name=i.filename,size=i.file_size,crc=i.CRC,compressed=i.compress_size) for i in z.infolist()]
    save('archive-inventory.json',inventory)
    print('Inventory',len(inventory),[x['name'] for x in inventory[:15]],flush=True)
save('source.json',dict(label_revision=REV,archive_url='https://drive.google.com/file/d/1mN8jzCKKK27p3ODGoDgepjiRYGQpB34u/view',author_page='https://captain-whu.github.io/SCD/',archive_bytes=remote.size,last_modified=remote.modified,downloaded_bytes=remote.bytes,label_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('Test_*.json')},scope='Inventory only; selected archive entries must be CRC-verified when downloaded. Entire archive not downloaded or hashed.'))
