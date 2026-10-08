"""Windows 真实进程监督：仅确认启动进程，不推断后代或重放。"""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('supervisor',Path(__file__).resolve().parents[1]/'runtime/native_process.py');supervisor=importlib.util.module_from_spec(spec);spec.loader.exec_module(supervisor)
@unittest.skipUnless(os.name=='nt','requires actual Windows process APIs')
class WindowsSupervisor(unittest.TestCase):
 def test_windows_timeout_remains_unknown(self):
  with tempfile.TemporaryDirectory() as tmp:
   result=supervisor.supervise([sys.executable,'-c','import time; print("started",flush=True); time.sleep(30)'],Path(tmp),timeout=1)
   self.assertEqual(result['status'],'UNKNOWN');self.assertEqual(result['terminationScope'],'launch-process-only')
   self.assertTrue(result['launchProcessStopped']);self.assertFalse(result['descendantsConfirmedStopped']);self.assertFalse(result['automaticReplay'])
   self.assertIn('started',result['stdout']);self.assertTrue(result['logComplete'])
 def test_windows_stdin_and_complete_logs(self):
  with tempfile.TemporaryDirectory() as tmp:
   result=supervisor.supervise([sys.executable,'-c','import sys; print(sys.stdin.read()); print("stderr",file=sys.stderr)'],Path(tmp),timeout=10,stdin_data=b'one request\n')
   self.assertEqual(result['status'],'EXITED');self.assertEqual(result['exitCode'],0);self.assertTrue(result['logComplete'])
   self.assertEqual(result['stdout'].strip(),'one request');self.assertEqual(result['stderr'].strip(),'stderr')
if __name__=='__main__':unittest.main()
