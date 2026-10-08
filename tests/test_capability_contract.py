"""能力快照和协议版本回归；不运行原生。"""
import contextlib
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


def gateway():
    path=ROOT/'runtime/command_gateway.py'
    spec=importlib.util.spec_from_file_location('gateway',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class CapabilityContract(unittest.TestCase):
    def test_legacy_receipt_is_read_only_without_modification(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'legacy.json';path.write_text('{"status":"old"}')
            before=path.read_bytes();result=gateway().read_receipt(path)
            self.assertTrue(result['readOnly']);self.assertFalse(result['compatible'])
            self.assertEqual(path.read_bytes(),before)

    def test_offline_discovery_never_authorizes_execution(self):
        g=gateway()
        with tempfile.TemporaryDirectory() as temporary:
            catalog=Path(temporary)/'catalog.json';catalog.write_text('[{"id":"library.info"}]')
            output=io.StringIO()
            with patch.object(sys,'argv',['commands.py','discover','--catalog',str(catalog)]),patch.object(g.subprocess,'run',side_effect=AssertionError('offline must not execute')),contextlib.redirect_stdout(output):
                self.assertEqual(g.main('lightcraft',ROOT/'runtime'),0)
            reply=json.loads(output.getvalue())
            self.assertEqual(reply['mode'],'offline')
            self.assertFalse(reply['executionAllowed'])
            self.assertIsNone(reply['executableIdentity'])
            self.assertEqual(len(reply['catalogSha256']),64)

    def test_offline_catalog_cannot_be_used_for_run(self):
        g=gateway()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);plan=root/'plan.json';plan.write_text('{"domain":"lightcraft","steps":[{"command":"library.info","params":{}}]}')
            with patch.object(sys,'argv',['commands.py','run',str(plan),'--catalog',str(root/'catalog.json'),'--output',str(root/'run')]),patch.object(g.subprocess,'run',side_effect=AssertionError('must not execute')),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(g.main('lightcraft',ROOT/'runtime'),1)
            self.assertFalse((root/'run').exists())

    def test_snapshot_coverage_reports_new_unassigned_command(self):
        path=ROOT/'runtime/coverage.py';spec=importlib.util.spec_from_file_location('coverage',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=module.report({'commands':[{'id':'new.feature'},{'id':'develop.get'}],'mode':'offline'})
        self.assertEqual(result['uncovered'],['new.feature'])
        self.assertEqual(result['commands'][1]['verification'],'NOT_RUN')

    def test_receipt_examples_obey_current_schema(self):
        g=gateway()
        paths=list((ROOT/'examples/receipts').glob('*.json'))
        self.assertEqual(len(paths),3)
        for path in paths:
            with self.subTest(path=path):
                result=g.read_receipt(path)
                self.assertTrue(result['compatible'])
                self.assertFalse(result['receipt']['completeAcceptance'])


if __name__=='__main__':unittest.main()
