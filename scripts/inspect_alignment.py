"""Non-scoring pilot review panels and preprocessing audit."""
import hashlib,json
from pathlib import Path
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
def median_filter(a,size=3):
    return np.median(np.lib.stride_tricks.sliding_window_view(np.pad(a,size//2,mode="edge"),(size,size)),axis=(-2,-1))
P=Path("/root/satquery/acquisition/s1s2-water-7-v2/crop")
E=Path("/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/.runtime/alignment-20261020")
E.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest={"scope":"Assistant diagnostic review, not independent human adjudication",
 "regions":[[0,0],[192,0],[384,0],[0,384],[192,384],[384,384]],
 "size":128,"coordinate_order":"column,row",
 "rules":"Stable ground features only; no water edges or bright SAR scatterer matched to a building without ambiguity review. No warp fitting. Missing reliable landmarks stays null.",
 "inputs":{n:sha(P/n) for n in ("sar-db.tif","optical-13band.tif")},
 "script_sha256":sha(Path(__file__))}
(E/"manifest.json").write_text(json.dumps(manifest,indent=2))
with rasterio.open(P/"optical-13band.tif") as ds:o=ds.read();transform=ds.transform
with rasterio.open(P/"sar-db.tif") as ds:s=ds.read()
rgb=np.clip(o[[3,2,1]].transpose(1,2,0)/3000,0,1)
stats=[]
for band in range(2):
    stats.append({"band":["VV","VH"][band],"min_db":float(np.nanmin(s[band])),
                  "max_db":float(np.nanmax(s[band])),"clip_fraction":float(((s[band]<-50)|(s[band]>10)).mean())})
for group in range(2):
    fig,axes=plt.subplots(3,3,figsize=(12,12),layout="constrained")
    for row,(col,y) in enumerate(manifest["regions"][group*3:group*3+3]):
        ext=[col,col+128,y+128,y]
        axes[row,0].imshow(rgb[y:y+128,col:col+128],extent=ext)
        axes[row,1].imshow(s[0,y:y+128,col:col+128],cmap="gray",vmin=-25,vmax=0,extent=ext)
        axes[row,2].imshow(median_filter(s[0],size=3)[y:y+128,col:col+128],cmap="gray",vmin=-25,vmax=0,extent=ext)
        for i,a in enumerate(axes[row]):
            a.set_title(f"Region {group*3+row+1}: "+["Optical RGB","SAR VV raw","SAR VV 3x3 median (display only)"][i])
            a.set_xlabel("Crop column");a.set_ylabel("Crop row");a.grid(alpha=.2)
    fig.savefig(E/f"regions-{group+1}.png",dpi=110);plt.close(fig)
(E/"preprocessing.json").write_text(json.dumps({"sar":stats,"optical_clip_fraction":float((o>12000).mean()),
 "optical_band_names":["B01","B02","B03","B04","B05","B06","B07","B08","B8A","B09","B10","B11","B12"],
 "display_filter_does_not_modify_inputs":True,"transform":list(transform)},indent=2))
print("Saved six-region review panels and clipping measurements")
