"""执行协议故障注入；不下载或启动 Lightcraft。"""
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

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/lightcraft-use/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExecutionProtocol(unittest.TestCase):
    def test_inner_timeout_is_unknown_not_ordinary_failure(self):
        gateway = load('command_gateway')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = root / 'plan.json'
            plan.write_text(json.dumps({'domain': 'lightcraft', 'steps': [{'command': 'library.info', 'params': {}}]}))
            results = [subprocess.CompletedProcess([], 0, '[{"id":"library.info"}]', ''),
                       subprocess.CompletedProcess([], 1, '{"result":"unknown","error":"inner timeout"}', '')]
            with patch.object(sys, 'argv', ['commands.py', 'run', str(plan), '--output', str(root / 'run')]), patch.object(gateway.subprocess, 'run', side_effect=results), contextlib.redirect_stdout(io.StringIO()):
                gateway.main('lightcraft', SCRIPTS)
            receipt = json.loads((root / 'run/receipt.json').read_text())
            self.assertEqual(receipt['status'], 'UNKNOWN')
            self.assertFalse(receipt['automaticReplay'])

    def parse(self, text, code=0):
        gateway = load('command_gateway')
        self.assertTrue(callable(getattr(gateway, 'parse_results', None)), 'missing step protocol interpreter')
        return gateway.parse_results([{'command': 'a'}, {'command': 'b'}], text.splitlines(), code)

    def test_invalid_missing_duplicate_truncated_results_are_unknown(self):
        for text in ['bad', '{"command":"a","ok":true}', '{"command":"a","ok":true}\n{"command":"a","ok":true}', '{"command":"a","ok":true}\n{']:
            with self.subTest(text=text):
                result = self.parse(text)
                self.assertEqual(result['status'], 'UNKNOWN')

    def test_partial_failure_leaves_later_steps_not_executed(self):
        result = self.parse('{"command":"a","ok":false,"error":"bad parameter"}', 1)
        self.assertEqual([r['status'] for r in result['steps']], ['FAILED', 'NOT_EXECUTED'])

    def test_not_saved_is_distinct_from_failed_edit(self):
        result = self.parse('{"command":"a","ok":false,"error":"saved in memory but not written to disk: full"}', 1)
        self.assertEqual(result['steps'][0]['status'], 'APPLIED_NOT_SAVED')
        self.assertEqual(result['status'], 'PERSISTENCE_UNCONFIRMED')

    def test_native_ok_with_partial_import_is_not_all_success(self):
        g=load('command_gateway')
        result=g.parse_results([{'command':'library.import'}],['{"command":"library.import","ok":true,"result":{"imported":[1],"failed":[["bad","decode"]]}}'],0)
        self.assertEqual(result['status'],'FAILED_OR_PARTIAL')
        self.assertEqual(result['steps'][0]['status'],'PARTIAL')

    def test_known_export_cannot_overwrite_original_or_hardlink(self):
        gateway = load('command_gateway')
        self.assertTrue(callable(getattr(gateway, 'preflight_writes', None)))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'original.png'
            source.write_bytes(b'original')
            target = root / 'alias.png'
            target.hardlink_to(source)
            for path in [source, target]:
                with self.assertRaises(ValueError):
                    gateway.preflight_writes({'steps': [{'command': 'app.export', 'params': {'path': str(path)}}]}, {str(source): 'digest'})

    def test_doctor_missing_runtime_does_not_create_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / 'missing'
            result = subprocess.run([sys.executable, '-I', '-B', str(SCRIPTS / 'bootstrap.py'), '--no-install', '--runtime-home', str(runtime)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'MISSING')
            self.assertFalse(runtime.exists())


if __name__ == '__main__':
    unittest.main()
