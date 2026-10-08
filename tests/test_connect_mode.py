"""连接模式的安装前拒绝、原生身份与只读协议边界。"""
import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'runtime'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class ConnectMode(unittest.TestCase):
    def test_mcp_and_run_mode_identity(self):
        mode=load('mode_contract')
        self.assertEqual(mode.inspect_mode(['run','library.info'])['mode'],'Headless')
        self.assertEqual(mode.inspect_mode(['mcp'])['transport'],'stdio-mcp')
        value=mode.inspect_mode(['run','--connect','127.0.0.1:18091','library.info'])
        self.assertEqual(value['mode'],'Connect');self.assertEqual(value['connectAddress'],'127.0.0.1:18091')
        self.assertTrue(value['readOnly']);self.assertTrue(value['nativeMayRetryReads'])

    def test_connect_headless_conflicts_before_runtime_access(self):
        invalid=[['run','--connect','--library','/missing','library.info'],
                 ['mcp','--connect','--headless'],['mcp','--headless','--connect'],
                 ['mcp','--connect','--demo'],['mcp','--connect=127.0.0.1:18091','photo.png']]
        for argv in invalid:
            with self.subTest(argv=argv),tempfile.TemporaryDirectory() as temporary:
                home=Path(temporary)/'never-installed'
                result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'runtime/cli.py'),'--runtime-home',str(home),'--require-installed','--',*argv],capture_output=True,text=True)
                self.assertEqual(result.returncode,1)
                self.assertIn('mode_conflict',json.loads(result.stdout)['error'])
                self.assertFalse(home.exists())

    def test_native_remote_write_retries_cannot_be_exposed(self):
        mode=load('mode_contract')
        with self.assertRaisesRegex(ValueError,'connect_write_unsupported_native_retry'):
            mode.inspect_mode(['run','--connect','develop.set','light.exposure=1'])
        with self.assertRaisesRegex(ValueError,'bounded_readonly'):
            mode.inspect_mode(['mcp','--connect'])

    def test_malformed_mcp_reply_cannot_become_a_success(self):
        mode=load('mode_contract');requests=mode.probe_requests()
        replies=[{'jsonrpc':'2.0','id':1,'result':{'serverInfo':[]}},
                 {'jsonrpc':'2.0','id':2,'result':{'tools':[]}},
                 {'jsonrpc':'2.0','id':3,'result':{}}]
        self.assertEqual(mode.classify_probe(requests,replies,'0.2.1')['status'],'UNKNOWN')
        changed=mode.probe_requests();changed[0]['id']=True
        with self.assertRaises(ValueError):mode.inspect_mode(['mcp','--connect'],changed)

    def test_connect_writes_reject_even_when_installation_would_be_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            home=Path(temporary)/'never-installed'
            process=subprocess.run([sys.executable,'-I','-B',str(ROOT/'runtime/cli.py'),'--runtime-home',str(home),'--','run','--connect','develop.set','light.exposure=1'],capture_output=True,text=True)
            self.assertEqual(process.returncode,1)
            self.assertIn('connect_write_unsupported_native_retry',json.loads(process.stdout)['error'])
            self.assertFalse(home.exists())

    def test_readonly_script_checked_as_a_whole(self):
        mode=load('mode_contract')
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'steps.jsonl'
            path.write_text(json.dumps({'command':'library.info','params':{}})+'\n'+json.dumps({'command':'develop.set','params':{'control':'light.exposure','value':1}})+'\n')
            with self.assertRaisesRegex(ValueError,'connect_write_unsupported_native_retry'):
                mode.inspect_mode(['run','--script',str(path),'--connect'])

    def test_mcp_requests_are_closed_readonly_and_identity_bound(self):
        mode=load('mode_contract');requests=mode.probe_requests()
        value=mode.inspect_mode(['mcp','--connect','127.0.0.1:18091'],requests)
        self.assertEqual(value['mode'],'Connect');self.assertTrue(value['readOnly'])
        for mutation in [dict(jsonrpc='2.0',id=4,method='tools/call',params={'name':'set_develop','arguments':{'values':{'light.exposure':1}}}),dict(jsonrpc='2.0',id=3,method='ping',params={})]:
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                mode.inspect_mode(['mcp','--connect'],requests+[mutation])
        with self.assertRaisesRegex(ValueError,'mode_conflict'):
            mode.inspect_mode(['mcp','--connect','--library','/tmp/not-opened'],requests)

    def test_mcp_failure_and_not_saved_share_existing_execution_semantics(self):
        mode=load('mode_contract');requests=mode.probe_requests()
        replies=[{'jsonrpc':'2.0','id':1,'result':{'serverInfo':{'name':'lightcraft','version':'0.2.1'}}},
                 {'jsonrpc':'2.0','id':2,'result':{'tools':[]}},
                 {'jsonrpc':'2.0','id':3,'error':{'code':-32603,'message':'NotSaved: saved in memory but not written to disk'}}]
        result=mode.classify_probe(requests,replies,'0.2.1')
        self.assertEqual(result['status'],'PERSISTENCE_UNCONFIRMED')
        self.assertEqual(result['steps'][2]['status'],'APPLIED_NOT_SAVED')
        result=mode.classify_probe(requests,replies[:2],'0.2.1')
        self.assertEqual(result['status'],'UNKNOWN')

if __name__=='__main__':unittest.main()
