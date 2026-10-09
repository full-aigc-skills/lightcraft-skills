"""仅操作本轮拥有的桌面进程及合成图专用库；明确请求，不重放编辑。"""
from pathlib import Path
import json,socket,subprocess,hashlib,os,signal,time
B=Path('/Users/wandl/workspaces/workspace-agent-skills');W=B/'evaluation-results/lightcraft-installed-desktop-20261009';S=B/'full-aigc-skills-repositories/lightcraft-skills';P=B/'full-aigc-plugins-repositories/lightcraft-plugin';PY='/Users/wandl/.local/bin/python3.12';state=json.loads((W/'launch.json').read_text());port=state['port'];lib=Path(state['library']);events=[];counter=10
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rpc(command,params=None):
 global counter
 counter+=1;q={'id':counter,'method':'engine.execute','params':{'command':command,'params':params or {}}}
 with socket.create_connection(('127.0.0.1',port),timeout=10) as s:
  s.settimeout(15);f=s.makefile('rwb');f.write((json.dumps(q)+'\n').encode());f.flush();line=f.readline(4*1024*1024);r=json.loads(line)
 events.append({'request':q,'reply':r});(W/'desktop-engine-rpc.json').write_text(json.dumps(events,indent=2)+'\n');assert r['id']==counter;return r
def value(r):assert r.get('ok') is True,r;return r['result']
def probe(name,connect=None,library=None):
 args=[PY,'-I','-B',str(S/'runtime/session_probe.py'),'--runtime-home',str(B/'evaluation-results/lightcraft-connect-20261008/runtime'),'--output',str(W/name),'--timeout','10']
 args+=['--connect',connect] if connect else ['--library',str(library)]
 r=subprocess.run(args,capture_output=True,text=True,timeout=25);(W/(name+'-result.json')).write_text(r.stdout);return json.loads((W/name/'receipt.json').read_text())
def main():
 fixture=B/'evaluation-results/lightcraft-mobile-20261009/source-bundle/original.png';original=sha(fixture)
 value(rpc('library.import',{'paths':[str(fixture)]}));query=value(rpc('catalog.query'));assert len(query['photos'])==1,query;pid=query['photos'][0]['id'];value(rpc('library.select',{'ids':[pid],'active':pid}));value(rpc('photo.rate',{'rating':1}))
 log=lib/'catalog.log';before=log.read_bytes();mode=log.stat().st_mode&0o777;checks={}
 try:
  log.chmod(0o400);failed=rpc('photo.rate',{'rating':4});info=value(rpc('library.info'));observed=value(rpc('catalog.query'))
  checks.update(nativeNotSaved=not failed['ok'] and 'saved in memory but not written to disk' in failed.get('error',''),unsavedOpsPositive=info.get('unsavedOps',0)>0,memoryRatingFour=observed['photos'][0]['rating']==4,diskUnchangedDuringFailure=log.read_bytes()==before)
 finally:log.chmod(mode)
 recovered=value(rpc('library.info'));confirmed=value(rpc('library.info'));checks['saveRecovered']=confirmed.get('unsavedOps')==0
 lock=lib/'catalog.lock';inode=lock.stat().st_ino;occupied=probe('occupied-live',library=lib);checks['occupiedRejected']=occupied['backendQuery']!='PASS';checks['lockUnchanged']=lock.exists() and lock.stat().st_ino==inode
 # 所属进程退出前已确认保存；仅终止 launch.json 记录且命令行匹配的验收进程。
 cmd=subprocess.check_output(['ps','-p',str(state['pid']),'-o','command='],text=True);assert str(W/'LightCraft.app/Contents/MacOS/LightCraft') in cmd and str(lib) in cmd
 os.kill(state['pid'],signal.SIGTERM)
 for _ in range(100):
  try:
   with socket.create_connection(('127.0.0.1',port),timeout=.1):pass
  except OSError:break
  time.sleep(.05)
 else:raise AssertionError('owned desktop failed to stop')
 disconnected=probe('disconnected-real',connect=f'127.0.0.1:{port}');checks['stoppedDesktopQueryNotPass']=disconnected['backendQuery']!='PASS'
 with (W/'restart.stdout.log').open('w') as out,(W/'restart.stderr.log').open('w') as err:
  p=subprocess.Popen([str(W/'LightCraft.app/Contents/MacOS/LightCraft'),'--library',str(lib),'--no-demo','--control',str(port)],stdout=out,stderr=err,env=dict(os.environ,LIGHTCRAFT_NO_PREFS='1'),start_new_session=True)
 (W/'restart.json').write_text(json.dumps({'pid':p.pid,'port':port,'library':str(lib)},indent=2)+'\n')
 try:
  for _ in range(100):
   if p.poll() is not None:raise AssertionError('desktop restart exited')
   try:
    with socket.create_connection(('127.0.0.1',port),timeout=.1):break
   except OSError:time.sleep(.05)
  else:raise AssertionError('desktop restart timeout')
  connected=probe('reconnected-explicit',connect=f'127.0.0.1:{port}');checks['explicitReconnectQueryPass']=connected['backendQuery']=='PASS';reopened=value(rpc('catalog.query'));checks['independentDesktopReopenRatingFour']=reopened['photos'][0]['rating']==4;checks['originalUnchanged']=sha(fixture)==original
 finally:
  if p.poll() is None:p.terminate()
  p.wait(timeout=15)
 # 插件只读观察当前来源回执；不声称来源快照一致或插件自动 MCP 集成。
 inspected=subprocess.run([PY,'-I','-B',str(P/'scripts/controller.py'),'session-inspect',str(W/'reconnected-explicit/receipt.json')],capture_output=True,text=True,timeout=15);(W/'plugin-session-inspect.json').write_text(inspected.stdout);checks['pluginObservesExplicitReconnect']=inspected.returncode==0 and json.loads(inspected.stdout).get('backendQuery')=='PASS'
 report={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'desktop':state,'clientVersion':'0.2.1','fixtureSha256':original,'editingRequests':'photo.rate 1 then photo.rate 4 once; no replay across restart','scope':'desktop 0.4.0 with fixed CLI 0.2.1; dedicated synthetic library; actual NotSaved/occupied/restart; no GUI visual or automatic plugin MCP integration'};(W/'desktop-result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
