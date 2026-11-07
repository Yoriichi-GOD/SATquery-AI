"""Synthetic known-answer fixture; never an event demonstration."""
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box,LineString,mapping
from .pipeline import digest,write_json


def create(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    pre=np.full((2,32,40),-10,dtype='float32');post=pre.copy()
    pre[:,2:5,2:5]=-23;post[:,2:5,2:5]=-23
    post[:,12:20,18:22]=-24
    pre[:,0,:]=-9999;post[:,0,:]=-9999
    meta=dict(driver='GTiff',count=2,height=32,width=40,dtype='float32',crs='EPSG:32645',transform=from_origin(400000,3100320,10,10),nodata=-9999)
    for name,a in [('pre',pre),('post',post)]:
        with rasterio.open(root/f'{name}.tif','w',**meta) as ds:ds.write(a)
    infrastructure={'role':'historical_osm','snapshot':'2026-07-27T00:00:00Z','analysis_crs':'EPSG:32645','synthetic':True,'features':[
      {'type':'Feature','id':'fixture-building','geometry':mapping(box(400185,3100130,400195,3100150)),'properties':{'kind':'building'}},
      {'type':'Feature','id':'fixture-bridge','geometry':mapping(LineString([(400050,3100160),(400350,3100160)])),'properties':{'kind':'bridge','node_ids':['v','h']}},
      {'type':'Feature','id':'fixture-safe-building','geometry':mapping(box(400020,3100200,400030,3100210)),'properties':{'kind':'building'}}],
      'settlements':[{'id':'fixture-village','node_id':'v','boundary_truncated':False}],'hub_node_ids':['h']}
    write_json(root/'infrastructure.json',infrastructure)
    sensor={'role':'observation','source':'Sentinel-1','units':'dB','bands':['VV','VH'],'terrain_corrected':True,'relative_orbit':19,'orbit_state':'descending'}
    m={'synthetic':True,'event_name':'Synthetic bridge-cut verification - NOT Nepal imagery','event_time':'2026-08-26T00:00:00Z','osm_snapshot':infrastructure['snapshot'],'infrastructure_role':'historical_osm',
       'infrastructure_path':'infrastructure.json','infrastructure_sha256':digest(root/'infrastructure.json'),
       'pre':dict(sensor,path='pre.tif',datetime='2026-08-20T00:00:00Z',scene_id='synthetic-pre',sha256=digest(root/'pre.tif')),
       'post':dict(sensor,path='post.tif',datetime='2026-09-01T00:00:00Z',scene_id='synthetic-post',sha256=digest(root/'post.tif')),
       'analysis':{'water_db':-17.,'drop_db':3.,'tile_size':13,'min_exposed_road_m':1.}}
    write_json(root/'manifest.json',m);return root/'manifest.json'

if __name__=='__main__':
    import sys
    print(create(sys.argv[1]))
