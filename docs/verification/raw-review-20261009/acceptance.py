"""真实 RAW 候选失败审阅，保持技术验收与视觉交付分离。"""
from pathlib import Path
import json,hashlib,subprocess,sys
B=Path('/Users/wandl/workspaces/workspace-agent-skills');P=B/'full-aigc-plugins-repositories/lightcraft-plugin';W=B/'evaluation-results/lightcraft-raw-review-20261009';PY='/Users/wandl/.local/bin/python3.12';C=P/'scripts/controller.py';task=W/'task';runtime=B/'evaluation-results/lightcraft-connect-20261008/runtime';original=B/'evaluation-results/lightcraft-raw-20261008/samples/nikon-d2h-1.nef';out=W/'exports/nikon-raw.png'
def call(action,payload=None,expect=0):
 args=[PY,'-I','-B',str(C),action,str(task)]
 if payload is not None:
  path=W/(action+'-payload.json');path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');args+=['--payload',str(path)]
 if action=='run':args+=['--runtime-home',str(runtime)]
 result=subprocess.run(args,capture_output=True,text=True,timeout=120);(W/(action+'-stdout.json')).write_text(result.stdout);(W/(action+'-stderr.log')).write_text(result.stderr);assert result.returncode==expect,(action,result.stdout,result.stderr);return json.loads(result.stdout)
if len(sys.argv)==1:
 assert not task.exists();(W/'exports').mkdir(exist_ok=True)
 def step(c,**params):return {'command':c,'params':params}
 plan={'domain':'lightcraft','steps':[step('library.import',paths=[str(original)],mode='add'),step('library.select',ids=[1],active=1),step('develop.set',control='light.exposure',value=.25),step('develop.get',id=1),step('app.export',path=str(out),format='png',width=256),step('catalog.query',limit=10),step('photo.inspect',id=1)]}
 state=call('init',{'goal':{'request':'验证 Nikon D2H RAW 偏色候选在视觉 FAIL 后不可交付','sampleSha256':hashlib.sha256(original.read_bytes()).hexdigest()},'plan':plan,'inputs':[str(original)],'library':str(W/'library'),'output_root':str(W/'exports')})
 state=call('run');assert state['status']=='VERIFYING',state
 receipt=json.loads(Path(state['receiptPath']).read_text());settings=next(row['native']['result'] for row in receipt['steps'] if row['command']=='develop.get')
 request=call('review-request',{'candidates':[{'path':str(out),'expected':{'format':'png','width':256}}],'settings':settings,'rubric_version':'raw-color-visual-v1'})
 print(json.dumps({'state':'AWAITING_ACTUAL_VISUAL_INSPECTION','image':str(out),'bindingSha256':request['bindingSha256']}))
else:
 assert sys.argv[1]=='record-fail';request=json.loads((W/'review-request-stdout.json').read_text())
 review={'schemaVersion':1,'requestId':request['requestId'],'bindingSha256':request['bindingSha256'],'source':'host-model','reviewer':'Codex primary agent actual view_image inspection','verdict':'FAIL','observations':['Nikon D2H RAW 导出墙面、白色色块和高光有明显青绿色偏色；与同一 NEF 内嵌相机 JPEG 的较中性墙面/白块对照不通过。参考图仅为视觉参照，不声称色度真值或 deltaE。']}
 state=call('review',review);assert state['acceptance']['visual']=='FAIL'
 before=(task/'state.json').read_bytes();denied=call('deliver',expect=1);after=(task/'state.json').read_bytes();assert denied['error']=='delivery_visual_review_required';assert before==after and not (task/'delivery.json').exists()
 report={'schemaVersion':1,'status':'PASS_NEGATIVE_DELIVERY_GUARD','creativeAcceptance':'FAIL','checks':{'actualNativeExecution':state['acceptance']['execution']=='NATIVE_EXIT_ZERO_REVIEW_REQUIRED','artifactTechnicalPass':state['acceptance']['artifacts']=='PASS','actualVisualFailRecorded':state['acceptance']['visual']=='FAIL','deliveryRejected':True,'stateUnchangedOnRejection':before==after,'noDeliveryFile':not (task/'delivery.json').exists(),'originalUnchanged':hashlib.sha256(original.read_bytes()).hexdigest()==state['originals'][str(original)]},'candidateSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'reviewBindingSha256':request['bindingSha256'],'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=P,text=True).strip(),'scope':'actual current plugin controller + protected public skill snapshot; negative delivery proof only; no RAW color correction or creative pass'}
 assert all(report['checks'].values());(W/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
