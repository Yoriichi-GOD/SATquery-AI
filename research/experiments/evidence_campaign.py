"""Controlled software fault injection on actual acquired-data measurements. Zero humans/LLMs."""
import argparse,copy,json,tempfile
from pathlib import Path
from collections import Counter
from research.terrain_exposure.io import save_json,sha256
from research.evaluation.evidence_contract import check

SPECS=[('varanasi','urban.net_built_difference_ha','ha'),('varanasi','urban.common_area_ha','ha'),
    ('sangam-vihar','urban.net_built_difference_ha','ha'),('sangam-vihar','urban.common_area_ha','ha'),
    ('kedarnath','historical.common_clear_fraction','fraction'),('kedarnath','historical.new-water-proxy.area_ha','ha'),
    ('kedarnath','historical.vegetation-loss-proxy.area_ha','ha'),('nepal','terrain.30.hydrology.valid_cells','cells')]

def run(measurements,output):
    root=Path(measurements);out=Path(output)
    if out.exists():raise FileExistsError('Choose a new immutable result folder')
    out.mkdir(parents=True);facts={};artifacts={}
    for case,path,unit in SPECS:
        file=root/case/'summary.json';value=json.loads(file.read_text())
        for key in path.split('.'):value=value[key]
        identity=case+':'+path;artifact=case+'/summary.json';artifacts[artifact]=file
        facts[identity]={'fact_id':identity,'kind':'conditional_measurement','unit':unit,'value':value,
            'artifact':artifact,'sha256':sha256(file),'quality':'Not independently validated accuracy; preserve case limitations'}
    unknown='nepal:validated_exposure_f1';facts[unknown]={'value':None,'reason':'Compatible independent exposure targets unavailable'}
    save_json(out/'challenge-protocol.json',{'population':'SCRIPTED_MEASUREMENT_CONTRACT_FAULTS',
        'human_participants':0,'llm_trials':0,'baseline':'Ungated relay accepts supplied typed payload; deliberately lacks checks',
        'valid_fact_count':len(SPECS),'mutations':['value+1','wrong unit','wrong source hash','damage interpretation'],
        'extra_challenges':['unknown target','unknown fact','tampered actual artifact'],
        'not_measured':['Natural-language correctness','Human productivity','Operational reliability','Scientific H4 causal effect']})
    rows=[]
    for identity,fact in facts.items():
        if fact.get('value') is None:continue
        base={k:fact[k] for k in ['fact_id','kind','unit','value','artifact','sha256']}
        mutations=[('valid',{}),('changed_value',{'value':fact['value']+1}),('wrong_unit',{'unit':'confirmed_buildings'}),
            ('wrong_hash',{'sha256':'0'*64}),('unsupported_damage',{'kind':'confirmed_damage'})]
        for fault,mutation in mutations:
            claim={**base,**mutation};status=check(claim,facts,artifacts)
            rows.append({'id':identity+':'+fault,'fault':fault,'expected_supported':fault=='valid',
                'ungated_accepted':True,'gate_accepted':status=='SUPPORTED_TYPED_MEASUREMENT','gate_status':status,'claim':claim})
    for identity in [unknown,'invented_fact']:
        status=check({'fact_id':identity,'value':1},facts,artifacts)
        rows.append({'id':identity,'fault':'unavailable','expected_supported':False,'ungated_accepted':True,
            'gate_accepted':status=='SUPPORTED_TYPED_MEASUREMENT','gate_status':status})
    first=next(f for f in facts.values() if f.get('value') is not None)
    with tempfile.TemporaryDirectory() as d:
        tampered=Path(d)/'summary.json';tampered.write_text('{}')
        paths={**artifacts,first['artifact']:tampered};status=check(first,facts,paths)
        rows.append({'id':'tampered-artifact','fault':'tampered_artifact','expected_supported':False,
            'ungated_accepted':True,'gate_accepted':status=='SUPPORTED_TYPED_MEASUREMENT','gate_status':status})
    result={'population':'SCRIPTED_CONTRACT_FAULT_INJECTION_NOT_HUMAN_STUDY','trials':len(rows),
        'valid_claims':sum(r['expected_supported'] for r in rows),'invalid_claims':sum(not r['expected_supported'] for r in rows),
        'valid_accepted':sum(r['gate_accepted'] and r['expected_supported'] for r in rows),
        'invalid_rejected':sum(not r['gate_accepted'] and not r['expected_supported'] for r in rows),
        'incorrect_decisions':sum(r['gate_accepted']!=r['expected_supported'] for r in rows),
        'statuses':dict(Counter(r['gate_status'] for r in rows)),
        'H4_status':'Software contract guards verified on predefined faults; real analyst/semantic experiment remains unperformed',
        'humans':0,'models':0}
    save_json(out/'facts.json',facts);save_json(out/'trials.json',rows);save_json(out/'summary.json',result)
    save_json(out/'manifest.json',{'files':{p.name:sha256(p) for p in out.iterdir() if p.is_file()}})
    print(json.dumps(result),flush=True);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--measurements',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();run(a.measurements,a.output)
