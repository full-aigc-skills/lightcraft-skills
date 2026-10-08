"""已授权固定原生制品的三照片批量验收；真实步骤，不生成视觉结论。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib


def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,required=True);parser.add_argument('--plugin-root',type=Path,required=True);parser.add_argument('--runtime-home',type=Path,required=True);parser.add_argument('--workdir',type=Path,required=True);parser.add_argument('--fixtures',type=Path,required=True);args=parser.parse_args()
 s=args.source_root;p=args.plugin_root;w=args.workdir;w.mkdir(parents=True,exist_ok=False);originals=w/'originals';originals.mkdir();exports=w/'exports';exports.mkdir();library=w/'library';scripts=s/'skills/lightcraft-use/scripts'
 batch=load(scripts/'batch_scope.py','batch');gateway=load(scripts/'command_gateway.py','gateway');core=load(p/'scripts/task_core.py','core');artifacts=load(scripts/'artifacts.py','artifacts')
 for name in ['gradient.png','gradient.jpg']:shutil.copyfile(args.fixtures/name,originals/name)
 def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data))
 pixels=b''.join(b'\x00'+bytes([30,80,150])*96 for _ in range(64))
 (originals/'control.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',96,64,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b''))
 inputs=gateway.capture_inputs([originals])
 def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 def run(name,plan,scriptdir=scripts):
  path=w/(name+'-plan.json');write(path,plan)
  r=subprocess.run([sys.executable,'-I','-B',str(scriptdir/'commands.py'),'run',str(path),'--output',str(w/name),'--runtime-home',str(args.runtime_home),'--require-installed','--library',str(library),'--input',str(originals),'--output-root',str(exports)],capture_output=True,text=True)
  if r.returncode:raise ValueError(r.stdout[-3000:]+r.stderr[-1000:])
  receipt=gateway.read_receipt(w/name/'receipt.json')['receipt'];assert receipt['status']=='NATIVE_EXIT_ZERO_REVIEW_REQUIRED';return receipt
 def step(command,**params):return {'command':command,'params':params}
 first=run('import',{'domain':'lightcraft','steps':[step('library.import',paths=[str(path) for path in sorted(originals.iterdir())],mode='add'),step('catalog.query',limit=100)]})
 ids=first['steps'][0]['native']['result']['imported'];assert len(ids)==3
 photos=first['steps'][1]['native']['result'];write(w/'catalog-result.json',photos)
 # 导入顺序 control.png、gradient.jpg、gradient.png；前两张梯度是目标，对照为纯色。
 target_ids=ids[1:];control_id=ids[0];scope={'targetIds':target_ids,'observedIds':ids,'allowedFields':['light.exposure']}
 r=subprocess.run([sys.executable,'-I','-B',str(scripts/'commands.py'),'discover','--runtime-home',str(args.runtime_home),'--require-installed'],capture_output=True,text=True,check=True);controls=json.loads(r.stdout)['controls']
 initial=batch.prepare(scope,[{'ids':target_ids,'values':{'light.exposure':.5}}],controls);write(w/'source-initial-contract.json',initial)
 receipt=run('source-initial',initial['plan']);initial_fact=batch.verify(initial,receipt);write(w/'source-initial-fact.json',initial_fact)
 def export_plan(name,selected):
  steps=[]
  for identifier in selected:steps.extend([step('library.select',ids=[identifier],active=identifier),step('app.export',path=str(exports/f'{name}-{identifier}.png'),format='png',width=60)])
  return {'domain':'lightcraft','steps':steps}
 run('source-initial-exports',export_plan('source-initial',target_ids))
 revised=batch.prepare(scope,[{'ids':[target_ids[1]],'values':{'light.exposure':.25}}],controls,initial);write(w/'source-revision-contract.json',revised)
 receipt=run('source-revision',revised['plan']);revision_fact=batch.verify(revised,receipt);write(w/'source-revision-fact.json',revision_fact)
 run('source-revision-exports',export_plan('source-revision',target_ids))
 def png_identity(path):
  data=path.read_bytes();offset=8;idat=b'';profile=None;other=[]
  while offset<len(data):
   size=int.from_bytes(data[offset:offset+4],'big');kind=data[offset+4:offset+8];body=data[offset+8:offset+8+size];offset+=size+12
   if kind==b'IDAT':idat+=body
   elif kind==b'iCCP':
    profile=bytearray(zlib.decompress(body[body.index(b'\0')+2:]));profile[24:36]=b'\0'*12
   else:other.append((kind.hex(),hashlib.sha256(body).hexdigest()))
  assert profile is not None
  return {'filteredPixelSha256':hashlib.sha256(zlib.decompress(idat)).hexdigest(),'iccContentExceptCreationTimeSha256':hashlib.sha256(profile).hexdigest(),'otherChunks':other}
 before_identity=png_identity(exports/f'source-initial-{target_ids[0]}.png');after_identity=png_identity(exports/f'source-revision-{target_ids[0]}.png')
 assert before_identity==after_identity
 write(w/'unmodified-export-comparison.json',{'status':'PASS','pixelAndProfileIdentity':before_identity,'beforeFileSha256':gateway.file_sha(exports/f'source-initial-{target_ids[0]}.png'),'afterFileSha256':gateway.file_sha(exports/f'source-revision-{target_ids[0]}.png'),'allowedDifference':'ICC header creation timestamp bytes 24:36 only; every other chunk and profile byte must match'})
 assert gateway.file_sha(exports/f'source-initial-{target_ids[1]}.png')!=gateway.file_sha(exports/f'source-revision-{target_ids[1]}.png')
 fact=[artifacts.verify(path,exports,{'format':'png','width':60,'height':40,'bitDepth':8}) for path in sorted(exports.iterdir())];assert all(a['technicalStatus']=='PASS' for a in fact)
 reopen=run('source-reopen',{'domain':'lightcraft','steps':[step('photo.inspect',id=i) for i in ids]+[step('library.info')]})
 for row in reopen['steps'][:-1]:assert row['native']['result']['develop']==revision_fact['afterSettings'][str(row['native']['result']['id'])]
 assert reopen['steps'][-1]['native']['result']['unsavedOps']==0
 # 插件采用已公开受保护技能快照执行，上游新资源不偷偷覆盖。
 plugin_contract=batch.prepare(scope,[{'ids':target_ids,'values':{'light.exposure':.75}}],controls);plan=plugin_contract['plan'];plan['steps']+=export_plan('plugin-initial',target_ids)['steps']
 task=w/'plugin-task';state=core.create(task,{'request':'第一张曝光 0.75，第二张曝光 0.125；初始批量候选故意以 0.75 验证失败后选择性修订'},plan,[str(originals)],library=str(library),output_root=str(exports),batch_scope=scope)
 state=core.run(task,args.runtime_home);assert state['status']=='VERIFYING',state.get('controllerError');assert state['batchObservation']['status']=='PASS'
 receipt=json.loads(Path(state['receiptPath']).read_text());latest={row['native']['result']['id']:row['native']['result'] for row in receipt['steps'] if row['command']=='photo.inspect'}
 candidates=[{'path':str(exports/f'plugin-initial-{i}.png'),'expected':{'width':60,'format':'png'}} for i in target_ids]
 review=core.review_request(task,candidates,{str(i):latest[i]['develop'] for i in target_ids},'batch-selective-v1')
 assert gateway.capture_inputs([originals])==inputs
 result={'schemaVersion':1,'scope':scope,'sourceBatch':'PASS','sourceSelectiveRevision':'PASS','sourceReopen':'PASS','pluginInitialExecution':'PASS','pluginVisual':'AWAITING_ACTUAL_REVIEW','inputSha256':inputs,'sourceArtifacts':fact,'task':str(task),'reviewRequest':review,'workdir':str(w)}
 write(w/'index.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['reviewRequest','sourceArtifacts']},ensure_ascii=False))

if __name__=='__main__':main()
