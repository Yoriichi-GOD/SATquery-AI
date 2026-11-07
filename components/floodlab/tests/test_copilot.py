import pytest
from floodlab.copilot import render
R={'run_id':'fixture','synthetic':True,'summary':{'new_water_m2':12300,'new_water_pixels':123,'exposed_buildings':7,'exposed_road_m':12.345,'exposed_bridge_features':2,'connectivity_assessed':False,'potentially_cut_off':0},'limitations':['test']}
def test_all_numbers_have_source_values():
 a=render(R,'summary','en');assert '12,300' in a['answer'];assert len(a['citations'])==5
 assert all(c['value']==R['summary'][c['pointer'].split('/')[-1]] for c in a['citations'])
def test_unknown_connectivity_is_not_zero_isolation():
 a=render(R,'connectivity','en');assert 'unresolved' in a['answer'];assert not a['citations'];assert '0' not in a['answer']
def test_nepali_uses_same_calculations():
 a=render(R,'buildings','ne');assert '7' in a['answer'];assert a['citations'][0]['value']==7
def test_unknown_intent_cannot_become_free_text():
 with pytest.raises(ValueError):render(R,'invent 999 casualties','en')


def test_tampered_frozen_evidence_is_rejected(tmp_path):
 import json,hashlib
 from floodlab.copilot import frozen_result
 files={}
 for name,value in [('result.json',R),('manifest.json',{}),('connectivity.json',{})]:
  payload=json.dumps(value).encode();(tmp_path/name).write_bytes(payload);files[name]=hashlib.sha256(payload).hexdigest()
 (tmp_path/'freeze.json').write_text(json.dumps({'files':files}))
 assert frozen_result(tmp_path)['run_id']=='fixture'
 (tmp_path/'result.json').write_text(json.dumps({**R,'run_id':'tampered'}))
 with pytest.raises(ValueError,match='mismatch'):frozen_result(tmp_path)
