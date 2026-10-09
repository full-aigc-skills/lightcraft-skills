from pathlib import Path
import importlib.util,json,subprocess,os,time
W=Path('/Users/wandl/workspaces/workspace-agent-skills/evaluation-results/lightcraft-installed-desktop-20261009');spec=importlib.util.spec_from_file_location('accept',W/'desktop_acceptance.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
lib=W/'notsaved-immutable-test-library';assert not lib.exists();a.lib=lib;a.events=[];a.counter=100
out=(W/'fault-desktop.stdout.log').open('w');err=(W/'fault-desktop.stderr.log').open('w');p=subprocess.Popen([str(W/'LightCraft.app/Contents/MacOS/LightCraft'),'--library',str(lib),'--no-demo','--control',str(a.port)],stdout=out,stderr=err,env=dict(os.environ,LIGHTCRAFT_NO_PREFS='1'),start_new_session=True)
log=lib/'catalog.log';flag=False
try:
 for _ in range(100):
  try:
   with a.socket.create_connection(('127.0.0.1',a.port),timeout=.1):break
  except OSError:time.sleep(.05)
 fixture=a.B/'evaluation-results/lightcraft-mobile-20261009/source-bundle/original.png';a.value(a.rpc('library.import',{'paths':[str(fixture)]}));query=a.value(a.rpc('catalog.query'));pid=query['photos'][0]['id'];a.value(a.rpc('library.select',{'ids':[pid],'active':pid}));a.value(a.rpc('photo.rate',{'rating':1}));before=log.read_bytes()
 subprocess.run(['chflags','uchg',str(log)],check=True);flag=True
 failed=a.rpc('photo.rate',{'rating':4});info=a.value(a.rpc('library.info'));observed=a.value(a.rpc('catalog.query'));checks={'nativeNotSaved':not failed['ok'] and 'saved in memory but not written to disk' in failed.get('error',''),'unsavedOpsPositive':info.get('unsavedOps',0)>0,'memoryRatingFour':observed['photos'][0]['rating']==4,'diskUnchangedDuringFailure':log.read_bytes()==before}
 subprocess.run(['chflags','nouchg',str(log)],check=True);flag=False
 a.value(a.rpc('library.info'));confirmed=a.value(a.rpc('library.info'));checks['saveRecovered']=confirmed.get('unsavedOps')==0
 (W/'fault-result.json').write_text(json.dumps({'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'method':'user immutable flag on dedicated test journal; restored in finally; original permission-only attempt preserved FAIL','rpc':'fault-rpc.json','replay':False},indent=2)+'\n');print(checks)
finally:
 if flag:subprocess.run(['chflags','nouchg',str(log)],check=True)
 if p.poll() is None:p.terminate()
 p.wait(timeout=15);out.close();err.close();(W/'fault-rpc.json').write_text(json.dumps(a.events,indent=2)+'\n')
