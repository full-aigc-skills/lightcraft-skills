"""显式批量范围与选择性修订；仅生成计划和核对事实，不执行或重放。"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re


def load(name):
 spec=importlib.util.spec_from_file_location('batch_'+name,Path(__file__).with_name(name+'.py'))
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def ids(values):
 if not isinstance(values,list) or not values or len(values)>200 or any(type(v) is not int or v<=0 for v in values) or len(set(values))!=len(values):raise ValueError('batch_ids_invalid')
 return values


def prepare(scope,changes,controls,parent=None):
 """校验固定范围和控件，返回按 ID 观测及修改的单会话计划。"""
 if not isinstance(scope,dict) or set(scope)!={'targetIds','observedIds','allowedFields'}:raise ValueError('batch_scope_invalid')
 targets=ids(scope['targetIds']);observed=ids(scope['observedIds']);fields=scope['allowedFields']
 if not set(targets)<=set(observed):raise ValueError('batch_targets_not_observed')
 if not isinstance(fields,list) or not fields or any(not isinstance(f,str) or not re.fullmatch(r'[a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)+',f) for f in fields) or len(set(fields))!=len(fields):raise ValueError('batch_fields_invalid')
 if parent is not None and (not isinstance(parent,dict) or parent.get('schemaVersion')!=1 or parent.get('scope')!=scope):raise ValueError('batch_revision_scope_changed')
 if not isinstance(changes,list) or not changes or len(changes)>200:raise ValueError('batch_changes_invalid')
 workflow=load('photo_workflows');seen=set();plan=[]
 for change in changes:
  if not isinstance(change,dict) or set(change)!={'ids','values'}:raise ValueError('batch_change_invalid')
  current=ids(change['ids']);values=change['values']
  if not set(current)<=set(targets) or not isinstance(values,dict) or not values or not set(values)<=set(fields):raise ValueError('batch_change_outside_scope')
  # 复用现有原生控件范围校验；虚拟基线仅用于检查值，并非运行结果。
  baseline={}
  for field in values:
   cursor=baseline;parts=field.split('.')
   for part in parts[:-1]:cursor=cursor.setdefault(part,{})
   cursor[parts[-1]]=0
  workflow.apply_local_changes(baseline,values,controls)
  for identifier in current:
   for field in values:
    key=(identifier,field)
    if key in seen:raise ValueError('duplicate_batch_write')
    seen.add(key)
 for identifier in observed:plan += [{'command':'photo.inspect','params':{'id':identifier}},{'command':'develop.get','params':{'id':identifier}}]
 plan += [{'command':'develop.set','params':copy.deepcopy(change)} for change in changes]
 for identifier in observed:plan += [{'command':'photo.inspect','params':{'id':identifier}},{'command':'develop.get','params':{'id':identifier}}]
 plan += [{'command':'library.info','params':{}}]
 if len(plan)>1000:raise ValueError('batch_plan_too_large')
 return {'schemaVersion':1,'scope':copy.deepcopy(scope),'changes':copy.deepcopy(changes),'controls':copy.deepcopy(controls),
         'parentContractSha256':digest(parent) if parent is not None else None,'plan':{'domain':'lightcraft','steps':plan},'automaticReplay':False}


def compare(contract,before,after):
 """核对完整设置：未修改照片和所有未授权字段均须保持不变。"""
 expected_keys={str(i) for i in contract['scope']['observedIds']}
 if not isinstance(before,dict) or not isinstance(after,dict) or set(before)!=expected_keys or set(after)!=expected_keys:raise ValueError('batch_observation_incomplete')
 expected=copy.deepcopy(before);workflow=load('photo_workflows')
 for change in contract['changes']:
  for identifier in change['ids']:expected[str(identifier)]=workflow.apply_local_changes(expected[str(identifier)],change['values'],contract['controls'])
 if not load('command_gateway').json_equal(expected,after):raise ValueError('batch_settings_outside_scope')
 return {'status':'PASS','observedIds':contract['scope']['observedIds'],'changedIds':sorted({i for c in contract['changes'] for i in c['ids']}),'automaticReplay':False,'visualAcceptance':'NOT_RUN'}


def verify(contract,receipt):
 """核对当前资源、原生执行及完整观测；不接受旧记录或用户自报通过。"""
 gateway=load('command_gateway');rebuilt=prepare(contract['scope'],contract['changes'],contract['controls'])
 if rebuilt['plan']!=contract['plan']:raise ValueError('batch_contract_plan_mismatch')
 if (receipt.get('schemaVersion')!=1 or receipt.get('status')!='NATIVE_EXIT_ZERO_REVIEW_REQUIRED' or receipt.get('protocolComplete') is not True
     or receipt.get('planSha256')!=digest(contract['plan']) or receipt.get('skillResourceSha256')!=gateway.capture_resources(Path(__file__).parent)
     or not receipt.get('inputSha256') or receipt.get('inputSha256')!=receipt.get('inputAfterSha256')
     or receipt.get('skillResourceAfterSha256')!=receipt.get('skillResourceSha256')
     or receipt.get('runtimeLockSha256')!=gateway.file_sha(Path(__file__).with_name('runtime.lock.json'))
     or receipt.get('process',{}).get('status')!='EXITED' or receipt.get('process',{}).get('exitCode')!=0 or receipt.get('process',{}).get('logComplete') is not True):raise ValueError('batch_receipt_identity_mismatch')
 lock=json.loads(Path(__file__).with_name('runtime.lock.json').read_text());native=receipt.get('runtimeIdentity',{})
 if native.get('version')!=lock['resolvedVersion'] or native.get('binarySha256') not in {v['binarySha256'] for v in lock['artifacts'].values()} or native.get('mode')!='Headless':raise ValueError('batch_native_identity_mismatch')
 rows=receipt.get('steps',[]);steps=contract['plan']['steps'];n=len(contract['scope']['observedIds']);before={};after={};photos=[]
 if len(rows)!=len(steps) or any(r.get('index')!=i or r.get('command')!=steps[i]['command'] or r.get('status')!='SUCCEEDED' for i,r in enumerate(rows)):raise ValueError('batch_steps_incomplete')
 for index,identifier in enumerate(contract['scope']['observedIds']):
  photo=rows[2*index].get('native',{}).get('result',{});source=photo.get('source',{})
  if photo.get('id')!=identifier or source.get('type')!='file' or source.get('path') not in receipt['inputSha256']:raise ValueError('batch_photo_identity_mismatch')
  photos.append(photo);before[str(identifier)]=rows[2*index+1]['native']['result']
  offset=2*n+len(contract['changes'])+2*index
  after_photo=rows[offset]['native']['result']
  if after_photo.get('id')!=identifier or after_photo.get('source')!=source:raise ValueError('batch_photo_identity_changed')
  after[str(identifier)]=rows[offset+1]['native']['result']
  if photo.get('develop')!=before[str(identifier)] or after_photo.get('develop')!=after[str(identifier)]:raise ValueError('batch_settings_identity_mismatch')
 result=compare(contract,before,after)
 result.update(schemaVersion=1,contractSha256=digest(contract),runId=receipt['runId'],planSha256=receipt['planSha256'],photos=photos,beforeSettings=before,afterSettings=after,runtimeIdentity=native,persistence=rows[-1]['native']['result'],completeAcceptance=False)
 return result


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','verify']);parser.add_argument('request',type=Path);parser.add_argument('--receipt',type=Path);parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();gateway=load('command_gateway')
 try:
  request=gateway.strict_json(args.request.read_text())
  result=prepare(**request) if args.action=='prepare' else verify(request,gateway.read_receipt(args.receipt)['receipt'])
  # 同目录 O_EXCL：失败不覆盖人工合同，不在检查时启动原生程序。
  with args.output.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
  print(json.dumps({'output':str(args.output),'automaticReplay':False}));return 0
 except (OSError,ValueError,TypeError,KeyError) as error:print(json.dumps({'error':str(error),'automaticReplay':False}));return 1

if __name__=='__main__':raise SystemExit(main())
