"""监督真实测试进程，绝不调用原生照片程序。"""
import importlib.util
from pathlib import Path
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeProcess(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location('supervisor', ROOT / 'runtime/native_process.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    def test_timeout_preserves_logs_and_never_confirms_descendants(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.module().supervise([sys.executable, '-c', 'import time; print("partial", flush=True); time.sleep(10)'], Path(temporary), .1)
            self.assertEqual(result['status'], 'UNKNOWN')
            self.assertIn('partial', result['stdout'])
            self.assertFalse(result['descendantsConfirmedStopped'])
            self.assertTrue(result['launchProcessStopped'])

    def test_large_log_is_on_disk_with_bounded_tail(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.module().supervise([sys.executable, '-c', 'print("x" * 200000)'], Path(temporary))
            self.assertEqual(result['status'], 'EXITED')
            self.assertTrue(result['stdoutTruncated'])
            self.assertLessEqual(len(result['stdout']), 65536)
            self.assertGreater((Path(temporary) / 'stdout.log').stat().st_size, 200000)

    def test_owner_observes_stop_request_without_claiming_cancellation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);stop=root/'stop.json'
            timer=threading.Timer(.2,lambda:stop.write_text('{}'));timer.start()
            try:
                result=self.module().supervise([sys.executable,'-c','import time; time.sleep(10)'],root/'logs',timeout=5,stop_file=stop)
            finally:timer.join()
            self.assertEqual(result['status'],'UNKNOWN')
            self.assertTrue(result['launchProcessStopped'])
            self.assertFalse(result['descendantsConfirmedStopped'])


if __name__ == '__main__':
    unittest.main()
