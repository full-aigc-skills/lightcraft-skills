"""Linux 无图像解码依赖时，验收驱动在原生安装之前失败。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('native_driver',ROOT/'scripts/native_acceptance.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
class NativeDecoderGate(unittest.TestCase):
 def test_missing_decoder_has_no_native_install_or_execution(self):
  with tempfile.TemporaryDirectory() as tmp,patch.dict('sys.modules',{'PIL':None}),patch('shutil.which',return_value=None),patch.object(driver.subprocess,'run',side_effect=AssertionError('must not install or execute')):
   root=Path(tmp)/'acceptance';result=driver.native(root)
   self.assertEqual(result['nativeStatus'],'FAIL');self.assertIn('image_decoder_required',result['error']);self.assertFalse((root/'runtime').exists())
if __name__=='__main__':unittest.main()
