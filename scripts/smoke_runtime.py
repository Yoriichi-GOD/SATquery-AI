"""Real-model smoke runs on tracked development examples, not accuracy benchmarks."""
import argparse
import json
import sys
import time
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'paired_lab')]
from preflight import digest, check


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workflow',choices=['water','temporal','land-cover','sar-scene'],required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--sar-input',type=Path,help='Required for sar-scene: real georeferenced 120x120 Sentinel-1 VV/VH dB crop at 10 m.')
    args=p.parse_args()
    if args.out.exists():p.error('Use a new output directory; existing evidence is never overwritten.')
    if args.workflow=='sar-scene' and args.sar_input is None:p.error('sar-scene requires --sar-input; the tracked BEN crop has no CRS and cannot validate this upload route.')
    readiness=check(args.workflow,verify_hashes=True)
    if readiness['status']=='blocked':
        print(json.dumps(readiness,indent=2));return 1
    import numpy as np
    import rasterio
    from inputs import inspect
    examples={'water':('flood-Bolivia_103757','Map water'),
              'temporal':('mci-test_000036','What road and building changes occurred?'),
              'land-cover':('ben-test-27-55','Identify land cover'),
              'sar-scene':('ben-test-27-55','Describe this SAR image')}
    sample,query=examples[args.workflow];base=ROOT/'paired_lab/samples'/sample
    names=['before.tif','after.tif'] if args.workflow=='temporal' else ['optical.tif','sar.tif']
    if args.workflow=='sar-scene':names=['sar.tif']
    records=([inspect(args.sar_input,'sar')] if args.workflow=='sar-scene' else
             [inspect(base/name,'sar' if name=='sar.tif' else 'optical') for name in names])
    started=time.perf_counter();args.out.mkdir(parents=True)
    if args.workflow=='water':
        import flood
        result=flood.segment(records[1]['data'],records[0]['data'],args.out)
        assert set(result['water_pixels'])=={'s1','s2','all'}
        assert all(0<=v<=result['denominator_pixels'] for v in result['water_pixels'].values())
    elif args.workflow=='temporal':
        import mci
        result=mci.temporal(*(r['data'].transpose(1,2,0) for r in records),args.out)
        assert result['denominator_pixels']==256*256
    elif args.workflow=='land-cover':
        import engine
        bands={name:r['data'][i] for r in records for i,name in enumerate(r['bands'])}
        result=engine.fusion(bands,args.out)
        assert set(result['scores'])=={'s1','s2','all'}
    else:
        import sar_single
        result=sar_single.run(records[0],args.out)
    report=dict(workflow=args.workflow,seconds=time.perf_counter()-started,
                python=sys.version,executable=sys.executable,preflight=readiness,
                inputs=[{'path':str(r['path']),'sha256':digest(r['path'])} for r in records],
                result=result,scope='Real inference on a previously inspected development example; no new accuracy score.')
    (args.out/'smoke.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with zipfile.ZipFile(args.out/'evidence.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for file in args.out.iterdir():
            if file.name!='evidence.zip':archive.write(file,file.name)
        for i,r in enumerate(records):archive.write(r['path'],f'input-{i+1}.tif')
    with zipfile.ZipFile(args.out/'evidence.zip') as archive:assert archive.testzip() is None
    print(json.dumps(dict(status='passed_real_inference',workflow=args.workflow,seconds=report['seconds'],output=str(args.out))))
    return 0


if __name__=='__main__':raise SystemExit(main())
