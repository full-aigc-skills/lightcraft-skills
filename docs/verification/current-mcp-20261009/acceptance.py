"""真实 Codex MCP 隔离验收；手工临时配置，不声明插件自动提供 MCP。"""
from pathlib import Path
import hashlib,json,os,queue,signal,shutil,subprocess,threading,time
B=Path('/Users/wandl/workspaces/workspace-agent-skills');W=B/'evaluation-results/lightcraft-current-mcp-20261008';H=B/'evaluation-results/lightcraft-current-host-20261008'
CLI=Path('/Applications/Kimi.app/Contents/Resources/resources/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex')
NATIVE=B/'evaluation-results/lightcraft-connect-20261008/runtime/lightcraft/0.2.1/lightcraft-cli'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def stop(p):
 if p.poll() is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
def discover(home,name):
 env=dict(os.environ,CODEX_HOME=str(home));q=queue.Queue()
 with (W/f'{name}-app-server.stderr.log').open('w') as errors:
  p=subprocess.Popen([str(CLI),'app-server','--stdio','--strict-config'],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True,bufsize=1,start_new_session=True)
  def read():
   for line in p.stdout:
    try:q.put(json.loads(line))
    except ValueError:q.put({'invalid':line})
  threading.Thread(target=read,daemon=True).start()
  def rpc(i,method,params):
   p.stdin.write(json.dumps({'id':i,'method':method,'params':params})+'\n');p.stdin.flush();deadline=time.monotonic()+60
   while time.monotonic()<deadline:
    r=q.get(timeout=max(.1,deadline-time.monotonic()))
    if r.get('id')==i:
     if 'error' in r:raise ValueError(r['error'])
     return r['result']
   raise TimeoutError(method)
  try:
   init=rpc(1,'initialize',{'clientInfo':{'name':'lightcraft_mcp_acceptance','version':'1'},'capabilities':{'experimentalApi':True}})
   p.stdin.write(json.dumps({'method':'initialized','params':{}})+'\n');p.stdin.flush()
   status=rpc(2,'mcpServerStatus/list',{'serverName':'lightcraft_readonly','detail':'full'})
   (W/f'{name}-mcp-status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
   rows=status['data'];assert len(rows)==1,rows
   tools=rows[0]['tools'];assert len(tools)==2 and all(t['name'] in ['query_photos','list_commands'] for t in tools.values()),list(tools)
   assert not rows[0].get('toolsError'),rows[0]
   return status
  finally:stop(p)
def main():
 assert subprocess.check_output([str(CLI),'--version'],text=True).strip()=='codex-cli 0.161.0'
 assert sha(NATIVE)==json.loads((B/'full-aigc-skills-repositories/lightcraft-skills/runtime/runtime.lock.json').read_text())['artifacts']['darwin-arm64']['binarySha256']
 setup=json.loads((H/'setup.json').read_text());results=[];global_config=sha(Path('/Users/wandl/.codex/config.toml'))
 for install in setup['installations']:
  name=install['name'];home=Path(install['home']);config=home/'config.toml';original=config.read_bytes();auth=home/'auth.json';assert not auth.exists()
  lib=W/f'{name}-测试库';scratch=W/f'{name}-scratch';scratch.mkdir(exist_ok=True)
  repo=B/('full-aigc-skills-repositories/lightcraft-skills' if name=='source' else 'full-aigc-plugins-repositories/lightcraft-plugin')
  skillroot=Path(install['skillsRoot']);before={str(p.relative_to(skillroot)):sha(p) for p in skillroot.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
  fragment='\n[mcp_servers.lightcraft_readonly]\ncommand = '+json.dumps(str(NATIVE))+'\nargs = '+json.dumps(['mcp','--compact','--library',str(lib)],ensure_ascii=False)+'\nenabled_tools = ["query_photos", "list_commands"]\nstartup_timeout_sec = 30\ntool_timeout_sec = 30\n'
  fragment+='\n[mcp_servers.lightcraft_readonly.tools.query_photos]\napproval_mode = \"approve\"\n[mcp_servers.lightcraft_readonly.tools.list_commands]\napproval_mode = \"approve\"\n'
  config.write_bytes(original+fragment.encode());(W/f'{name}-mcp-config.toml').write_text(fragment)
  try:
   status=discover(home,name);print(name,'catalog PASS two readonly tools',flush=True)
   shutil.copyfile('/Users/wandl/.codex/auth.json',auth);auth.chmod(0o600)
   prompt='这是已授权的隔离 MCP 宿主验收。必须调用 lightcraft_readonly MCP 的 query_photos 工具一次，参数 limit=2、offset=0，查询专用空测试库；报告实际返回的照片数量。只调用该 MCP 工具，不使用 shell、不编辑文件、不尝试安装、不重试写操作。若 MCP 不可用，明确失败，不用其他方式替代。'
   started=time.monotonic()
   with (W/f'{name}-exec.jsonl').open('w') as out,(W/f'{name}-exec.stderr.log').open('w') as err:
    p=subprocess.Popen([str(CLI),'exec','--json','--ephemeral','--skip-git-repo-check','--sandbox','read-only','-c','approval_policy="never"','--cd',str(scratch),prompt],env=dict(os.environ,CODEX_HOME=str(home)),stdout=out,stderr=err,start_new_session=True)
    try:code=p.wait(timeout=180)
    finally:stop(p)
   events=[json.loads(line) for line in (W/f'{name}-exec.jsonl').read_text().splitlines() if line.strip()]
   calls=[e['item'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='mcp_tool_call']
   shells=[e for e in events if e.get('item',{}).get('type')=='command_execution']
   checks={'processExitZero':code==0,'turnCompleted':any(e['type']=='turn.completed' for e in events),'oneActualMcpCall':len(calls)==1,'noShell':not shells,'restrictedCatalog':True,'globalConfigUnchanged':sha(Path('/Users/wandl/.codex/config.toml'))==global_config,'installedSkillsUnchanged':before=={str(p.relative_to(skillroot)):sha(p) for p in skillroot.rglob('*') if p.is_file() and '__pycache__' not in p.parts}}
   if calls:checks['querySucceeded']=calls[0].get('tool')=='query_photos' and calls[0].get('status')=='completed' and calls[0].get('error') is None
   record={'schemaVersion':1,'name':name,'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'calls':calls,'elapsedSeconds':round(time.monotonic()-started),'hostVersion':'0.161.0','hostSha256':sha(CLI),'nativeSha256':sha(NATIVE),'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'scope':'manual temporary host configuration; actual fixed headless MCP only, not desktop Connect or plugin manifest auto registration','installationBaselineCommit':install['sourceCommit']}
   (W/f'{name}-result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');results.append(record);print(name,record['status'],checks,flush=True)
  finally:
   auth.unlink(missing_ok=True);config.write_bytes(original)
   assert not auth.exists() and config.read_bytes()==original
 (W/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
