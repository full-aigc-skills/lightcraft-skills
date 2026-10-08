"""跨领域 TypeScript 资源须与 Python/JSON 一样绑定回执。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ExchangeResources(unittest.TestCase):
 def test_typescript_change_expires_resource_identity(self):
  spec=importlib.util.spec_from_file_location('gateway',ROOT/'runtime/command_gateway.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);file=root/'craft_exchange.ts';file.write_text('old');first=m.capture_resources(root);self.assertIn(file.name,first);file.write_text('new');self.assertNotEqual(first,m.capture_resources(root))
   alias=root/'alias.ts';alias.symlink_to(file)
   with self.assertRaises(ValueError):m.capture_resources(root)
if __name__=='__main__':unittest.main()
