"""验收身份失效与发行门禁；不创建 Git、下载或发布。"""
import importlib.util
from pathlib import Path
import tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
def module():
    spec=importlib.util.spec_from_file_location('verify_evidence',ROOT/'scripts/verify_evidence.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
class EvidenceIdentity(unittest.TestCase):
    def test_schema_workflow_and_readme_changes_expire_evidence(self):
        m=module()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for relative in ('schemas/task.json','.github/workflows/test.yml','README.md','licenses/Apache-2.0.txt','examples/receipts/success.json','scripts/craft_exchange.ts','tests/exchange/contract.test.ts'):
                path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('old')
                report={'schemaVersion':1,'sourceFingerprint':m.fingerprint(root),'layers':{k:{'status':'NOT_RUN'} for k in ('structure','mock','native','host','visual','platform','remoteCI')}}
                self.assertEqual(m.validate(root,report)['source'],'CURRENT')
                path.write_text('new')
                with self.assertRaisesRegex(ValueError,'stale'):m.validate(root,report)
    def test_pass_without_evidence_is_rejected(self):
        m=module()
        with tempfile.TemporaryDirectory() as temporary:
            report={'schemaVersion':1,'sourceFingerprint':m.fingerprint(temporary),'layers':{k:{'status':'PASS'} for k in ('structure','mock','native','host','visual','platform','remoteCI')}}
            with self.assertRaisesRegex(ValueError,'without_artifact'):m.validate(temporary,report)
if __name__=='__main__':unittest.main()
