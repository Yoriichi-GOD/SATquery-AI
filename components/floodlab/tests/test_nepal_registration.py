import json,hashlib,sqlite3
from pathlib import Path
from shapely.geometry import shape
B=Path(__file__).resolve().parents[1]
def test_registered_references_and_candidate_coverage():
    d=json.loads((B/'docs/dataset-readiness.json').read_text())
    assert not d['errors'] and len(d['references'])==2 and len(d['catalogue_counts'])==8
    for r in d['references']:
        # The first registration preceded reference inspection. Later post-freeze
        # evaluation legitimately inspected labels; that does not make them inputs.
        assert r['role']=='evaluation_only' and isinstance(r['damage_features_inspected'],bool)
        p=B/'evaluation_only/emsr'/r['filename']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    for a in d['areas']:
        candidate=a['recommended_metadata_pair']
        assert candidate and candidate['full_aoi_footprint_coverage']
        # Acquisition also progressed after the initial catalogue registration.
        assert isinstance(candidate['imagery_downloaded'],bool)
        assert 11.9<candidate['gap_days']<12.1

def test_reference_labels_remain_outside_prediction_and_response_code():
    for path in (B/'floodlab').glob('*.py'):
        text=path.read_text().lower()
        assert not any(marker in text for marker in ['emsr927','unosat','evaluation_only/','damage_gra']),path.name
    manifest=json.loads((B/'artifacts/runs/nepal-syapru-004/manifest.json').read_text())
    assert manifest['pre']['role']==manifest['post']['role']=='observation'
    assert manifest['infrastructure_role']=='historical_osm'
