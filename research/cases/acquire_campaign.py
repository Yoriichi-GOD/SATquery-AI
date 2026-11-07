"""Frozen case acquisition; native windows only. No metrics or label-based selection."""
from pathlib import Path
import argparse,json,math,logging,time
from research.datasets.cog import acquire,get_json
from research.terrain_exposure.io import save_json,sha256

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'research/experiments/case-campaign-20261107.json'
LICENCES={'copdem':'https://registry.opendata.aws/copernicus-dem/',
 'lulc':'https://planetarycomputer.microsoft.com/dataset/io-lulc-annual-v02',
 'worldcover':'https://esa-worldcover.org/en/data-access','jrc':'https://global-surface-water.appspot.com/download',
 'landsat':'https://www.usgs.gov/landsat-missions/landsat-data-access','nasadem':'https://planetarycomputer.microsoft.com/dataset/nasadem'}

def run(output,cases=None):
    output=Path(output);protocol=json.loads(PROTOCOL.read_text());status={}
    logging.getLogger('rasterio').setLevel(logging.CRITICAL)
    for case,cfg in protocol['cases'].items():
        if cases and case not in cases:continue
        folder=output/case;folder.mkdir(parents=True,exist_ok=True);records=[]
        save_json(folder/'case.json',cfg)
        def fetch(label,url,product,license_key,nodata=None,role='input'):
            start=time.monotonic()
            try:
                receipt=acquire(url,cfg['bbox'],folder/(label+'.tif'),license_url=LICENCES[license_key],
                    product=product,nodata=nodata,role=role,max_pixels=protocol['acquisition_limits']['native_window_max_pixels'])
                record={'label':label,'state':'ACQUIRED','file':label+'.tif','receipt':receipt,'seconds':time.monotonic()-start}
            except Exception as exc:
                # Public SAS query strings never enter logs or receipts, even on an HTTP/GDAL failure.
                record={'label':label,'state':'UNAVAILABLE','error_type':type(exc).__name__,
                    'http_status':getattr(getattr(exc,'response',None),'status_code',None),
                    'source_url':url.split('?')[0],'seconds':time.monotonic()-start}
            records.append(record);save_json(folder/'acquisition.json',{'case_id':case,'protocol_sha256':sha256(PROTOCOL),'assets':records})
            print(json.dumps({'case':case,'asset':label,'state':record['state'],'seconds':round(record['seconds'],2)}),flush=True)
        west,south,east,north=cfg['bbox']
        for lat in range(math.floor(south),math.ceil(north)):
            for lon in range(math.floor(west),math.ceil(east)):
                tile=f'Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM'
                fetch('dem30-'+str(lat)+'-'+str(lon),f'https://copernicus-dem-30m.s3.amazonaws.com/{tile}/{tile}.tif','CopernicusGLO30','copdem')
        if case in {'varanasi','sangam-vihar'}:
            tile='44R' if case=='varanasi' else '43R'
            for year in protocol['urban']['years']:
                fetch('lulc-'+str(year),f'https://ai4edataeuwest.blob.core.windows.net/io-lulc/io-annual-lulc-v02/{tile}_{year}0101-{year+1}0101.tif',
                      f'ImpactObservatoryEsri annualLULCv02 {year}','lulc',0)
            wc='N24E081' if case=='varanasi' else 'N27E075'
            for year,version in [(2020,'v100'),(2021,'v200')]:
                fetch('worldcover-'+str(year),f'https://esa-worldcover.s3.eu-central-1.amazonaws.com/{version}/{year}/map/ESA_WorldCover_10m_{year}_{version}_{wc}_Map.tif',
                      f'ESAWorldCover{year}{version}','worldcover',0,'cross_product_context_not_reference')
            tile='80E_30N' if case=='varanasi' else '70E_30N'
            for product in ['occurrence','seasonality']:
                fetch('jrc-'+product,f'https://s3.waw4-1.cloudferro.com/swift/v1/global-surface-water/download2024/Aggregated/VER1-5/{product}/{product}_{tile}_v1_5_2024.tif',
                      'JRCGSWv1.5 '+product,'jrc',255,'historical_water_context_not_event_reference')
        if case=='kedarnath':
            for label,date in [('before','20130522'),('after','20130623')]:
                item_id=f'LC08_L2SP_145039_{date}_02_T1'
                item=get_json('https://planetarycomputer.microsoft.com/api/stac/v1/collections/landsat-c2-l2/items/'+item_id)
                save_json(folder/('landsat-'+label+'-item.json'),item)
                for band in protocol['landsat']['bands']:
                    fetch('landsat-'+label+'-'+band,item['assets'][band]['href'],item_id+':'+band,'landsat')
            for lon in [78,79]:
                item_id=f'NASADEM_HGT_n30e0{lon}'
                try:
                    item=get_json('https://planetarycomputer.microsoft.com/api/stac/v1/collections/nasadem/items/'+item_id)
                    save_json(folder/(item_id+'-item.json'),item)
                    fetch('nasadem-'+str(lon),item['assets']['elevation']['href'],item_id,'nasadem')
                except Exception as exc:records.append({'label':item_id,'state':'UNAVAILABLE','error_type':type(exc).__name__})
        status[case]={'acquired':sum(r['state']=='ACQUIRED' for r in records),'unavailable':sum(r['state']!='ACQUIRED' for r in records)}
        save_json(folder/'acquisition.json',{'case_id':case,'protocol_sha256':sha256(PROTOCOL),'assets':records})
    save_json(output/'acquisition-summary.json',status)
    return status

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--case',action='append');a=p.parse_args();run(a.output,a.case)
