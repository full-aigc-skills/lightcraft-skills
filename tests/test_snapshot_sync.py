"""同步器必须保留用户漂移和已发布快照；只修改临时测试副本。"""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOMAIN=ROOT.name.removesuffix('-skills')
PLUGIN=ROOT.parents[1]/'full-aigc-plugins-repositories'/f'{DOMAIN}-plugin'

class SnapshotSyncContract(unittest.TestCase):
    def module(self):
        path=ROOT/'scripts/sync_local_snapshot.py'
        spec=importlib.util.spec_from_file_location('snapshot_sync',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_user_snapshot_edits_are_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'plugin';shutil.copytree(PLUGIN,target)
            skill=target/'skills'/f'{DOMAIN}-use'/'SKILL.md'
            skill.write_text(skill.read_text()+'\nUser edit must survive\n')
            before=skill.read_bytes();lock=(target/'candidate-source.json').read_bytes()
            with self.assertRaisesRegex(ValueError,'preserve_modified_plugin_snapshot'):
                self.module().sync(target)
            self.assertEqual(skill.read_bytes(),before)
            self.assertEqual((target/'candidate-source.json').read_bytes(),lock)

    def test_published_source_identity_is_never_replaced_by_local_candidate(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'plugin';shutil.copytree(PLUGIN,target)
            path=target/'candidate-source.json';data=json.loads(path.read_text());data['releaseTag']='v0.1.0';path.write_text(json.dumps(data))
            before=path.read_bytes()
            with self.assertRaisesRegex(ValueError,'not_current_local_candidate'):
                self.module().sync(target)
            self.assertEqual(path.read_bytes(),before)

    def test_source_removal_is_not_silently_applied(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);target=root/'plugin';shutil.copytree(PLUGIN,target)
            source=root/ROOT.name;shutil.copytree(ROOT,source)
            (source/'skills'/f'{DOMAIN}-use'/'SKILL.md').unlink()
            module=self.module()
            before=(target/'candidate-source.json').read_bytes()
            with patch.object(module,'ROOT',source):
                with self.assertRaisesRegex(ValueError,'source_removal_requires_review'):module.sync(target)
            self.assertEqual((target/'candidate-source.json').read_bytes(),before)

    def test_source_version_identity_is_checked_before_copy(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'plugin';shutil.copytree(PLUGIN,target)
            path=target/'candidate-source.json';data=json.loads(path.read_text());data['sourceVersion']='wrong';path.write_text(json.dumps(data))
            before=path.read_bytes()
            with self.assertRaisesRegex(ValueError,'source_identity_mismatch'):self.module().sync(target)
            self.assertEqual(path.read_bytes(),before)

if __name__=='__main__':unittest.main()
