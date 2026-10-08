"""专用测试库中注入真实 journal 写权限故障；不操作用户照片库。"""
from pathlib import Path
import hashlib,importlib.util,json,os,queue,signal,subprocess,threading,time
B=Path('/Users/wandl/workspaces/workspace-agent-skills');W=B/'evaluation-results/lightcraft-current-mcp-20261008';N=B/'evaluation-results/lightcraft-connect-20261008/runtime/lightcraft/0.2.1/lightcraft-cli';S=B/'full-aigc-skills-repositories/lightcraft-skills'
lib=W/'notsaved-library-2';assert not lib.exists()
fixture=S/'docs/verification/windows-20261008/ci-native/darwin-arm64/inputs/before-1.png'
# Find only the archived synthetic PNG, never a user original.
if not fixture.exists():
 choices=list((S/'docs/verification/windows-20261008/ci-native').rglob('before-1.png'));assert choices;fixture=choices[0]
original=hashlib.sha256(fixture.read_bytes()).hexdigest()
r=subprocess.run([str(N),'run','--library',str(lib),'--import',str(fixture),'photo.rate','rating=1'],capture_output=True,text=True,timeout=30)
(W/'notsaved-seed.stdout.log').write_text(r.stdout);(W/'notsaved-seed.stderr.log').write_text(r.stderr);assert r.returncode==0,r.stderr
q=queue.Queue();events=[]
with (W/'notsaved-native.stderr.log').open('w') as err:
 p=subprocess.Popen([str(N),'mcp','--compact','--library',str(lib)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1,start_new_session=True)
 def reader():
  for line in p.stdout:q.put(json.loads(line))
 threading.Thread(target=reader,daemon=True).start()
 def rpc(i,method,params):
  request={'jsonrpc':'2.0','id':i,'method':method,'params':params};events.append({'request':request})
  p.stdin.write(json.dumps(request)+'\n');p.stdin.flush();reply=q.get(timeout=30);events.append({'reply':reply});assert reply.get('id')==i,reply;return reply
 def value(reply):
  result=reply['result'];assert not result.get('isError'),result
  if 'structuredContent' in result:return result['structuredContent']
  return json.loads(result['content'][0]['text'])
 log=lib/'catalog.log';oldmode=None
 try:
  rpc(1,'initialize',{'protocolVersion':'2024-11-05','clientInfo':{'name':'notsaved_acceptance','version':'1'},'capabilities':{}})
  p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized','params':{}})+'\n');p.stdin.flush()
  before=value(rpc(2,'tools/call',{'name':'query_photos','arguments':{}}));pid=before['photos'][0]['id']
  value(rpc(3,'tools/call',{'name':'select_photos','arguments':{'ids':[pid]}}))
  log.touch(exist_ok=True);oldmode=log.stat().st_mode&0o777;oldbytes=log.read_bytes();log.chmod(0o400)
  failed=rpc(4,'tools/call',{'name':'run_command','arguments':{'command':'photo.rate','params':{'rating':4}}})
  info=value(rpc(5,'tools/call',{'name':'run_command','arguments':{'command':'library.info','params':{}}}))
  observed=value(rpc(6,'tools/call',{'name':'query_photos','arguments':{}}))
  checks={'nativeReportsNotSaved':'saved in memory but not written to disk' in json.dumps(failed),'unsavedOpsPositive':info.get('unsavedOps',0)>0,'memoryRatingFour':observed['photos'][0]['rating']==4,'diskJournalUnchangedDuringFailure':log.read_bytes()==oldbytes}
  log.chmod(oldmode);oldmode=None
  recovered=value(rpc(7,'tools/call',{'name':'run_command','arguments':{'command':'library.info','params':{}}}));confirmed=value(rpc(8,'tools/call',{'name':'run_command','arguments':{'command':'library.info','params':{}}}));checks['queuedSaveRecovered']=confirmed.get('unsavedOps')==0
 finally:
  if oldmode is not None:log.chmod(oldmode)
  if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
  p.wait(timeout=10)
  (W/'notsaved-rpc.json').write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n')
r=subprocess.run([str(N),'run','--library',str(lib),'catalog.query','library.info'],capture_output=True,text=True,timeout=30)
(W/'notsaved-reopen.stdout.log').write_text(r.stdout);(W/'notsaved-reopen.stderr.log').write_text(r.stderr)
rows=[json.loads(x) for x in r.stdout.splitlines() if x.strip()];checks['independentReopenRatingFour']=r.returncode==0 and rows[0]['result']['photos'][0]['rating']==4
checks['originalUnchanged']=hashlib.sha256(fixture.read_bytes()).hexdigest()==original
spec=importlib.util.spec_from_file_location('gateway',S/'runtime/command_gateway.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
error=failed['result']['content'][0]['text'];classified=g.parse_results([{'command':'photo.rate','params':{'rating':4}}],[json.dumps({'command':'photo.rate','ok':False,'error':error})],1,False)
checks['wrapperClassifiesNotSaved']=classified['steps'][0]['status']=='APPLIED_NOT_SAVED'
report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'nativeSha256':hashlib.sha256(N.read_bytes()).hexdigest(),'fixtureSha256':original,'classification':classified,'replay':'one explicit photo.rate only; after permission restoration native persistence retries queued save on explicit library.info, not command replay','scope':'fixed CLI headless native MCP; real disk permission failure; no desktop or Connect NotSaved claim'}
(W/'notsaved-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
