import pytest
from fastapi import HTTPException
from floodlab.server import artifact,health

def test_separate_service():assert health()['service']=='satquery-flood-lab'

@pytest.mark.parametrize('run_id,name',[('..','result.json'),('synthetic-bridge-001','../../README.md'),('synthetic-bridge-001','unknown.txt')])
def test_download_allowlist(run_id,name):
    with pytest.raises(HTTPException) as e:artifact(run_id,name)
    assert e.value.status_code==404

def test_experimental_evidence_is_independent():
    from floodlab.server import experimental_evidence,workspace_status,samples,disconnected_analysis
    d=experimental_evidence()
    assert d['tests']['passed']>=40 and not d['benchmarks']['metrics']
    assert workspace_status()['lab_port']==8770 and samples()==[]
    with pytest.raises(HTTPException) as e:disconnected_analysis('analyze')
    assert e.value.status_code==503
