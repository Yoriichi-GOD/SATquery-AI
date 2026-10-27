import json,time,hashlib,base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
P=Path("/root/satquery/acquisition/s1s2-water-7-v2")
m=json.loads((P/"manifest.json").read_text())
deadline=(P/"manifest.json").stat().st_mtime+900
receipts=json.loads((P/"receipts.json").read_text())
done={r["file"] for r in receipts}
j=json.loads((P/"gcs-listing.json").read_text())
assets=[x for x in j["items"] if ("/IMG_DATA/" in x["name"] and "_B" in x["name"] and x["name"].endswith(".jp2"))
            or x["name"].endswith(("MSK_CLOUDS_B00.gml","MTD_MSIL1C.xml","MTD_TL.xml"))]
partial_bytes=0
for x in assets:
    p=P/Path(x["name"]).name
    if p.exists() and p.name not in done:
        partial_bytes+=p.stat().st_size
        p.rename(p.with_suffix(p.suffix+".serial-partial"))
assert m["planned_bytes"]+partial_bytes<m["download_ceiling_bytes"]
(P/"continuation.json").write_text(json.dumps(dict(reason="Parallel optical continuation within original deadline",partial_bytes=partial_bytes,deadline=deadline,workers=8),indent=2))
def get(x):
    p=P/Path(x["name"]).name
    if p.name in done:return None
    url="https://storage.googleapis.com/gcp-public-data-sentinel-2/"+x["name"]
    h=hashlib.sha256();md=hashlib.md5();n=0
    with requests.get(url,stream=True,timeout=45) as r:
        r.raise_for_status()
        with p.open("xb") as f:
            for b in r.iter_content(2**20):
                if time.time()>deadline:raise RuntimeError("Original deadline exceeded")
                n+=len(b)
                if n>int(x["size"]):raise RuntimeError("Oversized object")
                f.write(b);h.update(b);md.update(b)
    assert n==int(x["size"]) and base64.b64encode(md.digest()).decode()==x["md5Hash"]
    print("Verified",p.name,flush=True)
    return dict(file=p.name,bytes=n,sha256=h.hexdigest(),url=url,generation=x["generation"],md5_verified=True)
with ThreadPoolExecutor(max_workers=8) as pool:
    for r in pool.map(get,assets):
        if r:receipts.append(r)
        (P/"receipts.json").write_text(json.dumps(receipts,indent=2))
(P/"completed.json").write_text(json.dumps(dict(downloaded_bytes=m["planned_bytes"]+partial_bytes,seconds=time.time()-(deadline-900),files=len(receipts),includes_interrupted_optical_bytes=True),indent=2))
print("ACQUISITION COMPLETE",flush=True)
