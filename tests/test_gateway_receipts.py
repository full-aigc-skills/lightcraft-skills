"""任务回执与输入身份合同；全部子进程为模拟，不安装或运行原生工具。"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
DOMAIN=ROOT.name.removesuffix('-skills')

class ReceiptContract(unittest.TestCase):
    def setUp(self):
        self.scripts=ROOT/'skills'/f'{DOMAIN}-use'/'scripts'
        spec=importlib.util.spec_from_file_location('gateway',self.scripts/'command_gateway.py')
        self.g=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.g)

    def catalog(self):
        return [{'name':'doc_info','input_schema':{'type':'object','properties':{}}}] if DOMAIN=='printcraft' else [{'id':'file.new','params':'','menu':[]}]

    def plan(self,root):
        p=root/'plan.json'
        p.write_text(json.dumps({'domain':DOMAIN,'steps':[{'command':'doc_info' if DOMAIN=='printcraft' else 'file.new','params':{}}]}))
        return p

    def invoke(self,argv,side_effect):
        with patch.object(sys,'argv',['commands.py',*argv]),patch.object(self.g.subprocess,'run',side_effect=side_effect) as run,contextlib.redirect_stdout(io.StringIO()):
            result=self.g.main(DOMAIN,self.scripts)
            return result,run.call_count

    def test_receipt_binds_explicit_input_and_actual_runtime_lock(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/'input.bin';source.write_bytes(b'original input');output=root/'output'
            discovery=subprocess.CompletedProcess([],0,json.dumps(self.catalog()),'')
            success=subprocess.CompletedProcess([],0,'{"command":"file.new","ok":true,"result":{}}','')
            result,count=self.invoke(['run',str(self.plan(root)),'--output',str(output),'--input',str(source)],[discovery,success])
            self.assertEqual((result,count),(0,2))
            receipt=json.loads((output/'receipt.json').read_text())
            self.assertEqual(receipt['inputSha256'][str(source)],hashlib.sha256(b'original input').hexdigest())
            self.assertEqual(receipt['runtimeLockSha256'],hashlib.sha256((self.scripts/'runtime.lock.json').read_bytes()).hexdigest())
            self.assertFalse(receipt['completeAcceptance'])
            self.assertEqual(receipt['status'],'NATIVE_EXIT_ZERO_REVIEW_REQUIRED')

    def test_changed_input_during_discovery_blocks_native_edit(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/'input.bin';source.write_bytes(b'original');output=root/'output'
            def changed(argv,**kwargs):
                source.write_bytes(b'changed while installing')
                return subprocess.CompletedProcess([],0,json.dumps(self.catalog()),'')
            result,count=self.invoke(['run',str(self.plan(root)),'--output',str(output),'--input',str(source)],changed)
            self.assertEqual((result,count),(1,1))
            self.assertFalse(output.exists())

    def test_input_missing_is_rejected_before_discovery(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            result,count=self.invoke(['run',str(self.plan(root)),'--output',str(root/'out'),'--input',str(root/'missing')],AssertionError('must not start'))
            self.assertEqual((result,count),(1,0))

    def test_timeout_keeps_partial_logs_and_unknown_without_replay(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);output=root/'output'
            discovery=subprocess.CompletedProcess([],0,json.dumps(self.catalog()),'')
            timeout=subprocess.TimeoutExpired(['native'],900,output=b'partial output',stderr=b'partial error')
            result,count=self.invoke(['run',str(self.plan(root)),'--output',str(output)],[discovery,timeout])
            self.assertEqual((result,count),(1,2))
            receipt=json.loads((output/'receipt.json').read_text())
            self.assertEqual(receipt['status'],'UNKNOWN')
            self.assertEqual(receipt['stdout'],'partial output')
            self.assertEqual(receipt['stderr'],'partial error')
            self.assertFalse(receipt['automaticReplay'])

    def test_changed_input_on_zero_exit_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/'input.bin';source.write_bytes(b'original');output=root/'output';calls=[]
            def native(argv,**kwargs):
                calls.append(argv)
                if len(calls)==1:return subprocess.CompletedProcess([],0,json.dumps(self.catalog()),'')
                source.write_bytes(b'changed by native operation')
                return subprocess.CompletedProcess([],0,'{"command":"file.new","ok":true,"result":{}}','')
            result,count=self.invoke(['run',str(self.plan(root)),'--output',str(output),'--input',str(source)],native)
            self.assertEqual((result,count),(1,2))
            self.assertEqual(json.loads((output/'receipt.json').read_text())['status'],'INPUT_CHANGED_REVIEW_REQUIRED')

if __name__=='__main__':unittest.main()
