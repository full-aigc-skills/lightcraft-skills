"""隔离 Python 不依赖 Windows locale 解码技能中文资料。"""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checks',ROOT/'runtime/package_checks.py');checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
class PortableText(unittest.TestCase):
 def test_chinese_skill_validation_with_windows_default_encoding(self):
  original=Path.read_text
  def windows_read(path,encoding=None,errors=None):return original(path,encoding=encoding or 'cp1252',errors=errors)
  with patch.object(Path,'read_text',windows_read):
   result=checks.skills(ROOT,sorted(p.name for p in (ROOT/'skills').iterdir() if p.is_dir()),ROOT/'runtime')
  self.assertEqual(result['structure'],'PASS')
if __name__=='__main__':unittest.main()
