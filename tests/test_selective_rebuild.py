"""选择性重建必须绑定原生基线并拒绝漂移，不隐式重跑导入。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('driver',ROOT/'scripts/craft_exchange_acceptance.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
class SelectiveRebuild(unittest.TestCase):
 def test_inventory_rejects_symlink_and_detects_changed_baseline(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'file').write_text('original');identity=driver.tree_identity(root)
   self.assertIn('file',identity);(root/'file').write_text('changed')
   self.assertNotEqual(identity,driver.tree_identity(root))
   (root/'alias').symlink_to(root/'file')
   with self.assertRaisesRegex(ValueError,'baseline_symlink'):driver.tree_identity(root)
 def test_only_actual_three_node_change_can_rebuild(self):
  good={'invalidated':['photo','layout','pdf'],'reusable':['photo-import'],'executionAllowed':False,'automaticReplay':False}
  driver.check_rebuild_selection(good)
  for wrong in [dict(good,invalidated=['photo-import','photo','layout','pdf']),dict(good,invalidated=[]),dict(good,reusable=[]),dict(good,executionAllowed=True)]:
   with self.assertRaises(ValueError):driver.check_rebuild_selection(wrong)
 def test_exposure_rejects_bool_nan_or_same_value(self):
  for value in [True,float('nan'),float('inf'),1]:
   with self.assertRaises(ValueError):driver.changed_exposure(value,1)
  self.assertEqual(driver.changed_exposure(2,1),2)
if __name__=='__main__':unittest.main()
