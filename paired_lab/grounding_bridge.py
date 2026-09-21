"""Execute the existing isolated grounding worker through the unified controller."""
import json,time
from pathlib import Path
from single_bridge import request

def run(record, query, plan, out, progress=lambda stage: None):
    progress('Preparing RGB preview for experimental grounding')
    source = Path(record['path']).with_suffix('.png')
    with source.open('rb') as f:
        image = request('POST', '/grounding/api/images', files={'file': ('analysis-preview.png', f, 'image/png')}).json()
    job = request('POST', '/grounding/api/runs', json={'image_id':image['id'], 'category':plan['category'], 'threshold':plan['score_threshold'], 'mode':plan['mode']}).json()
    started = time.perf_counter()
    while time.perf_counter() - started < 660:
        job = request('GET', '/grounding/api/runs/' + job['id']).json()
        if job['state'] == 'error': raise ValueError(job.get('error', 'Grounding failed.'))
        progress(job.get('stage', 'Grounding worker running'))
        if job['state'] == 'complete': break
        time.sleep(.4)
    else: raise ValueError('Grounding exceeded the wait limit. Inspect the worker before retrying; no fallback was used.')
    progress('Collecting grounding evidence')
    (out/'grounding-raw-result.json').write_text(json.dumps(job, indent=2))
    for alias, filename in {'source':'source.png','boxes':'boxes.png','outlines':'outlines.png','masks':'masks.png','instances':'instances.png','arrays':'masks.npz'}.items():
        (out/filename).write_bytes(request('GET', f'/grounding/api/runs/{job["id"]}/{alias}').content)
    r = job['result']
    limitations = list(r['limitations']) + ['Analysis uses the normalized RGB preview; original upload is retained separately. GeoTIFF preview stretching is display-only, not spectral analysis.']
    return dict(task='grounding', answer=f'{r["objects"]} {plan["category"]} proposals retained. '+('Inspect predicted masks; object identity is not verified.' if r['objects'] else 'No proposals passed the settings; this does not establish absence.'),
                seconds=r['seconds'], objects=r['objects'], detections=r['detections'], union_mask_pixels=r['union_mask_pixels'], union_mask_percent=r['union_mask_percent'], total_image_pixels=r['total_image_pixels'], mode=r['mode'],
                confidence={'kind':'Detector score and SAM predicted IoU are not measured accuracy.'},
                trace=r['trace'] + [{'tool':'Grounding worker','run_id':job['id'],'models':r['models'],'settings':r['settings'],'peak_gpu_GiB':r['peak_gpu_GiB']}], limitations=limitations)
