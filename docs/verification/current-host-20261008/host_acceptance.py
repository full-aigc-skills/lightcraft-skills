"""当前候选的真实 Codex 宿主验收；不调用原生编辑或公开发布。"""
from pathlib import Path
import hashlib,io,json,os,queue,shutil,subprocess,threading,time,tomllib,zipfile
BASE=Path('/Users/wandl/workspaces/workspace-agent-skills')
WORK=BASE/'evaluation-results/lightcraft-current-host-20261008'
CLI=Path('/Applications/Kimi.app/Contents/Resources/resources/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex')
PYTHON='/Users/wandl/.local/bin/python3.12'
S=BASE/'full-aigc-skills-repositories/lightcraft-skills';P=BASE/'full-aigc-plugins-repositories/lightcraft-plugin'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inventory(path):return {str(p.relative_to(path)):digest(p) for p in sorted(path.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
def snapshot(root,dest,subset=None):
 argv=['git','archive','--format=zip','HEAD']+([subset] if subset else [])
 data=subprocess.check_output(argv,cwd=root)
 with zipfile.ZipFile(io.BytesIO(data)) as z:z.extractall(dest)
def call(home,*args):
 env=dict(os.environ,CODEX_HOME=str(home));result=subprocess.run([str(CLI),*args,'--json'],env=env,capture_output=True,text=True,encoding='utf-8',timeout=120)
 if result.returncode:raise RuntimeError(result.stderr[-1500:]+result.stdout[-1500:])
 return json.loads(result.stdout)
def discover(home,work,name):
 env=dict(os.environ,CODEX_HOME=str(home));messages=queue.Queue()
 with (WORK/(name+'-app-server.stderr.log')).open('w') as errors:
  proc=subprocess.Popen([str(CLI),'app-server','--stdio'],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True,encoding='utf-8',bufsize=1)
  def reader():
   for line in proc.stdout:
    try:messages.put(json.loads(line))
    except ValueError:messages.put({'invalidProtocolLine':line})
  threading.Thread(target=reader,daemon=True).start()
  def rpc(i,method,params):
   proc.stdin.write(json.dumps({'id':i,'method':method,'params':params})+'\n');proc.stdin.flush();deadline=time.monotonic()+60
   while time.monotonic()<deadline:
    response=messages.get(timeout=max(.1,deadline-time.monotonic()))
    if response.get('id')==i:
     if 'error' in response:raise RuntimeError(str(response['error']))
     return response['result']
   raise TimeoutError(method)
  try:
   init=rpc(1,'initialize',{'clientInfo':{'name':'lightcraft_current_acceptance','version':'1'},'capabilities':{'experimentalApi':True}})
   proc.stdin.write(json.dumps({'method':'initialized','params':{}})+'\n');proc.stdin.flush()
   response=rpc(2,'skills/list',{'cwds':[str(work)],'forceReload':True})
   return {'initialization':init,'skills':response}
  finally:proc.terminate();proc.wait(timeout=10)
def setup():
 assert subprocess.check_output([str(CLI),'--version'],text=True).strip()=='codex-cli 0.161.0'
 config=tomllib.loads(Path('/Users/wandl/.codex/config.toml').read_text())
 installations=[]
 for name,root in [('source',S),('plugin',P)]:
  home=WORK/(name+' 宿主 验收 home');home.mkdir(exist_ok=True);scratch=WORK/(name+'-scratch');scratch.mkdir(exist_ok=True)
  (home/'config.toml').write_text(''.join(f'{key} = {json.dumps(config[key])}\n' for key in ('model','model_reasoning_effort','service_tier') if key in config))
  if name=='source':
   snapshot(root,home,'skills');loaded=home/'skills';installed={'kind':'standalone-skills','version':'0.1.0-dev.2','sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()}
  else:
   market=WORK/'candidate-marketplace';dest=market/'plugins/lightcraft';dest.mkdir(parents=True)
   snapshot(root,dest);(market/'.agents/plugins').mkdir(parents=True)
   (market/'.agents/plugins/marketplace.json').write_text(json.dumps({'name':'lightcraft-current-acceptance','plugins':[{'name':'lightcraft','source':'./plugins/lightcraft','version':'0.1.0-dev.3','description':'Current unpublished candidate host acceptance'}]}))
   call(home,'plugin','marketplace','add',str(market));installed=call(home,'plugin','add','lightcraft@lightcraft-current-acceptance');loaded=Path(installed['installedPath'])/'skills'
  # 在隔离配置中关闭其他技能，保留实际用户目录与全局配置不变。
  first=discover(home,scratch,name+'-initial');rows=[s for group in first['skills']['data'] for s in group.get('skills',[])]
  with (home/'config.toml').open('a') as out:
   for row in rows:
    path=Path(row['path'])
    if not (path.is_relative_to(loaded) and path.relative_to(loaded).parts[0] in json.loads((root/('skill-suite.json' if name=='source' else 'source-suite.json')).read_text())['skills']):out.write('\n[[skills.config]]\npath = '+json.dumps(str(path))+'\nenabled = false\n')
  current=discover(home,scratch,name+'-isolated');rows=[s for group in current['skills']['data'] for s in group.get('skills',[])]
  enabled=[s for s in rows if s.get('enabled')]
  assert len(enabled)==6 and all(Path(s['path']).is_relative_to(loaded) for s in enabled),(name,len(enabled))
  expected=inventory(root/'skills');observed={k:v for k,v in inventory(loaded).items() if not k.startswith('.system/')};assert observed==expected,'installed_skill_identity_mismatch'
  auth=home/'auth.json';shutil.copyfile('/Users/wandl/.codex/auth.json',auth);auth.chmod(0o600)
  record={'name':name,'home':str(home),'workdir':str(scratch),'skillsRoot':str(loaded),'installation':installed,'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'installedSkillSha256':observed,'enabledSkills':enabled,'otherSkillsDisabled':len(rows)-6}
  installations.append(record);(WORK/(name+'-discovery.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 (WORK/'setup.json').write_text(json.dumps({'hostVersion':'codex-cli 0.161.0','hostBinarySha256':digest(CLI),'model':config.get('model'),'installations':installations},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'setup':'PASS','installations':[{'name':x['name'],'skills':6,'disabled':x['otherSkillsDisabled']} for x in installations]}),flush=True)
if __name__=='__main__':setup()
