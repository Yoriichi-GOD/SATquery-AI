"""Explicit experimental RGB-pair mode; exact frozen templates, no paraphrase coercion."""
import hashlib
import json
import re
import time
from pathlib import Path
from PIL import Image
from runtime_paths import CDVQA, ENCODER, read_manifest

CONTRACT=json.loads((Path(__file__).with_name('cdvqa-questions.json')).read_text(encoding='utf-8'))

def supported(question):
    return ' '.join(re.findall(r'[a-z]+|\d+',question.lower())) in CONTRACT['supported_questions']

def inspect_rgb(path):
    with Image.open(path) as im:
        if im.mode!='RGB' or min(im.size)<32 or im.width*im.height>1_048_576:
            raise ValueError('CDVQA uploads require prepared RGB images, 32 pixels minimum per side and at most 1 megapixel. No automatic spectral rendering.')
        im.load()
        return dict(path=str(path),modality='optical',cdvqa_rgb=True,shape=[im.height,im.width],count=3,
                    sha256=digest(path))

def validate(records,aligned):
    if len(records)!=2 or not all(r.get('cdvqa_rgb') for r in records):
        raise ValueError('Use the experimental CDVQA uploader for both prepared RGB dates.')
    if records[0]['shape']!=records[1]['shape']:raise ValueError('CDVQA pair dimensions differ; align inputs before upload.')
    if aligned is not True:raise ValueError('Confirm that first/before and second/after images cover the same area and are already aligned.')
    return dict(task='cdvqa',alignment='User-declared; physical co-registration is not verified',
                inputs=[{k:v for k,v in r.items() if k!='path'} for r in records])

def available():
    if not (CDVQA/'paired-best.pt').is_file() or not ENCODER.is_file():
        raise ValueError('CDVQA checkpoint or encoder unavailable. Run scripts/preflight.py --workflow cdvqa --verify-hashes; supply the maintainer release and public encoder described in docs/ASSETS.md.')
    manifest=read_manifest(CDVQA/'release.json')
    if any(manifest.get(k)!=CONTRACT[k] for k in CONTRACT):
        raise ValueError('CDVQA release contract differs from the integrated frozen model; restore the matching release.')

def run(records,query,out,progress=lambda _:None):
    available()
    from scripts.predict_cdvqa import Predictor
    start=time.perf_counter();progress('Loading frozen experimental CDVQA classifier')
    predictor=Predictor(CDVQA,ENCODER,'cpu')
    progress('Answering the exact supported question on the ordered RGB pair')
    result=predictor.predict(records[0]['path'],records[1]['path'],query,aligned=True)
    for role,r in zip(['before','after'],records):
        with Image.open(r['path']) as im:im.save(Path(out)/(role+'.png'))
    result.update(task='cdvqa',seconds=time.perf_counter()-start,
                  trace=[dict(tool=result['model'],checkpoint_sha256=result['checkpoint_sha256'],encoder_sha256=result['encoder_sha256'],preprocessing=result['preprocessing'])])
    return result

from paired_lab.external_data.common import digest
