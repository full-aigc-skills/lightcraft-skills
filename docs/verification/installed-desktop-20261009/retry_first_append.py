from pathlib import Path
import importlib.util,json,subprocess,os,time
W=Path('/Users/wandl/workspaces/workspace-agent-skills/evaluation-results/lightcraft-installed-desktop-20261009');spec=importlib.util.spec_from_file_location('accept',W/'desktop_acceptance.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
lib=W/'notsaved-first-append-test-library';assert not lib.exists();a.lib=lib;a.events=[];a.counter=100
seed=subprocess.run([str(a.B/'evaluation-results/lightcraft-connect-20261008/runtime/lightcraft/0.2.1/lightcraft-cli'),'run','--library',str(lib),'--import',str(a.B/'evaluation-results/lightcraft-mobile-20261009/source-bundle/original.png'),'photo.rate','rating=1'],capture_output=True,text=True,timeout=30);assert seed.returncode==0,seed.stderr
(W/'first-append-seed.log').write_text(seed.stdout+seed.stderr)
log=lib/'catalog.log';original_mode=log.stat().st_mode&0o777;log.chmod(0o400)
a.W=W/'first-append-proof';a.W.mkdir()
out=(W/'first-append-desktop.stdout.log').open('w');err=(W/'first-append-desktop.stderr.log').open('w');p=subprocess.Popen([str(W/'LightCraft.app/Contents/MacOS/LightCraft'),'--library',str(lib),'--no-demo','--control',str(a.port)],stdout=out,stderr=err,env=dict(os.environ,LIGHTCRAFT_NO_PREFS='1'),start_new_session=True)
log=lib/'catalog.log';flag=False
try:
 for _ in range(100):
  try:
   with a.socket.create_connection(('127.0.0.1',a.port),timeout=.1):break
  except OSError:time.sleep(.05)
 fixture=a.B/'evaluation-results/lightcraft-mobile-20261009/source-bundle/original.png';query=a.value(a.rpc('catalog.query'));pid=query['photos'][0]['id'];a.value(a.rpc('library.select',{'ids':[pid],'active':pid}));before=log.read_bytes()
 log.chmod(0o400);flag=True
 failed=a.rpc('photo.rate',{'rating':4});info=a.value(a.rpc('library.info'));observed=a.value(a.rpc('catalog.query'));checks={'nativeNotSaved':not failed['ok'] and 'saved in memory but not written to disk' in failed.get('error',''),'unsavedOpsPositive':info.get('unsavedOps',0)>0,'memoryRatingFour':observed['photos'][0]['rating']==4,'diskUnchangedDuringFailure':log.read_bytes()==before}
 log.chmod(original_mode);flag=False
 a.value(a.rpc('library.info'));confirmed=a.value(a.rpc('library.info'));checks['saveRecovered']=confirmed.get('unsavedOps')==0
 (W/'first-append-result.json').write_text(json.dumps({'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'method':'readonly journal before desktop first append; restored in finally; earlier attempts retained FAIL','rpc':'fault-rpc.json','replay':False},indent=2)+'\n');print(checks)
finally:
 log.chmod(original_mode)
 if p.poll() is None:p.terminate()
 p.wait(timeout=15);out.close();err.close();(W/'first-append-rpc.json').write_text(json.dumps(a.events,indent=2)+'\n')
