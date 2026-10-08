"""只读 MCP 探测的封闭请求、缺失依赖与错误回执。"""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class MCPProbe(unittest.TestCase):
    def test_missing_runtime_records_not_started_without_install(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);out=root/'probe';home=root/'not-installed'
            process=subprocess.run([sys.executable,'-I','-B',str(ROOT/'runtime/session_probe.py'),'--output',str(out),'--runtime-home',str(home)],capture_output=True,text=True)
            self.assertEqual(process.returncode,1)
            receipt=json.loads((out/'receipt.json').read_text())
            self.assertEqual(receipt['status'],'FAILED_OR_PARTIAL')
            self.assertTrue(all(s['status']=='NOT_EXECUTED' for s in receipt['steps']))
            self.assertFalse(receipt['automaticReplay']);self.assertFalse(home.exists())
            self.assertEqual(receipt['backendSessionIdentity'],'NOT_PROVIDED_BY_NATIVE_PROTOCOL')

if __name__=='__main__':unittest.main()
