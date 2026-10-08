"""只消费已有安装的执行模式；缺失时不能退回安装器。"""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class RequireInstalled(unittest.TestCase):
    def test_launcher_and_gateway_missing_runtime_have_no_install_side_effect(self):
        for entry in ('cli.py','commands.py'):
            with self.subTest(entry=entry),tempfile.TemporaryDirectory() as temporary:
                home=Path(temporary)/'missing-runtime'
                argv=[sys.executable,'-I','-B',str(ROOT/'runtime'/entry)]
                if entry=='commands.py':argv+=['discover']
                argv+=['--runtime-home',str(home),'--require-installed']
                if entry=='cli.py':argv+=['--','commands','--json']
                result=subprocess.run(argv,capture_output=True,text=True)
                self.assertEqual(result.returncode,1,result.stderr)
                self.assertIn('require_installed_runtime_not_ready',json.loads(result.stdout)['error'])
                self.assertFalse(home.exists())

if __name__=='__main__':unittest.main()
