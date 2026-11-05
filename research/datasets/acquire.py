"""Bounded resumable public downloads and STAC discovery, CLI only."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from research.terrain_exposure.io import sha256, save_json


def download(url, destination, *, expected_sha256=None, max_bytes=16*1024*1024, role="input", license_url=None):
    parts=urlsplit(url)
    if parts.scheme!='https' or not parts.hostname or parts.username or parts.password or not license_url:
        raise ValueError('Public HTTPS URL and source license record required')
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        actual=sha256(destination)
        if expected_sha256 and actual!=expected_sha256:raise ValueError('Cached source hash mismatch')
        receipt_path=destination.with_suffix(destination.suffix+'.source.json')
        if not receipt_path.exists():raise ValueError('Cached asset lacks provenance receipt')
        receipt=json.loads(receipt_path.read_text())
        if receipt.get('url')!=url or receipt.get('sha256')!=actual:raise ValueError('Cached provenance mismatch')
        return receipt
    partial=destination.with_suffix(destination.suffix+'.part')
    progress=partial.with_suffix(partial.suffix+'.json')
    offset=partial.stat().st_size if partial.exists() else 0
    saved=json.loads(progress.read_text()) if progress.exists() else {}
    if offset and (saved.get('url')!=url or not saved.get('etag')):
        raise ValueError('Partial asset needs matching source URL and ETag to resume')
    if offset>max_bytes:raise ValueError('Partial exceeds download cap')
    headers={'User-Agent':'SATquery-scientific-replay/1'}
    if offset:headers.update({'Range':f'bytes={offset}-','If-Range':saved['etag']})
    with urlopen(Request(url,headers=headers),timeout=30) as response:
        status=response.status;etag=response.headers.get('ETag')
        if status==206:
            if not offset or not re.match(rf'^bytes {offset}-\d+/\d+$',response.headers.get('Content-Range','')) or etag!=saved.get('etag'):
                raise ValueError('Server returned inconsistent resume range/version')
            mode='ab'
        elif status==200:
            offset=0;mode='wb'  # Range ignored or source version changed; restart, never append.
        else:raise ValueError('Unexpected download status')
        declared=response.headers.get('Content-Length')
        if declared and offset+int(declared)>max_bytes:raise ValueError('Download exceeds cap')
        save_json(progress,{'url':url,'etag':etag})
        with partial.open(mode) as stream:
            while True:
                block=response.read(65536)
                if not block:break
                offset+=len(block)
                if offset>max_bytes:raise ValueError('Download exceeded cap')
                stream.write(block)
    actual=sha256(partial)
    if expected_sha256 and actual!=expected_sha256:raise ValueError('Downloaded source hash mismatch')
    partial.replace(destination)
    if progress.exists():progress.unlink()
    receipt={'url':url,'sha256':actual,'bytes':destination.stat().st_size,'role':role,'license_url':license_url,
             'retrieved_utc':datetime.now(timezone.utc).isoformat(),'etag':etag,'credentials_used':False}
    save_json(destination.with_suffix(destination.suffix+'.source.json'),receipt)
    return receipt


def discover(bbox, interval, *, collection='sentinel-2-l2a', limit=20, endpoint='https://earth-search.aws.element84.com/v1'):
    if len(bbox)!=4 or not (-180<=bbox[0]<bbox[2]<=180 and -90<=bbox[1]<bbox[3]<=90) or not 1<=limit<=100:
        raise ValueError('Invalid STAC bounds or page limit')
    if endpoint!='https://earth-search.aws.element84.com/v1':raise ValueError('Only declared public discovery endpoint supported')
    query={'collections':[collection],'bbox':bbox,'datetime':interval,'limit':limit}
    request=Request(endpoint+'/search',data=json.dumps(query).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urlopen(request,timeout=30) as response:
        raw=response.read(8*1024*1024+1)
    if len(raw)>8*1024*1024:raise ValueError('STAC response exceeds cap')
    data=json.loads(raw)
    if data.get('type')!='FeatureCollection' or not isinstance(data.get('features'),list):raise ValueError('Invalid STAC result')
    return {'provider':endpoint,'request':query,'response':data,'role':'discovery_only_not_acquired_imagery',
            'truncated':any(link.get('rel')=='next' for link in data.get('links',[])),
            'retrieved_utc':datetime.now(timezone.utc).isoformat(),
            'warning':'Scene cloud fraction is not local valid coverage; assets require separate license/calibration/quality inspection'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    d=sub.add_parser('download');d.add_argument('--url',required=True);d.add_argument('--output',required=True)
    d.add_argument('--sha256');d.add_argument('--license-url',required=True);d.add_argument('--role',default='input')
    d.add_argument('--max-bytes',type=int,default=16*1024*1024)
    s=sub.add_parser('discover');s.add_argument('--bbox',type=float,nargs=4,required=True)
    s.add_argument('--interval',required=True);s.add_argument('--output',required=True);s.add_argument('--collection',default='sentinel-2-l2a')
    args=parser.parse_args()
    if args.command=='download':value=download(args.url,args.output,expected_sha256=args.sha256,max_bytes=args.max_bytes,role=args.role,license_url=args.license_url)
    else:
        if Path(args.output).exists():raise FileExistsError('Do not overwrite discovery evidence')
        value=discover(args.bbox,args.interval,collection=args.collection);save_json(args.output,value)
    print(json.dumps({k:v for k,v in value.items() if k!='response'},indent=2))


if __name__=='__main__':main()
