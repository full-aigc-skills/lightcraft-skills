"""RAW 验收驱动协议回归；全部模拟，不执行 Lightcraft、不安装。"""
import hashlib,importlib.util,json
from pathlib import Path
from types import SimpleNamespace
import subprocess,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]

def driver():
    spec=importlib.util.spec_from_file_location('raw_driver',ROOT/'scripts/raw_acceptance.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class RawAcceptanceDriver(unittest.TestCase):
    def test_native_nullable_reason_is_not_boolean(self):
        m=driver()
        self.assertEqual(m.decode_mode({'kind':'raw','previewOnly':'unsupported compression'}),'PREVIEW_FALLBACK')
        self.assertEqual(m.decode_mode({'kind':'raw','previewOnly':None}),'FULL_RAW_REPORTED')
        for photo in ({'kind':'raw'}, {'kind':'image','previewOnly':None}, {'kind':'raw','previewOnly':False}):
            self.assertEqual(m.decode_mode(photo),'UNKNOWN')

    def test_unconfirmed_reopen_and_protocol_never_pass(self):
        for fault in ('persistence','identity','wrong_source','receipt_status','none','preview_fallback'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary).resolve();source=root/'mock.nef';source.write_bytes(b'mock RAW bytes')
                m=driver();settings={'light':{'exposure':.25}}
                photo={'id':1,'source':{'type':'file','path':str(source)}}
                if fault=='identity':photo={'id':1}
                if fault=='wrong_source':photo={'id':1,'source':{'type':'file','path':str(root/'other.nef')}}
                def receipt(path):
                    name=path.parent.name
                    if name=='import':results=[{'imported':[1],'duplicates':[],'failed':[]},{}]
                    elif name=='edit-export':results=[{}, {}, settings,{}, {'photos':[{'id':1,'kind':'raw','previewOnly':'unsupported compression' if fault=='preview_fallback' else None}]},photo]
                    else:results=[{},photo,settings,{'persistent':fault!='persistence','unsavedOps':0}]
                    commands={'import':['library.import','catalog.query'], 'edit-export':['library.select','develop.set','develop.get','app.export','catalog.query','photo.inspect'], 'reopen':['library.select','photo.inspect','develop.get','library.info']}[name]
                    plan=json.loads((path.parent.parent/(name+'-plan.json')).read_text())
                    return {'compatible':True,'receipt':{'schemaVersion':1,'domain':'lightcraft','runId':name,'status':'UNKNOWN' if fault=='receipt_status' else 'NATIVE_EXIT_ZERO_REVIEW_REQUIRED','protocolComplete':True,
                        'planSha256':hashlib.sha256(json.dumps(plan,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
                        'libraryPath':str(path.parent.parent/'library'),'skillResourceSha256':{'test':'fixture'},
                        'inputSha256':{str(source):hashlib.sha256(source.read_bytes()).hexdigest()},'inputAfterSha256':{str(source):hashlib.sha256(source.read_bytes()).hexdigest()},
                        'steps':[{'index':i,'command':cmd,'status':'SUCCEEDED','native':{'result':r}} for i,(cmd,r) in enumerate(zip(commands,results))]}}
                artifacts=SimpleNamespace(sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest(),verify=lambda *a,**k:{'technicalStatus':'PASS'})
                gateway=SimpleNamespace(read_receipt=receipt,capture_inputs=lambda paths:{str(source):artifacts.sha(source)},capture_resources=lambda path:{'test':'fixture'})
                bootstrap=SimpleNamespace(doctor=lambda *a:{'status':'READY'})
                with patch.object(m,'load',side_effect=lambda name:{'bootstrap':bootstrap,'artifacts':artifacts,'command_gateway':gateway}[name]),patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'','')):
                    result=m.validate({'samples':[{'path':str(source),'sha256':artifacts.sha(source)}]},root/'mock-runtime',root/'work')
                record=result['samples'][0]
                if fault in ('none','preview_fallback'):
                    self.assertEqual(record['nativeAcceptance'],'PASS' if fault=='none' else 'PASS_WITH_PREVIEW_FALLBACK')
                    if fault=='preview_fallback':self.assertEqual(record['fullRawAcceptance'],'NOT_PROVEN')
                else:
                    self.assertEqual(record['nativeAcceptance'],'FAIL_OR_UNSUPPORTED')
                    self.assertIn({'persistence':'persistence_unconfirmed','identity':'photo_mismatch','wrong_source':'photo_mismatch','receipt_status':'execution_unconfirmed'}[fault],record['error'])

if __name__=='__main__':unittest.main()
