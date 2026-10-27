"""Bounded range-only metadata extraction from the official versioned archive."""
import io,json,zipfile,hashlib
from pathlib import Path
import requests

class Remote(io.RawIOBase):
    def __init__(self,url):
        self.url=url;self.pos=0;self.transferred=0
        with requests.get(url,headers={"Range":"bytes=0-0"},stream=True,timeout=30) as r:
            if r.status_code!=206:raise RuntimeError("Server does not honor ranges")
            self.size=int(r.headers["Content-Range"].split("/")[-1])
    def seekable(self):return True
    def tell(self):return self.pos
    def seek(self,n,whence=0):
        self.pos=n if whence==0 else self.pos+n if whence==1 else self.size+n
        return self.pos
    def read(self,n=-1):
        n=self.size-self.pos if n<0 else min(n,self.size-self.pos)
        if n==0:return b""
        if n>2**20 or self.transferred+n>16*2**20:raise RuntimeError("Metadata byte budget exceeded")
        start=self.pos
        with requests.get(self.url,headers={"Range":f"bytes={start}-{start+n-1}"},stream=True,timeout=30) as r:
            if r.status_code!=206 or not r.headers.get("Content-Range","").startswith(f"bytes {start}-"):
                raise RuntimeError("Range response mismatch")
            b=r.raw.read(n+1)
        if len(b)!=n:raise RuntimeError("Range length mismatch")
        self.pos+=n;self.transferred+=n
        return b

def main():
    out=Path("/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/.runtime/acquisition-20261020")
    out.mkdir(exist_ok=False)
    url="https://zenodo.org/records/11278238/files/part1.zip?download=1"
    remote=Remote(url)
    with zipfile.ZipFile(remote) as z:
        listing=[dict(name=i.filename,bytes=i.file_size,compressed=i.compress_size) for i in z.infolist()]
        (out/"part1-index.json").write_text(json.dumps(listing,indent=2))
        records=[]
        for item in z.infolist():
            if item.filename.endswith("_meta.json"):
                if item.file_size>1024*1024:raise RuntimeError("Oversized metadata")
                b=z.read(item)
                dest=out/Path(item.filename).name
                dest.write_bytes(b)
                records.append(dict(member=item.filename,sha256=hashlib.sha256(b).hexdigest()))
    (out/"receipt.json").write_text(json.dumps(dict(source=url,archive_bytes=remote.size,downloaded_bytes=remote.transferred,records=records),indent=2))
    print(json.dumps(dict(downloaded_bytes=remote.transferred,metadata_files=len(records),first=records[:1]),indent=2))
if __name__=="__main__":main()
