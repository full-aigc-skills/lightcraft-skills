"""显式验证所属桌面进程的超时、恢复和独立重开；只查询，不重放编辑。"""
from pathlib import Path
import json,subprocess,os,signal,time,importlib.util
W=Path('/Users/wandl/workspaces/workspace-agent-skills/evaluation-results/lightcraft-installed-desktop-20261009');spec=importlib.util.spec_from_file_location('a',W/'desktop_acceptance.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);a.W=W/'timeout-reopen-proof';a.W.mkdir();lib=W/'notsaved-first-append-test-library'
out=(a.W/'desktop.stdout.log').open('w');err=(a.W/'desktop.stderr.log').open('w');p=subprocess.Popen([str(W/'LightCraft.app/Contents/MacOS/LightCraft'),'--library',str(lib),'--no-demo','--control',str(a.port)],stdout=out,stderr=err,env=dict(os.environ,LIGHTCRAFT_NO_PREFS='1'),start_new_session=True);stopped=False
try:
 for _ in range(100):
  if p.poll() is not None:raise AssertionError('desktop exited')
  try:
   with a.socket.create_connection(('127.0.0.1',a.port),timeout=.1):break
  except OSError:time.sleep(.05)
 q=a.value(a.rpc('catalog.query'));checks={'independentReopenRatingFour':q['photos'][0]['rating']==4}
 os.kill(p.pid,signal.SIGSTOP);stopped=True
 result=subprocess.run([a.PY,'-I','-B',str(a.S/'runtime/session_probe.py'),'--runtime-home',str(a.B/'evaluation-results/lightcraft-connect-20261008/runtime'),'--connect',f'127.0.0.1:{a.port}','--output',str(a.W/'timeout'),'--timeout','1'],capture_output=True,text=True,timeout=15);(a.W/'timeout-result.json').write_text(result.stdout)
 receipt=json.loads((a.W/'timeout/receipt.json').read_text());checks['timeoutUnknown']=receipt['status']=='UNKNOWN' and receipt['backendQuery']=='NOT_CONFIRMED' and receipt['automaticReplay'] is False
 os.kill(p.pid,signal.SIGCONT);stopped=False
 recovered=a.probe('recovered-explicit',connect=f'127.0.0.1:{a.port}');checks['explicitRecoveryQueryPass']=recovered['backendQuery']=='PASS';q=a.value(a.rpc('catalog.query'));checks['ratingUnchangedAfterRecovery']=q['photos'][0]['rating']==4
 (a.W/'result.json').write_text(json.dumps({'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'desktopVersion':'0.4.0','clientVersion':'0.2.1','onlyOwnedPidSuspended':p.pid,'editReplay':False},indent=2)+'\n');print(checks)
finally:
 if stopped:os.kill(p.pid,signal.SIGCONT)
 if p.poll() is None:p.terminate()
 p.wait(timeout=15);out.close();err.close()
