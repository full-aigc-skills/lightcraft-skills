"""批量显影范围、选择性修订和回执身份的行为回归。"""
import importlib.util
from pathlib import Path
import copy
import unittest

ROOT=Path(__file__).resolve().parents[1]

def module():
 spec=importlib.util.spec_from_file_location('batch_scope',ROOT/'runtime/batch_scope.py')
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

class BatchScope(unittest.TestCase):
 def setUp(self):
  self.scope={'targetIds':[1,2],'observedIds':[1,2,3],'allowedFields':['light.exposure']}
  self.controls=[{'id':'light.exposure','min':-5,'max':5}]
  self.changes=[{'ids':[1,2],'values':{'light.exposure':.5}}]
 def test_explicit_batch_and_single_photo_revision(self):
  api=module();first=api.prepare(self.scope,self.changes,self.controls)
  revision=api.prepare(self.scope,[{'ids':[2],'values':{'light.exposure':.25}}],self.controls,first)
  writes=[r for r in revision['plan']['steps'] if r['command']=='develop.set']
  self.assertEqual(writes,[{'command':'develop.set','params':{'ids':[2],'values':{'light.exposure':.25}}}])
  self.assertEqual(revision['parentContractSha256'],api.digest(first))
 def test_invalid_ids_rejected_before_plan(self):
  for ids in [[],[True],[0],[1,1],[4]]:
   with self.subTest(ids=ids),self.assertRaises(ValueError):module().prepare(self.scope,[{'ids':ids,'values':{'light.exposure':.5}}],self.controls)
 def test_allowed_fields_cannot_expand_or_reset(self):
  for values in [{'light.contrast':.5},{'light.exposure':8},{'light.exposure':True},{'light.exposure':float('nan')},{}]:
   with self.subTest(values=values),self.assertRaises(ValueError):module().prepare(self.scope,[{'ids':[1],'values':values}],self.controls)
 def test_revision_cannot_change_original_scope(self):
  api=module();first=api.prepare(self.scope,self.changes,self.controls);scope=copy.deepcopy(self.scope);scope['targetIds'].append(3)
  with self.assertRaisesRegex(ValueError,'scope_changed'):api.prepare(scope,self.changes,self.controls,first)
 def test_unobserved_targets_and_duplicate_writes_rejected(self):
  scope=copy.deepcopy(self.scope);scope['observedIds']=[1,3]
  with self.assertRaises(ValueError):module().prepare(scope,self.changes,self.controls)
  with self.assertRaises(ValueError):module().prepare(self.scope,self.changes*2,self.controls)
 def test_compare_preserves_unmodified_photo_and_other_fields(self):
  api=module();contract=api.prepare(self.scope,[{'ids':[2],'values':{'light.exposure':.25}}],self.controls)
  before={str(i):{'light':{'exposure':0,'contrast':0}} for i in [1,2,3]};after=copy.deepcopy(before);after['2']['light']['exposure']=.25
  self.assertEqual(api.compare(contract,before,after)['status'],'PASS')
  for photo,key in [('1','exposure'),('2','contrast'),('3','exposure')]:
   mutated=copy.deepcopy(after);mutated[photo]['light'][key]=1
   with self.subTest(photo=photo,key=key),self.assertRaisesRegex(ValueError,'settings_outside_scope'):api.compare(contract,before,mutated)
 def test_missing_observation_is_not_success(self):
  api=module();contract=api.prepare(self.scope,self.changes,self.controls)
  with self.assertRaisesRegex(ValueError,'observation'):api.compare(contract,{'1':{}},{'1':{}})


 def test_receipt_identity_and_current_resources_required(self):
  api=module();gateway=api.load('command_gateway');contract=api.prepare(self.scope,self.changes,self.controls)
  source='/synthetic/original.png';base={'light':{'exposure':0,'contrast':0}};current=copy.deepcopy(base);rows=[]
  for i,step in enumerate(contract['plan']['steps']):
   identifier=step['params'].get('id');result={}
   if step['command']=='develop.set':current['light']['exposure']=.5
   elif step['command']=='photo.inspect':result={'id':identifier,'source':{'type':'file','path':source},'develop':copy.deepcopy(current if identifier in [1,2] else base)}
   elif step['command']=='develop.get':result=copy.deepcopy(current if identifier in [1,2] else base)
   rows.append({'index':i,'command':step['command'],'status':'SUCCEEDED','native':{'result':result}})
  import json
  lock=json.loads((ROOT/'runtime/runtime.lock.json').read_text());resources=gateway.capture_resources(ROOT/'runtime')
  receipt={'schemaVersion':1,'status':'NATIVE_EXIT_ZERO_REVIEW_REQUIRED','protocolComplete':True,'planSha256':api.digest(contract['plan']),
   'skillResourceSha256':resources,'skillResourceAfterSha256':resources,'inputSha256':{source:'0'*64},'inputAfterSha256':{source:'0'*64},
   'runtimeLockSha256':gateway.file_sha(ROOT/'runtime/runtime.lock.json'),'process':{'status':'EXITED','exitCode':0,'logComplete':True},
   'runtimeIdentity':{'version':lock['resolvedVersion'],'binarySha256':next(iter(lock['artifacts'].values()))['binarySha256'],'mode':'Headless'},'steps':rows,'runId':'synthetic-unit-only'}
  self.assertEqual(api.verify(contract,receipt)['status'],'PASS')
  for key,value in [('planSha256','0'*64),('status','UNKNOWN'),('skillResourceAfterSha256',{}),('inputAfterSha256',{})]:
   changed=copy.deepcopy(receipt);changed[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):api.verify(contract,changed)
  changed=copy.deepcopy(receipt);changed['steps'][-3]['native']['result']['develop']['light']['contrast']=1
  with self.assertRaises(ValueError):api.verify(contract,changed)

if __name__=='__main__':unittest.main()
