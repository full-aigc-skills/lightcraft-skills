"""Linux 发布树解包及精确资产身份回归；不执行测试制品。"""
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bootstrap',ROOT/'runtime/bootstrap.py');bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap)
class LinuxInstaller(unittest.TestCase):
 def archive(self,path,rows):
  with tarfile.open(path,'w:gz') as out:
   for name,kind in rows:
    item=tarfile.TarInfo(name);item.type=kind;item.linkname='/outside'
    if kind==tarfile.REGTYPE:item.size=3;out.addfile(item,io.BytesIO(b'cli'))
    else:out.addfile(item)
 def test_regular_release_tree_extracts(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);archive=root/'release.tar.gz';self.archive(archive,[('release/bin/lightcraft-cli',tarfile.REGTYPE)])
   bootstrap.extract(archive,root/'unpacked')
   self.assertEqual((root/'unpacked/release/bin/lightcraft-cli').read_bytes(),b'cli')
 def test_unsafe_tar_never_partially_extracts(self):
  for rows in [[('good',tarfile.REGTYPE),('../escape',tarfile.REGTYPE)],[('link',tarfile.SYMTYPE)],[('link',tarfile.LNKTYPE)],[('device',tarfile.CHRTYPE)],[('same',tarfile.REGTYPE),('same',tarfile.REGTYPE)],[('parent',tarfile.REGTYPE),('parent/file',tarfile.REGTYPE)]]:
   with self.subTest(rows=rows),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);archive=root/'release.tar.gz';self.archive(archive,rows)
    with self.assertRaisesRegex(ValueError,'unsafe_archive'):bootstrap.extract(archive,root/'unpacked')
    self.assertFalse((root/'unpacked').exists())
 def test_tar_size_limit_precedes_extraction(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);archive=root/'release.tar.gz';self.archive(archive,[('file',tarfile.REGTYPE)])
   with patch.object(bootstrap,'MAX_BYTES',2):
    with self.assertRaisesRegex(ValueError,'archive_too_large'):bootstrap.extract(archive,root/'unpacked')
   self.assertFalse((root/'unpacked').exists())
 def test_linux_asset_architecture_mismatch_before_write(self):
  lock=json.loads((ROOT/'runtime/runtime.lock.json').read_text());lock['artifacts']['linux-aarch64']=dict(lock['artifacts']['darwin-arm64'],url='https://github.com/storytold/lightcraft/releases/download/v0.2.1/lightcraft-0.2.1-linux-x86_64.tar.gz')
  with tempfile.TemporaryDirectory() as tmp:
   home=Path(tmp)/'runtime'
   with patch.object(bootstrap,'download',side_effect=AssertionError('must not download')):
    with self.assertRaisesRegex(ValueError,'runtime_release_identity_mismatch'):bootstrap.install(lock,home,platform_key='linux-aarch64')
   self.assertFalse(home.exists())
if __name__=='__main__':unittest.main()
