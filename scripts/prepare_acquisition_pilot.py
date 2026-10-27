"""Create a fixed crop and verify input contracts; no model or water scoring."""
import hashlib,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.warp import reproject,Resampling,transform_bounds,transform_geom
from rasterio.features import rasterize

P=Path("/root/satquery/acquisition/s1s2-water-7-v2")
R=Path("/mnt/c/Users/nrgen/.codex/scratch/SATquery AI")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(2**20),b""):h.update(b)
    return h.hexdigest()
def main():
    assert (P/"completed.json").exists(),"Acquisition incomplete"
    for r in json.loads((P/"receipts.json").read_text()):assert sha(P/r["file"])==r["sha256"]
    out=P/"crop";out.mkdir(exist_ok=False)
    metadata={e.tag.split("}")[-1]:e.text for e in ET.parse(P/"MTD_MSIL1C.xml").getroot().iter()}
    manifest=json.loads((P/"manifest.json").read_text())
    assert metadata["PRODUCT_URI"]==manifest["product"]+".SAFE"
    assert float(metadata["QUANTIFICATION_VALUE"])==10000
    w=Window(5120,5120,512,512)
    with rasterio.open(P/"sentinel12_s1_7_img.tif") as ds:
        s1=ds.read(window=w,masked=True).astype("float32").filled(np.nan)/100.
        profile=ds.profile;profile.update(width=512,height=512,transform=ds.window_transform(w),dtype="float32",nodata=float("nan"),compress="deflate")
    bands=['B01','B02','B03','B04','B05','B06','B07','B08','B8A','B09','B10','B11','B12']
    s2=np.full((13,512,512),np.nan,dtype=np.float32)
    native=[]
    for i,b in enumerate(bands):
        f=next(P.glob("*_"+b+".jp2"))
        with rasterio.open(f) as ds:
            reproject(rasterio.band(ds,1),s2[i],src_transform=ds.transform,src_crs=ds.crs,
                src_nodata=0,dst_transform=profile["transform"],dst_crs=profile["crs"],
                dst_nodata=np.nan,resampling=Resampling.bilinear)
            native.append(dict(band=b,crs=str(ds.crs),resolution=list(ds.res),file=f.name))
    for name,a in [("sar-db.tif",s1),("optical-13band.tif",s2)]:
        pp=dict(profile,count=len(a))
        with rasterio.open(out/name,"w",**pp) as ds:
            ds.write(a)
            if len(a)==13:
                for i,b in enumerate(bands,1):ds.set_band_description(i,b)
    validity={}
    for sensor in ("s1","s2"):
        with rasterio.open(P/f"sentinel12_{sensor}_7_valid.tif") as ds:
            assert ds.crs==profile["crs"]
            assert ds.window_transform(w).almost_equals(profile["transform"])
            mask=ds.read(1,window=w)
            assert set(np.unique(mask))<=set([0,1])
        validity[sensor]=float((mask==1).mean())
        pp=dict(profile,count=1,dtype="uint8",nodata=None)
        with rasterio.open(out/f"{sensor}-reference-valid.tif","w",**pp) as ds:ds.write(mask,1)
    # Provider cloud QA polygons: preserve and rasterize their classes, never call them human truth.
    cloud_path=P/"MSK_CLOUDS_B00.gml";root=ET.parse(cloud_path).getroot()
    assert root.tag.split("}")[-1]=="Mask","Unexpected cloud QA document"
    polygons=[]
    for poly in root.iter():
        if poly.tag.split("}")[-1]!="Polygon":continue
        rings=[]
        for pos in poly.iter():
            if pos.tag.split("}")[-1]=="posList":
                values=list(map(float,pos.text.split()))
                assert len(values)%2==0
                rings.append(np.asarray(values).reshape(-1,2).tolist())
        if not rings:continue
        srs=poly.attrib.get("srsName")
        if not srs:
            srs=next((el.attrib["srsName"] for el in root.iter() if "srsName" in el.attrib),None)
        assert srs,"Cloud QA CRS missing"
        geom=transform_geom(srs,profile["crs"],dict(type="Polygon",coordinates=rings))
        polygons.append((geom,1))
    cloud=rasterize(polygons,out_shape=(512,512),transform=profile["transform"],fill=0,dtype="uint8") if polygons else np.zeros((512,512),dtype="uint8")
    with rasterio.open(out/"provider-cloud-qa.tif","w",**dict(profile,count=1,dtype="uint8",nodata=None)) as ds:ds.write(cloud,1)
    sys.path.insert(0,str(R))
    from paired_lab.flood import prepare,available
    import torch
    x,valid=prepare(s1,s2);features=available(torch.from_numpy(x).unsqueeze(0),"all")
    assert x.shape==(15,512,512) and features.shape==(1,17,512,512)
    assert np.isfinite(x).all() and valid.any()
    # Footprint check against every local Sen1Floods11 input, independent of outcome labels.
    bounds=rasterio.transform.array_bounds(512,512,profile["transform"])
    bb=transform_bounds(profile["crs"],"EPSG:4326",*bounds)
    overlap=[]
    for file in Path("/root/satquery/paired-lab/sen1floods11/S1Hand").glob("*.tif"):
        with rasterio.open(file) as ds:b=transform_bounds(ds.crs,"EPSG:4326",*ds.bounds)
        if min(bb[2],b[2])>max(bb[0],b[0]) and min(bb[3],b[3])>max(bb[1],b[1]):overlap.append(file.name)
    result=dict(status="input_contract_passed",crop_bounds_wgs84=bb,
        original_product_verified=metadata["PRODUCT_URI"],quantification_value=10000,
        processing_baseline=metadata["PROCESSING_BASELINE"],
        finite_pair_fraction=float(valid.mean()),reference_valid_fraction=validity,
        provider_cloud_qa_fraction=float(cloud.mean()),provider_cloud_polygon_count=len(polygons),
        cloud_caveat="Provider automated polygon union, not independently verified cloud truth; includes any cloud types present",
        optical_native_bands=native,optical_resampling="bilinear to original SAR crop grid; not physical alignment proof",
        sar_conversion="original stored dB times 100 divided by 100",input_shape=list(features.shape),
        sen1floods11_crop_footprint_overlaps=overlap,
        freshness="Acquisition pilot exposed; full exposure independence and physical alignment unresolved",
        no_model_inference=True,no_water_reference_scoring=True,
        artifacts={f.name:sha(f) for f in out.glob("*.tif")})
    (out/"verification.json").write_text(json.dumps(result,indent=2))
    from PIL import Image,ImageDraw
    rgb=np.clip(np.nan_to_num(s2[[3,2,1]])/3000,0,1)
    sar=np.clip((np.nan_to_num(s1[0],nan=-30)+30)/30,0,1)
    sheet=Image.new("RGB",(1024,548),"white")
    sheet.paste(Image.fromarray((rgb.transpose(1,2,0)*255).astype("uint8")),(0,36))
    sheet.paste(Image.fromarray((sar*255).astype("uint8")).convert("RGB"),(512,36))
    draw=ImageDraw.Draw(sheet)
    draw.text((10,10),"Original L1C RGB - fixed acquisition crop",fill="black")
    draw.text((522,10),"SAR VV - visual diagnostic, not alignment proof",fill="black")
    sheet.save(out/"pair-preview.png")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
