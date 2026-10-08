"""真实 Python 包装链 + 假原生制品；不下载或执行 Lightcraft。"""
import hashlib,json,platform,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FAKE="#!/usr/bin/env python3\nimport json,sys,time\nargs=sys.argv[1:]\nif args[:1]==['commands']:print(json.dumps([{'id':'library.info'},{'id':'develop.get'}]))\nelif args[:1]==['controls']:print('[]')\nelif args[:1]==['run']:\n for line in open(args[args.index('--script')+1]):\n  step=json.loads(line)\n  print(json.dumps({'command':step['command'],'ok':True,'result':{'fixture':True}}),flush=True)\n  if step['params'].get('sleep'):time.sleep(10)\nelse:print('lightcraft-cli 0.2.1')\n"

class WrapperIntegration(unittest.TestCase):
    def fixture(self,root):
        scripts=root/'独立 技能/scripts';shutil.copytree(ROOT/'runtime',scripts)
        key=platform.system().lower()+'-'+platform.machine().lower()
        runtime=root/'runtime';destination=runtime/'lightcraft/0.2.1';destination.mkdir(parents=True)
        binary=destination/'lightcraft-cli';binary.write_text(FAKE);binary.chmod(0o755)
        lock=json.loads((scripts/'runtime.lock.json').read_text())
        expected=next(iter(lock['artifacts'].values()))
        expected['binarySha256']=hashlib.sha256(binary.read_bytes()).hexdigest()
        lock['artifacts']={key:expected}
        (scripts/'runtime.lock.json').write_text(json.dumps(lock))
        (destination/'installation.json').write_text(json.dumps(dict(expected,name='lightcraft',version='0.2.1')))
        return scripts,runtime

    def invoke(self,root,sleep=False):
        scripts,runtime=self.fixture(root)
        plan=root/'plan.json'
        plan.write_text(json.dumps({'domain':'lightcraft','steps':[{'command':'library.info','params':{'sleep':sleep}},{'command':'develop.get','params':{}}]}))
        result=subprocess.run([sys.executable,'-I','-B',str(scripts/'commands.py'),'run',str(plan),'--runtime-home',str(runtime),'--require-installed','--output',str(root/'run'),'--timeout','0.2' if sleep else '5'],capture_output=True,text=True,timeout=10)
        return result,json.loads((root/'run/receipt.json').read_text())

    def test_wrapper_chain_preserves_native_timeout_and_partial_step(self):
        with tempfile.TemporaryDirectory() as temporary:
            result,receipt=self.invoke(Path(temporary),True)
            self.assertEqual(result.returncode,1,result.stdout+result.stderr)
            self.assertEqual(receipt['status'],'UNKNOWN')
            self.assertEqual(receipt['steps'][0]['status'],'SUCCEEDED')
            self.assertEqual(receipt['steps'][1]['status'],'UNKNOWN')
            self.assertEqual(receipt['process']['error'],'TimeoutExpired')
            self.assertFalse(receipt['process']['descendantsConfirmedStopped'])

    def test_wrapper_chain_binds_actual_fixture_binary_and_steps(self):
        with tempfile.TemporaryDirectory() as temporary:
            result,receipt=self.invoke(Path(temporary))
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(receipt['status'],'NATIVE_EXIT_ZERO_REVIEW_REQUIRED')
            self.assertEqual([r['status'] for r in receipt['steps']],['SUCCEEDED','SUCCEEDED'])
            self.assertEqual(receipt['runtimeIdentity']['binarySha256'],hashlib.sha256(FAKE.encode()).hexdigest())
            self.assertTrue(Path(receipt['process']['logDirectory'],'stdout.log').is_file())

if __name__=='__main__':unittest.main()
