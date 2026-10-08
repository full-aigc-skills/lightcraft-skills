from pathlib import Path
import shutil,json,subprocess,os,hashlib,threading,queue,time
r=Path(__file__).resolve().parent;p=Path('/Users/wandl/workspaces/workspace-agent-skills/full-aigc-plugins-repositories/lightcraft-plugin');market=r/'marketplace';dest=market/'plugins/lightcraft';manifest=market/'.agents/plugins/marketplace.json';manifest.parent.mkdir(parents=True,exist_ok=True)
home=r/'宿主 升级验收 home';home.mkdir(exist_ok=True);binary=str(r/'codex-host/node_modules/.bin/codex');env=dict(os.environ,CODEX_HOME=str(home));name='lightcraft-release-acceptance'
old=Path('/Users/wandl/.codex/plugins/cache/lightcraft-acceptance/lightcraft/0.1.0-dev.1')
shutil.copytree(old,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git','__pycache__'))
def write_market(version):manifest.write_text(json.dumps({'name':name,'plugins':[{'name':'lightcraft','source':'./plugins/lightcraft','version':version,'description':'Lightcraft actual version upgrade acceptance'}]},indent=2)+'\n')
def cli(*args):return json.loads(subprocess.check_output([binary,*args,'--json'],env=env,text=True))
write_market('0.1.0-dev.1');cli('plugin','marketplace','add',str(market));first=cli('plugin','add','lightcraft@'+name);assert first['version']=='0.1.0-dev.1'
state=r/'restored-old-task';shutil.copytree(p/'docs/verification/native-20261008/plugin-task-v4',state,dirs_exist_ok=True)
def inventory():return {str(f.relative_to(state)):hashlib.sha256(f.read_bytes()).hexdigest() for f in state.rglob('*') if f.is_file()}
before=inventory();shutil.copytree(p,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git','__pycache__'));write_market('0.1.0-dev.2');second=cli('plugin','add','lightcraft@'+name);assert second['version']=='0.1.0-dev.2';cache=Path(second['installedPath']);old_cache_retained=(cache.parent/'0.1.0-dev.1').is_dir()
lock=json.loads((cache/'candidate-source.json').read_text());assert lock['commit']=='87fe7cebab2bc687ef7b819eb355e4e28132e6e9'
q=queue.Queue()
with (r/'app-server.stderr.log').open('w') as err:
 proc=subprocess.Popen([binary,'app-server','--stdio'],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
 def reader():
  for l in proc.stdout:q.put(json.loads(l))
 threading.Thread(target=reader,daemon=True).start()
 def rpc(i,method,params):
  proc.stdin.write(json.dumps({'id':i,'method':method,'params':params})+'\n');proc.stdin.flush();deadline=time.monotonic()+45
  while time.monotonic()<deadline:
   result=q.get(timeout=max(.1,deadline-time.monotonic()))
   if result.get('id')==i:
    assert 'error' not in result,result
    return result['result']
  raise TimeoutError(method)
 try:
  init=rpc(1,'initialize',{'clientInfo':{'name':'lightcraft_upgrade_acceptance','version':'0.1.0'},'capabilities':{'experimentalApi':True}})
  proc.stdin.write(json.dumps({'method':'initialized','params':{}})+'\n');proc.stdin.flush()
  allskills=rpc(2,'skills/list',{'cwds':[str(r)],'forceReload':True})
  skills=[s for x in allskills['data'] for s in x.get('skills',[]) if s.get('pluginId')=='lightcraft@'+name]
  assert len(skills)==6 and all('/0.1.0-dev.2/' in s['path'] and s['enabled'] for s in skills)
 finally:proc.terminate();proc.wait(timeout=10)
assert before==inventory()
report={'schemaVersion':1,'status':'PASS','hostVersion':subprocess.check_output([binary,'--version'],text=True).strip(),'previousInstall':first,'updatedInstall':second,'sourceCommit':lock['commit'],'sourceTag':lock['releaseTag'],'sourceLockSha256':hashlib.sha256((cache/'candidate-source.json').read_bytes()).hexdigest(),'previousCacheRetained':old_cache_retained,'cacheRetentionControlledByHost':True,'sixSkillsReload':'PASS','skills':skills,'archivedTaskAndReceipts':'UNCHANGED','taskFilesSha256':before,'scope':'Actual CLI install 0.1.0-dev.1 -> 0.1.0-dev.2 and app-server reload in persistent Chinese/space cache; historical task copied from archived native evidence because original temporary directory was externally removed; no native editing replay'}
(r/'host-upgrade.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'from':first['version'],'to':second['version'],'skills':len(skills)},ensure_ascii=False))
