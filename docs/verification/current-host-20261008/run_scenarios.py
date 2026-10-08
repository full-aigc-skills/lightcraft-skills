"""执行宿主验收提示，记录实际模型、工具事件和输入保全；不安装 CLI。"""
import importlib.util,json,os,subprocess,threading,queue,time
from pathlib import Path
ROOT=Path('/Users/wandl/workspaces/workspace-agent-skills/evaluation-results/lightcraft-current-host-20261008')
spec=importlib.util.spec_from_file_location('driver',ROOT/'host_acceptance.py');driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
setup=json.loads((ROOT/'setup.json').read_text());global_config=Path('/Users/wandl/.codex/config.toml');before=driver.digest(global_config)
scenarios=[
 ('natural','我想用 Lightcraft 给照片提亮并导出 PNG。现在只读取已安装技能说明，告诉我应走哪个入口、需要哪些输入和原片保护要求；不安装、不下载、不运行原生程序、不修改文件。','lightcraft-use/SKILL.md'),
 ('explicit','请使用 $lightcraft-cli-export，只读取已安装技能及其导出流程，说明导出前的输入和覆盖冲突检查。不要切换成通用入口，不安装、不下载、不执行导出、不修改文件。','lightcraft-cli-export/SKILL.md'),
 ('recovery','我的 Lightcraft 导出进程状态 UNKNOWN，回执不完整。只读取已安装技能和恢复说明，判断能否自动重放、是否能把原片不变或进程结束作为交付完成证明。不要实际恢复或重放，不运行原生程序，不修改文件。','lightcraft-use/SKILL.md'),
 ('missing-dependency',None,'lightcraft-cli-setup/SKILL.md'),
 ('unrelated','只回答 6*7 的数字，不使用技能、不调用工具。',None)
]
summary=[]
try:
 for install in setup['installations']:
  home=Path(install['home']);work=Path(install['workdir']);skills=Path(install['skillsRoot']);env=dict(os.environ,CODEX_HOME=str(home))
  for name,prompt,expected in scenarios:
   prefix=install['name']+'-'+name;path=ROOT/(prefix+'.jsonl');err=ROOT/(prefix+'.stderr.log')
   if path.exists():raise ValueError('scenario_output_already_exists: '+prefix)
   missing=work/'never-installed-runtime'
   if name=='missing-dependency':prompt=f'请使用已安装的 lightcraft-cli-setup，只检查指定空运行目录 {missing} 的依赖。必须实际用 {driver.PYTHON} -I -B 调用该技能 bootstrap.py --no-install --runtime-home 指向这个目录并报告原始状态；不安装、不下载、不启动原生程序、不创建该目录，不修改文件。'
   inventory=driver.inventory(skills);started=time.monotonic();events=[];updates=queue.Queue()
   with path.open('w') as output,err.open('w') as errors:
    argv=[str(driver.CLI),'exec','--json','--ephemeral','--skip-git-repo-check','--sandbox','read-only','-c','approval_policy="never"','--cd',str(work),prompt]
    proc=subprocess.Popen(argv,env=env,stdout=subprocess.PIPE,stderr=errors,text=True,encoding='utf-8',bufsize=1)
    def reader():
     for line in proc.stdout:updates.put(line)
     updates.put(None)
    thread=threading.Thread(target=reader,daemon=True);thread.start();deadline=time.monotonic()+600;last=time.monotonic()
    try:
     while True:
      if time.monotonic()>deadline:raise TimeoutError('scenario_deadline: '+prefix)
      try:line=updates.get(timeout=5)
      except queue.Empty:
       if time.monotonic()-last>30:print(json.dumps({'scenario':prefix,'status':'RUNNING','elapsedSeconds':round(time.monotonic()-started)}),flush=True);last=time.monotonic()
       continue
      if line is None:break
      output.write(line);output.flush();events.append(json.loads(line))
     proc.wait(timeout=10)
    finally:
     if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
   completed=[e['item'] for e in events if e.get('type')=='item.completed'];commands=[e for e in completed if e.get('type')=='command_execution'];messages=[e['text'] for e in completed if e.get('type')=='agent_message'];final=messages[-1] if messages else ''
   checks={'processExitZero':proc.returncode==0,'turnCompleted':any(e.get('type')=='turn.completed' for e in events),'installedSkillsUnchanged':inventory==driver.inventory(skills),'globalConfigUnchanged':driver.digest(global_config)==before,'commandsExitedZero':all(e.get('exit_code')==0 for e in commands)}
   if expected:checks['actualInstalledEntryRead']=any(str(skills) in e.get('command','') and expected in e.get('command','') for e in commands)
   if name=='unrelated':checks.update(noTools=not commands,correctAnswer=final.strip()=='42')
   if name=='recovery':checks['noAutomaticReplayReported']='UNKNOWN' in final and any(x in final for x in ('不能','不可','禁止','不要','不应','不得'))
   if name=='missing-dependency':checks['actualMissingDiagnostic']=any('--no-install' in e.get('command','') and str(missing) in e.get('command','') and '"status": "MISSING"' in e.get('aggregated_output','') for e in commands);checks['runtimeDirectoryNotCreated']=not missing.exists()
   result={'scenario':prefix,'status':'PASS' if all(checks.values()) else 'FAIL','hostVersion':setup['hostVersion'],'sourceCommit':install['sourceCommit'],'installedSkillsSha256':inventory,'checks':checks,'completedItems':completed,'final':final,'elapsedSeconds':round(time.monotonic()-started),'eventsSha256':driver.digest(path)}
   (ROOT/(prefix+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');summary.append({k:result[k] for k in ('scenario','status','checks','elapsedSeconds')});(ROOT/'scenario-index.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
   print(json.dumps({'scenario':prefix,'status':result['status'],'commands':len(commands),'elapsedSeconds':result['elapsedSeconds']}),flush=True)
   if result['status']!='PASS':raise ValueError('host_scenario_failed: '+prefix+' '+str(checks))
finally:
 # 授权凭据仅用于本轮隔离进程，不进入归档材料；结束后删除本轮副本。
 for install in setup['installations']:
  auth=Path(install['home'])/'auth.json'
  if auth.is_file():auth.unlink()
