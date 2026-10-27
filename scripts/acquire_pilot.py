"""One metadata-selected acquisition pilot. Never evaluate or train a model."""
import base64,hashlib,json,struct,time,zlib
from pathlib import Path
import requests,zipfile
from concurrent.futures import ThreadPoolExecutor
from acquire_pair_metadata import Remote

ROOT=Path("/root/satquery/acquisition/s1s2-water-7-v2")
E=Path("/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/.runtime/acquisition-20261020")
def main():
    ROOT.mkdir(parents=True,exist_ok=False)
    source=json.loads((E/"sentinel12_7_meta.json").read_text())
    product=source["properties"]["s2_srcids"][0]
    prefix=f"tiles/48/Q/UD/{product}.SAFE/"
    listing=requests.get("https://storage.googleapis.com/storage/v1/b/gcp-public-data-sentinel-2/o",
        params={"prefix":prefix,"maxResults":1000},timeout=30)
    listing.raise_for_status();j=listing.json()
    assert not j.get("nextPageToken")
    assets=[x for x in j["items"] if ("/IMG_DATA/" in x["name"] and "_B" in x["name"] and x["name"].endswith(".jp2"))
            or x["name"].endswith(("MSK_CLOUDS_B00.gml","MTD_MSIL1C.xml","MTD_TL.xml"))]
    assert len([x for x in assets if x["name"].endswith(".jp2")])==13
    license_response=requests.get("https://zenodo.org/api/records/11278238",timeout=30)
    license_response.raise_for_status();record=license_response.json()
    (ROOT/"zenodo-record.json").write_text(json.dumps(record,indent=2))
    (ROOT/"gcs-listing.json").write_text(json.dumps(j,indent=2))
    url="https://zenodo.org/records/11278238/files/part1.zip?download=1"
    remote=Remote(url)
    with zipfile.ZipFile(remote) as z:
        members=[z.getinfo(f"7/sentinel12_{sensor}_7_{kind}.tif") for sensor,kind in
                 [("s1","img"),("s1","valid"),("s2","valid"),("s1","msk"),("s2","msk")]]
    manifest={"status":"frozen_before_raster_download","purpose":"Acquisition/compatibility pilot only; no unseen acceptance claim",
      "selection":"Lowest numeric official validation ID in part1 metadata with one optical and one SAR source: 7",
      "source_metadata_sha256":hashlib.sha256((E/"sentinel12_7_meta.json").read_bytes()).hexdigest(),
      "license":record["metadata"]["license"],"source":url,"product":product,
      "download_ceiling_bytes":1500*1024**2,"time_ceiling_seconds":900,
      "planned_bytes":sum(int(x["size"]) for x in assets)+sum(x.compress_size for x in members),
      "crop":{"row":5120,"col":5120,"height":512,"width":512,"selection":"Fixed central crop before viewing pixels"},
      "scores_authorized":False}
    assert manifest["planned_bytes"]<manifest["download_ceiling_bytes"]
    (ROOT/"manifest.json").write_text(json.dumps(manifest,indent=2))
    receipts=[];start=time.monotonic();used=0
    def chunks(r):
        nonlocal used
        for b in r.iter_content(2**20):
            used+=len(b)
            if used>manifest["download_ceiling_bytes"] or time.monotonic()-start>900:raise RuntimeError("Acquisition ceiling exceeded")
            yield b
    def archive_chunks(offset,size):
        nonlocal used
        def get_range(pair):
            lo,hi=pair
            with requests.get(url,headers={"Range":f"bytes={lo}-{hi}"},stream=True,timeout=90) as r:
                if r.status_code!=206 or not r.headers.get("Content-Range","").startswith(f"bytes {lo}-"):
                    raise RuntimeError("Archive range mismatch")
                data=r.raw.read(hi-lo+2)
                if len(data)!=hi-lo+1:raise RuntimeError("Archive range length mismatch")
                return data
        parts=[(lo,min(lo+8*2**20,offset+size)-1) for lo in range(offset,offset+size,8*2**20)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            for i in range(0,len(parts),8):
                for data in pool.map(get_range,parts[i:i+8]):
                    used+=len(data)
                    if used>manifest["download_ceiling_bytes"] or time.monotonic()-start>900:raise RuntimeError("Acquisition ceiling exceeded")
                    yield data
                print("Archive bytes received",used,flush=True)
    for info in members:
        remote.seek(info.header_offset);header=remote.read(30)
        assert header[:4]==b"PK\x03\x04"
        n,e=struct.unpack_from("<HH",header,26);offset=info.header_offset+30+n+e
        path=ROOT/Path(info.filename).name
        h=hashlib.sha256();crc=0;count=0
        decompressor=zlib.decompressobj(-15) if info.compress_type==8 else None
        assert info.compress_type in (0,8)
        with path.open("xb") as f:
                for b in archive_chunks(offset,info.compress_size):
                    data=decompressor.decompress(b) if decompressor else b
                    f.write(data);h.update(data);crc=zlib.crc32(data,crc);count+=len(data)
                    if count>info.file_size:raise RuntimeError("Expanded member exceeds expected size")
                if decompressor:
                    data=decompressor.flush();f.write(data);h.update(data);crc=zlib.crc32(data,crc);count+=len(data)
        assert count==info.file_size and crc==info.CRC
        receipts.append(dict(file=path.name,sha256=h.hexdigest(),bytes=count,archive_member=info.filename,crc32_verified=True))
        print("Verified",path.name,count,flush=True)
        (ROOT/"receipts.json").write_text(json.dumps(receipts,indent=2))
    for asset in assets:
        path=ROOT/Path(asset["name"]).name;h=hashlib.sha256();md5=hashlib.md5();count=0
        url="https://storage.googleapis.com/gcp-public-data-sentinel-2/"+asset["name"]
        with requests.get(url,stream=True,timeout=60) as r:
            r.raise_for_status()
            with path.open("xb") as f:
                for b in chunks(r):f.write(b);h.update(b);md5.update(b);count+=len(b)
        assert count==int(asset["size"]) and base64.b64encode(md5.digest()).decode()==asset["md5Hash"]
        receipts.append(dict(file=path.name,sha256=h.hexdigest(),bytes=count,url=url,generation=asset["generation"],md5_verified=True))
        print("Verified",path.name,count,flush=True)
        (ROOT/"receipts.json").write_text(json.dumps(receipts,indent=2))
    (ROOT/"completed.json").write_text(json.dumps(dict(downloaded_bytes=used,seconds=time.monotonic()-start,files=len(receipts)),indent=2))
    print("ACQUISITION COMPLETE",flush=True)
if __name__=="__main__":main()
