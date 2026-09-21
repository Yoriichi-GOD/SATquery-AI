import sys,unittest,tempfile,json,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from unittest.mock import patch
from fastapi import HTTPException
import server
import grounding_lab.app as lab
class CoordinationTests(unittest.TestCase):
 def setUp(self):
  server.busy=False;lab.busy=False
  self.tmp=tempfile.TemporaryDirectory();self.old=lab.DATA;lab.DATA=Path(self.tmp.name)
  self.iid=uuid.uuid4().hex;p=lab.DATA/self.iid;p.mkdir();(p/'input.png').touch();(p/'image.json').write_text('{}')
  self.selection=lab.Selection(image_id=self.iid,category='stadium')
 def tearDown(self):
  server.busy=False;lab.busy=False;lab.DATA=self.old;self.tmp.cleanup()
 def test_main_busy_is_visible_and_rejects_lab(self):
  server.busy=True;self.assertTrue(lab.status()['busy'])
  with self.assertRaises(HTTPException) as raised:lab.run(self.selection)
  self.assertEqual(raised.exception.status_code,409);self.assertFalse(lab.busy)
 def test_failed_setup_releases_both_gates(self):
  with patch.object(lab.pool,'submit',side_effect=RuntimeError('test setup failure')):
   with self.assertRaises(RuntimeError):lab.run(self.selection)
  self.assertFalse(server.busy);self.assertFalse(lab.busy)
 def test_failed_worker_releases_both_gates(self):
  with patch.object(lab.pool,'submit'):j=lab.run(self.selection)
  self.assertTrue(server.busy);self.assertTrue(lab.busy)
  with patch.object(lab.subprocess,'run',side_effect=RuntimeError('test worker failure')):lab.worker(j['id'])
  self.assertFalse(server.busy);self.assertFalse(lab.busy)
  self.assertEqual(lab.get_run(j['id'])['state'],'error')
if __name__=='__main__':unittest.main()
