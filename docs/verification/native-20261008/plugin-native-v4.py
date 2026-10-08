from pathlib import Path
import json,subprocess,sys
root=Path('/tmp/lightcraft-acceptance-HoMkD5').resolve();cache=Path('/Users/wandl/.codex/plugins/cache/lightcraft-acceptance/lightcraft/0.1.0-dev.1');task=root/'plugin-task-v4';library=root/'plugin-library-v4';exports=root/'plugin-exports-v4';exports.mkdir();original=root/'png-jpeg/originals/gradient.png';runtime=root/'png-jpeg/runtime'
def step(c,**p):return {'command':c,'params':p}
def controller(action,payload=None):
 argv=[sys.executable,'-I','-B',str(cache/'scripts/controller.py'),action,str(task)]
 if payload is not None:
  f=root/('plugin-'+action+'.json');f.write_text(json.dumps(payload));argv+=['--payload',str(f)]
 if action=='run':argv+=['--runtime-home',str(runtime)]
 p=subprocess.run(argv,capture_output=True,text=True)
 if p.returncode:raise ValueError(p.stdout[-3000:]+p.stderr[-1000:])
 return json.loads(p.stdout)
plan={'domain':'lightcraft','steps':[step('library.import',paths=[str(original)],mode='add'),step('library.select',ids=[1],active=1),step('photo.inspect',id=1),step('develop.get',id=1),step('app.export',path=str(exports/'before.png'),format='png',width=96),step('develop.set',control='light.exposure',value=.5),step('develop.get',id=1),step('app.export',path=str(exports/'edited.png'),format='png',width=96)]}
controller('init',{'goal':{'request':'将合成渐变照片曝光提高 0.5，保留渐变形状和颜色连续性，导出 96 像素宽 PNG。'},'plan':plan,'inputs':[str(original)],'library':str(library),'output_root':str(exports),'max_revisions':2});state=controller('run');assert state['status']=='VERIFYING',state['status']
receipt=json.loads(Path(state['receiptPath']).read_text());assert receipt['steps'][0]['native']['result']['imported']==[1]
reopen=root/'plugin-reopen-v4';rp=root/'plugin-reopen-plan.json';rp.write_text(json.dumps({'domain':'lightcraft','steps':[step('library.select',ids=[1],active=1),step('photo.inspect',id=1),step('develop.get',id=1),step('library.info')]}));subprocess.run([sys.executable,'-I','-B',str(cache/'skills/lightcraft-use/scripts/commands.py'),'run',str(rp),'--runtime-home',str(runtime),'--require-installed','--library',str(library),'--input',str(original),'--output-root',str(exports),'--output',str(reopen)],stdout=subprocess.DEVNULL,check=True)
request=controller('review-request',{'candidates':[{'path':str(exports/'edited.png'),'expected':{'format':'png','width':96,'height':64,'bitDepth':8}}],'settings':receipt['steps'][6]['native']['result'],'rubric_version':'synthetic-gradient-v1','reopen_evidence':{'receiptPath':str(reopen/'receipt.json')}});(root/'plugin-review-request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2));print(json.dumps({'status':'AWAITING_REVIEW','task':str(task),'before':str(exports/'before.png'),'candidate':str(exports/'edited.png'),'requestId':request['requestId']},ensure_ascii=False))
