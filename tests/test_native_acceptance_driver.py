"""合成图片验收驱动覆盖两个输入；原生调用全部替身，不安装 Lightcraft。"""
import copy,importlib.util,json,subprocess,tempfile,unittest,uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]

class NativeAcceptanceDriver(unittest.TestCase):
    def test_both_input_formats_get_before_after_and_independent_reopen(self):
        spec=importlib.util.spec_from_file_location('native_driver',ROOT/'scripts/native_acceptance.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        actual_load=m.load;gateway=actual_load('command_gateway');real_run=subprocess.run
        receipts={};settings={i:{'light':{'exposure':0},'crop':{'x':.2},'masks':[{'id':7}]} for i in (1,2)}
        observed=[];active=1
        def execute(argv,**kwargs):
            nonlocal active
            if argv[0]=='sips':return real_run(argv,**kwargs)
            if Path(argv[3]).name=='bootstrap.py':reply={'fixture':True,'status':'READY'}
            elif 'discover' in argv:reply={'commands':[{'id':x} for x in ('library.import','library.select','catalog.query','photo.inspect','develop.get','develop.set','app.export','library.info')], 'controls':[{'id':'light.exposure','min':-5,'max':5}]}
            else:
                plan=json.loads(Path(argv[argv.index('run')+1]).read_text());output=Path(argv[argv.index('--output')+1]);output.mkdir()
                library=Path(argv[argv.index('--library')+1]);library.mkdir(exist_ok=True)
                originals=Path(argv[argv.index('--input')+1]);rows=[]
                for index,step in enumerate(plan['steps']):
                    command=step['command'];params=step['params'];result={}
                    if command=='library.import':result={'imported':[1,2],'duplicates':[],'failed':[]}
                    if command=='library.select':active=params['active']
                    if command=='photo.inspect':result={'id':active,'source':{'type':'file','path':str(originals/('gradient.png' if active==1 else 'gradient.jpg'))}}
                    if command=='develop.get':result=copy.deepcopy(settings[active])
                    if command=='develop.set':settings[active]['light']['exposure']=params['value']
                    if command=='app.export':observed.append((active,'export',settings[active]['light']['exposure']))
                    if command=='library.info':result={'persistent':True,'unsavedOps':0};observed.append((active,'reopen',None))
                    rows.append({'index':index,'command':command,'status':'SUCCEEDED','native':{'result':result}})
                reply={'schemaVersion':1,'domain':'lightcraft','runId':str(uuid.uuid4()),'status':'NATIVE_EXIT_ZERO_REVIEW_REQUIRED','protocolComplete':True,
                       'planSha256':__import__('hashlib').sha256(json.dumps(plan,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
                       'libraryPath':str(library),'skillResourceSha256':gateway.capture_resources(m.SCRIPTS),'inputSha256':gateway.capture_inputs([originals]),'inputAfterSha256':gateway.capture_inputs([originals]),'steps':rows}
                receipts[output.name]=reply
            return subprocess.CompletedProcess(argv,0,json.dumps(reply),'')
        fake_gateway=SimpleNamespace(capture_inputs=gateway.capture_inputs,capture_resources=gateway.capture_resources,read_receipt=lambda path:{'compatible':True,'receipt':receipts[path.parent.name]})
        def load(name):
            if name=='command_gateway':return fake_gateway
            if name=='artifacts':return SimpleNamespace(verify=lambda path,root,expected:{'technicalStatus':'PASS','path':str(path),'fixtureOnly':True})
            return actual_load(name)
        with tempfile.TemporaryDirectory() as temporary,patch.object(m,'load',side_effect=load),patch.object(m.subprocess,'run',side_effect=execute):
            result=m.native(Path(temporary)/'work')
        self.assertEqual(result['nativeStatus'],'PASS',result)
        self.assertEqual({row[0] for row in observed},{1,2})
        for photo_id in (1,2):
            self.assertIn((photo_id,'export',0),observed)
            self.assertIn((photo_id,'export',.5),observed)
            self.assertIn((photo_id,'reopen',None),observed)

if __name__=='__main__':unittest.main()
