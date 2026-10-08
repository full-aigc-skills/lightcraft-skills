"""安装完整性、平台与互斥测试；测试制品不执行。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]


class InstallerBoundaries(unittest.TestCase):
    def setup(self):
        path=ROOT/'runtime/bootstrap.py'
        spec=importlib.util.spec_from_file_location('bootstrap',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module,json.loads(path.with_name('runtime.lock.json').read_text())

    def test_unsupported_platform_has_no_side_effect(self):
        b,lock=self.setup()
        with tempfile.TemporaryDirectory() as temporary:
            home=Path(temporary)/'runtime'
            with self.assertRaisesRegex(ValueError,'unsupported_platform'):b.install(lock,home,platform_key='linux-x86_64')
            self.assertFalse(home.exists())

    def test_bad_archive_never_executes_and_no_destination(self):
        b,lock=self.setup()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);archive=root/'bad.zip';archive.write_bytes(b'bad archive')
            with patch.object(b.subprocess,'run',side_effect=AssertionError('must not execute')):
                with self.assertRaisesRegex(ValueError,'archive_checksum'):b.install(lock,root/'runtime',archive,'darwin-arm64')
            self.assertFalse((root/'runtime/lightcraft/0.2.1').exists())

    def test_traversal_archive_rejected_before_extract(self):
        b,_=self.setup()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);archive=root/'bad.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr('../escape','bad')
            with self.assertRaisesRegex(ValueError,'unsafe_archive'):b.extract(archive,root/'unpacked')
            self.assertFalse((root/'escape').exists())

    def test_bad_installation_receipt_preserved(self):
        b,lock=self.setup()
        with tempfile.TemporaryDirectory() as temporary:
            destination=Path(temporary)/'0.2.1';destination.mkdir()
            binary=destination/'lightcraft-cli';binary.write_bytes(b'fixture')
            expected=dict(lock['artifacts']['darwin-arm64'],binarySha256=b.digest(binary))
            receipt=destination/'installation.json';receipt.write_text('{}')
            with self.assertRaisesRegex(ValueError,'receipt_mismatch'):b.inspect_install(destination,'lightcraft-cli',expected)
            self.assertEqual(receipt.read_text(),'{}')

    def test_install_lock_blocks_without_downloading(self):
        import fcntl
        b,lock=self.setup()
        with tempfile.TemporaryDirectory() as temporary:
            home=Path(temporary);parent=home/'lightcraft';parent.mkdir()
            with (parent/'.install.lock').open('w') as stream:
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with patch.object(b,'LOCK_WAIT_SECONDS',.01),patch.object(b,'download',side_effect=AssertionError('must not download')):
                    with self.assertRaisesRegex(TimeoutError,'runtime_install_busy'):b.install(lock,home,platform_key='darwin-arm64')


if __name__=='__main__':unittest.main()
