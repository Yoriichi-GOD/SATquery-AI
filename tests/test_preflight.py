"""Preflight must distinguish missing/corrupt assets from executable inference."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import preflight


class PreflightTests(unittest.TestCase):
    def asset(self, **extra):
        return dict(id='test',workflows=['water'],root='assets',path='weights.pt',kind='manual',
                    source='maintainer',access='manual',required=[],sha256=None,**extra)

    def test_missing_file_explains_recovery(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(preflight.paths,'ASSET_ROOT',Path(tmp)):
            row=preflight.inspect(self.asset())
            self.assertEqual(row['status'],'blocked')
            self.assertIn('maintainer',row['recovery'])

    def test_corrupt_weight_is_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(preflight.paths,'ASSET_ROOT',Path(tmp)):
            target=Path(tmp)/'weights.pt';target.write_bytes(b'changed')
            asset=self.asset();asset['sha256']='0'*64
            row=preflight.inspect(asset,True)
            self.assertEqual(row['status'],'blocked')
            self.assertIn('SHA256 mismatch',row['reason'])

    def test_missing_shard_rejected_even_with_other_weight_present(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(preflight.paths,'ASSET_ROOT',Path(tmp)):
            root=Path(tmp);(root/'one.safetensors').write_bytes(b'x')
            (root/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{'a':'two.safetensors'}}))
            asset=self.asset();asset.update(path='',required=['*.safetensors'])
            self.assertIn('Missing model shard',preflight.inspect(asset)['reason'])

    def test_verified_hash_never_claims_inference(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(preflight.paths,'ASSET_ROOT',Path(tmp)):
            target=Path(tmp)/'weights.pt';target.write_bytes(b'weights')
            asset=self.asset();asset['sha256']=preflight.digest(target)
            self.assertEqual(preflight.inspect(asset,True)['status'],'hash_verified_not_executed')

    def test_custom_root_does_not_leak_developer_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            env={**os.environ,'SATQUERY_ASSET_ROOT':tmp}
            for name in ('SATQUERY_PAIRED_DIR','SATQUERY_GROUNDING_DIR','SATQUERY_APP_DATA','SATQUERY_VQA_ADAPTER','SATQUERY_CDVQA_MODEL_DIR'):
                env.pop(name,None)
            result=subprocess.check_output([sys.executable,'-c',
                'import runtime_paths as p; print(p.PAIRED); print(p.GROUNDING); print(p.CDVQA); print(p.APP_DATA)'],env=env,text=True)
            self.assertNotIn('/root/satquery',result)
            self.assertTrue(all(str(Path(tmp)) in line for line in result.splitlines()))

    def test_vqa_override_requires_pinned_provenance(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'SATQUERY_VQA_MODEL':tmp}):
            with self.assertRaisesRegex(ValueError,'provenance'):
                preflight.paths.vqa_path()
            receipt=Path(tmp)/'satquery-source.json'
            receipt.write_text(json.dumps({'repo':'wrong','revision':'wrong'}))
            with self.assertRaisesRegex(ValueError,'provenance'):
                preflight.paths.vqa_path()
            receipt.write_text(json.dumps({'repo':preflight.paths.VQA_REPO,'revision':preflight.paths.VQA_REVISION}))
            self.assertEqual(preflight.paths.vqa_path(),tmp)

    def test_vqa_pinned_cache_directory_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot=Path(tmp)/preflight.paths.VQA_REVISION;snapshot.mkdir()
            with patch.dict(os.environ,{'SATQUERY_VQA_MODEL':str(snapshot)}):
                self.assertEqual(preflight.paths.vqa_path(),str(snapshot))

    def test_relative_manifest_paths_follow_manifest(self):
        self.assertEqual(preflight.paths.manifest_path({'path':'model.pt'},Path('assets/release.json')),Path('assets/model.pt'))


if __name__=='__main__':unittest.main()
