"""Windows 进程架构、固定制品和安装身份回归。"""
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bootstrap',ROOT/'runtime/bootstrap.py');bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap)
class WindowsInstaller(unittest.TestCase):
 def test_process_architecture_not_only_os_machine(self):
  for machine,bits,expected in [('AMD64',64,'windows-x86_64'),('AMD64',32,'windows-x86'),('ARM64',64,'windows-arm64')]:
   with patch.object(bootstrap.platform,'system',return_value='Windows'),patch.object(bootstrap.platform,'machine',return_value=machine),patch.object(bootstrap.struct,'calcsize',return_value=bits//8):
    self.assertEqual(bootstrap.current_platform(),expected)
 def test_windows_exe_install_reuse_and_readonly_doctor(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);archive=root/'release.zip'
   with zipfile.ZipFile(archive,'w') as out:
    out.writestr('release/lightcraft-cli.exe',b'fixed-cli');out.writestr('release/LICENSE-MIT','license')
   key='windows-x86_64';expected={'url':'https://github.com/storytold/lightcraft/releases/download/v0.2.1/lightcraft-0.2.1-windows-x64-portable.zip','archiveSha256':bootstrap.digest(archive),'binarySha256':__import__('hashlib').sha256(b'fixed-cli').hexdigest(),'versionOutput':'lightcraft-cli 0.2.1'}
   lock={'artifact':'lightcraft-cli','resolvedVersion':'0.2.1','artifacts':{key:expected}}
   with patch.object(bootstrap.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'lightcraft-cli 0.2.1\n','')) as run:
    result=bootstrap.install(lock,root/'runtime',archive,platform_key=key)
    self.assertTrue(result['executable'].endswith('lightcraft-cli.exe'));self.assertFalse(result['reused'])
    self.assertTrue(bootstrap.install(lock,root/'runtime',archive,platform_key=key)['reused']);self.assertEqual(run.call_count,1)
   with patch.object(bootstrap.subprocess,'run',side_effect=AssertionError('doctor must not execute')):
    self.assertEqual(bootstrap.doctor(lock,root/'runtime',platform_key=key)['status'],'READY')
 @unittest.skipUnless(os.name=='nt','requires actual Windows locking APIs')
 def test_windows_lock_contention_releases_on_process_exit(self):
  with tempfile.TemporaryDirectory() as tmp:
   parent=Path(tmp);ready=parent/'ready'
   code="import importlib.util,sys,time; from pathlib import Path; spec=importlib.util.spec_from_file_location('b',sys.argv[1]); b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b); "+"\nwith b.installation_mutex(Path(sys.argv[2])):\n Path(sys.argv[3]).write_text('ready');time.sleep(30)"
   process=subprocess.Popen([sys.executable,'-I','-B','-c',code,str(ROOT/'runtime/bootstrap.py'),str(parent),str(ready)])
   try:
    deadline=time.monotonic()+10
    while not ready.exists():
     if process.poll() is not None or time.monotonic()>deadline:self.fail('lock holder failed to start')
     time.sleep(.05)
    with patch.object(bootstrap,'LOCK_WAIT_SECONDS',.1):
     with self.assertRaisesRegex(TimeoutError,'runtime_install_busy'):
      with bootstrap.installation_mutex(parent):self.fail('contended lock acquired')
   finally:process.terminate();process.wait(timeout=10)
   with bootstrap.installation_mutex(parent):self.assertTrue(ready.exists())
 def test_wrong_windows_asset_rejected_before_writes(self):
  lock=json.loads((ROOT/'runtime/runtime.lock.json').read_text())
  lock['artifacts']['windows-x86_64']=dict(lock['artifacts']['darwin-arm64'],url='https://github.com/storytold/lightcraft/releases/download/v0.2.1/lightcraft-0.2.1-windows-x86-portable.zip')
  with tempfile.TemporaryDirectory() as tmp:
   home=Path(tmp)/'runtime'
   with self.assertRaisesRegex(ValueError,'runtime_release_identity_mismatch'):bootstrap.install(lock,home,platform_key='windows-x86_64')
   self.assertFalse(home.exists())
if __name__=='__main__':unittest.main()
