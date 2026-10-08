import pathlib,json,subprocess,sys,hashlib,fcntl
root=pathlib.Path('/tmp/lightcraft-acceptance-HoMkD5');base=root/'png-jpeg';source=pathlib.Path('/Users/wandl/workspaces/workspace-agent-skills/full-aigc-skills-repositories/lightcraft-skills');commands=source/'skills/lightcraft-use/scripts/commands.py';results={}
def step(c,**p):return {'command':c,'params':p}
def run(name,steps):
 plan=root/(name+'.json');plan.write_text(json.dumps({'domain':'lightcraft','steps':steps}));out=root/name
 p=subprocess.run([sys.executable,'-I','-B',str(commands),'run',str(plan),'--runtime-home',str(base/'runtime'),'--require-installed','--library',str(base/'library'),'--input',str(base/'originals'),'--output-root',str(base/'exports'),'--output',str(out)],capture_output=True,text=True)
 receipt=json.loads((out/'receipt.json').read_text());return p.returncode,receipt
code,r=run('duplicate-missing',[step('library.import',paths=[str(base/'originals/gradient.png'),str(base/'originals/missing.png')],mode='add'),step('catalog.query')]);result=r['steps'][0]['native']['result'];assert result['duplicates'] and result['failed'] and not result['imported'];results['partialImport']={'status':'PASS','receipt':str(root/'duplicate-missing/receipt.json'),'result':result}
code,r=run('batch-scope',[step('library.select',ids=[1,2],active=1),step('develop.get',id=1),step('develop.get',id=2),step('develop.set',ids=[1],values={'light.exposure':.25}),step('develop.get',id=1),step('develop.get',id=2)])
a,b,c,d=[r['steps'][i]['native']['result'] for i in [1,2,4,5]];want=json.loads(json.dumps(a));want['light']['exposure']=.25;assert c==want and d==b;results['batchScope']={'status':'PASS','receipt':str(root/'batch-scope/receipt.json'),'targetIds':[1],'unchangedIds':[2]}
with (base/'library/catalog.lock').open('r+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 code,r=run('occupied-library',[step('library.info')]);assert code!=0 and r['status']!='NATIVE_EXIT_ZERO_REVIEW_REQUIRED';results['libraryLock']={'status':'PASS','receipt':str(root/'occupied-library/receipt.json'),'observedStatus':r['status'],'noForcedUnlock':True}
(root/'native-contracts.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False))
