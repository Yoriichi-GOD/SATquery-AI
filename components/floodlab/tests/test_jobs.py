import json
import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from floodlab import jobs

def test_rejects_invalid_area_and_future_date():
 with pytest.raises(ValidationError):jobs.EventRequest(bbox=[2,1,0,3],event_date='2026-08-26')
 with pytest.raises(ValidationError):jobs.EventRequest(bbox=[0,0,1,1],event_date='2999-01-01')

def test_only_one_job_and_restart_is_not_success(tmp_path,monkeypatch):
 monkeypatch.setattr(jobs,'ROOT',tmp_path);monkeypatch.setattr(jobs,'active',None)
 monkeypatch.setattr(jobs.pool,'submit',lambda *args:None)
 q=jobs.EventRequest(bbox=[0,0,1,1],event_date='2020-01-01')
 result=jobs.submit(q)
 assert jobs.status(result['job_id'])['state']=='queued'
 with pytest.raises(HTTPException) as error:jobs.submit(q)
 assert error.value.status_code==409
 monkeypatch.setattr(jobs,'active',None)
 interrupted=jobs.status(result['job_id'])
 assert interrupted['state']=='interrupted' and interrupted['events'][-1]['state']=='interrupted'

def test_failed_provider_does_not_leak_details(tmp_path,monkeypatch):
 monkeypatch.setattr(jobs,'ROOT',tmp_path);monkeypatch.setattr(jobs,'active','event-aaaaaaaaaaaa')
 def fail(*args):raise RuntimeError('secret-token=do-not-expose')
 monkeypatch.setattr(jobs,'discover',fail)
 jobs.execute('event-aaaaaaaaaaaa',jobs.EventRequest(bbox=[0,0,1,1],event_date='2020-01-01'))
 result=jobs.status('event-aaaaaaaaaaaa')
 assert result['state']=='failed' and 'secret' not in json.dumps(result)
 assert jobs.active is None

def test_job_runs_all_stages_before_completion(tmp_path,monkeypatch):
 monkeypatch.setattr(jobs,'ROOT',tmp_path);monkeypatch.setattr(jobs,'active','event-bbbbbbbbbbbb');calls=[]
 def stage(name,result=None):
  def f(*args,**kwargs):calls.append(name);return result
  return f
 for name in ('discover','acquire','prepare','attach_topology','attach_optical','run'):
  monkeypatch.setattr(jobs,name,stage(name,{} if name=='discover' else tmp_path/'manifest.json'))
 jobs.execute('event-bbbbbbbbbbbb',jobs.EventRequest(bbox=[0,0,1,1],event_date='2020-01-01'))
 assert calls==['discover','acquire','prepare','attach_topology','attach_optical','run']
 assert jobs.status('event-bbbbbbbbbbbb')['state']=='complete'

def test_failed_optical_stage_cannot_publish_complete(tmp_path,monkeypatch):
 monkeypatch.setattr(jobs,'ROOT',tmp_path);monkeypatch.setattr(jobs,'active','event-cccccccccccc')
 for name in ('discover','acquire','prepare','attach_topology'):monkeypatch.setattr(jobs,name,lambda *args,**kwargs:None)
 def fail(*args,**kwargs):raise ValueError('grid mismatch')
 monkeypatch.setattr(jobs,'attach_optical',fail)
 def forbidden(*args):pytest.fail('Must not publish after failed validation')
 monkeypatch.setattr(jobs,'run',forbidden)
 jobs.execute('event-cccccccccccc',jobs.EventRequest(bbox=[0,0,1,1],event_date='2020-01-01'))
 assert jobs.status('event-cccccccccccc')['state']=='failed'


def test_status_keeps_timestamped_stage_history(tmp_path,monkeypatch):
 monkeypatch.setattr(jobs,'ROOT',tmp_path)
 first=jobs.write_status('event-dddddddddddd','queued','Waiting to acquire satellite observations')
 started=first['created_at']
 jobs.write_status('event-dddddddddddd','running','Processing pre Sentinel-1 acquisition')
 jobs.write_status('event-dddddddddddd','running','Processing pre Sentinel-1 acquisition')
 final=jobs.write_status('event-dddddddddddd','complete','Evidence saved.')
 assert final['created_at']==started
 assert [x['message'] for x in final['events']]==['Waiting to acquire satellite observations','Processing pre Sentinel-1 acquisition','Evidence saved.']
 assert all(x['at'] and x['state'] for x in final['events'])
