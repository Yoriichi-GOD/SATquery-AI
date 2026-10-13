import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class EvidencePageTests(unittest.TestCase):
    def test_browser_scores_match_saved_sources(self):
        spec=importlib.util.spec_from_file_location('page_builder',ROOT/'scripts/build_evidence_page.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertEqual(json.loads(m.DEST.read_text()),m.build())
    def test_two_splits_and_three_water_pathways(self):
        d=json.loads((ROOT/'paired_lab/web/benchmark-data.json').read_text())
        self.assertEqual(set(d['cdvqa']),{'Test','Test2'})
        for split in ['test','bolivia']:
            rows=[r for r in d['metrics'] if r['workflow']=='water' and r['split']==split and r['metric']=='iou']
            self.assertEqual({r['path_or_class'] for r in rows},{'s1','s2','all'})
