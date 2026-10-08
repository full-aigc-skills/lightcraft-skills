import subprocess,json,threading,queue,pathlib,time
out=pathlib.Path('/tmp/lightcraft-acceptance-HoMkD5');q=queue.Queue()
with (out/'host-server.stderr.log').open('w') as err:
 p=subprocess.Popen(['codex','app-server','--stdio'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
 def reader():
  for line in p.stdout:q.put(json.loads(line))
 threading.Thread(target=reader,daemon=True).start()
 def rpc(i,method,params):
  p.stdin.write(json.dumps({'id':i,'method':method,'params':params})+'\n');p.stdin.flush();deadline=time.monotonic()+45
  while time.monotonic()<deadline:
   r=q.get(timeout=max(.1,deadline-time.monotonic()))
   if r.get('id')==i:
    if 'error' in r:raise ValueError(r['error'])
    return r['result']
  raise TimeoutError(method)
 try:
  init=rpc(1,'initialize',{'clientInfo':{'name':'lightcraft_acceptance','version':'0.1.0'},'capabilities':{'experimentalApi':True}})
  p.stdin.write(json.dumps({'method':'initialized','params':{}})+'\n');p.stdin.flush()
  skills=rpc(2,'skills/list',{'cwds':['/tmp/lightcraft-acceptance-HoMkD5'],'forceReload':True})
  records=[]
  for item in skills.get('data',[]):
   records.extend(s for s in item.get('skills',[]) if 'lightcraft' in s.get('name',''))
  evidence={'initialize':init,'skills':records,'errors':[e for item in skills.get('data',[]) for e in item.get('errors',[]) if 'lightcraft' in str(e)]}
  (out/'host-discovery.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
  print(json.dumps(evidence,ensure_ascii=False))
 finally:
  p.terminate();p.wait(timeout=10)
