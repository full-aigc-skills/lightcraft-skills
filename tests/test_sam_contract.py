"""SAM 可用性与文件身份回归；假模型只用于负向测试。"""
import importlib.util
import hashlib
from unittest import mock
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
def api():
 spec=importlib.util.spec_from_file_location('sam_contract',ROOT/'runtime/sam_contract.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class SamContract(unittest.TestCase):
 def snapshot(self,commands=()):
  lock=json.loads((ROOT/'runtime/runtime.lock.json').read_text());binary=lock['artifacts']['darwin-arm64']['binarySha256']
  return {'domain':'lightcraft','mode':'Headless','executionAllowed':True,'executableIdentity':{'version':lock['resolvedVersion'],'binarySha256':binary,'status':'READY'},'commands':[{'id':c} for c in commands]}
 def test_absent_command_is_unknown_not_feature_false(self):
  r=api().assess(self.snapshot());self.assertEqual(r['compileFeature'],'UNKNOWN');self.assertIn('status_command_absent',r['blockers']);self.assertFalse(r['executionAllowed']);self.assertFalse(r['downloadAllowed'])
 def test_command_presence_is_not_feature_enabled(self):
  r=api().assess(self.snapshot(['segment.model.status']));self.assertEqual(r['compileFeature'],'UNKNOWN');self.assertIn('status_not_observed',r['blockers'])
 def test_boolean_types_and_license_are_required(self):
  m=api();s=self.snapshot(['segment.model.status']);status={'available':False,'installed':False,'loaded':False,'busy':False,'analyzing':False,'sizeBytes':3439938512,'license':'SAM License (Meta)','licenseUrl':m.LICENSE_URL}
  self.assertEqual(m.assess(s,status)['compileFeature'],'REPORTED_DISABLED')
  for key,value in [('available',1),('installed','false'),('sizeBytes',True),('license','Apache-2.0'),('licenseUrl','https://example.com')]:
   with self.subTest(key=key),self.assertRaises(ValueError):m.assess(s,dict(status,**{key:value}))
 def test_status_cannot_be_attached_to_missing_command(self):
  with self.assertRaises(ValueError):api().assess(self.snapshot(),{})
 def test_offline_wrong_domain_and_binary_identity_rejected(self):
  for key,value in [('mode','offline'),('domain','printcraft'),('executionAllowed',1),('executableIdentity',{'status':'READY','version':'0.2.2','binarySha256':'0'*64})]:
   with self.subTest(key=key),self.assertRaises(ValueError):api().assess(dict(self.snapshot(),**{key:value}))
 def test_local_files_are_checked_without_creating_or_downloading(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/'models';r=api().assess(self.snapshot(),model_dir=p);self.assertFalse(p.exists());self.assertEqual(r['modelFiles'][0]['status'],'MISSING')
   p.mkdir();(p/'model.safetensors').write_bytes(b'fake weights');(p/'vocab.json').write_bytes(b'fake vocab');(p/'merges.txt').symlink_to(p/'vocab.json')
   r=api().assess(self.snapshot(),model_dir=p);self.assertFalse(r['modelIdentityVerified']);self.assertEqual([x['status'] for x in r['modelFiles']],['SIZE_MISMATCH','SIZE_MISMATCH','NOT_REGULAR'])
 def test_local_content_digest_checks_use_both_identities(self):
  m=api()
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);content=b'fake test only';rows=[]
   for item in m.FILES:
    row=dict(item,bytes=len(content));(root/row['name']).write_bytes(content)
    if 'sha256' in row:row['sha256']=hashlib.sha256(content).hexdigest()
    if 'gitBlobSha1' in row:row['gitBlobSha1']=hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()
    rows.append(row)
   with mock.patch.object(m,'FILES',tuple(rows)):
    self.assertTrue(all(row['status']=='IDENTITY_MATCH' for row in m.file_facts(root)))
    for row in rows:(root/row['name']).write_bytes(b'X'*len(content))
    self.assertTrue(all(row['status']=='DIGEST_MISMATCH' for row in m.file_facts(root)))
 def test_model_directory_symlink_is_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);actual=root/'actual';actual.mkdir();alias=root/'alias';alias.symlink_to(actual,target_is_directory=True)
   self.assertTrue(all(row['status']=='NOT_REGULAR' for row in api().file_facts(alias)))
 def test_manifest_is_immutable_and_approval_never_inferred(self):
  r=api().assess(self.snapshot());self.assertEqual(r['modelManifest']['revision'],'3c879f39826c281e95690f02c7821c4de09afae7');self.assertFalse(r['automaticReplay']);self.assertFalse(r['completeAcceptance']);self.assertEqual(r['authorization'],{'download':'NOT_GRANTED','execution':'NOT_GRANTED'})
if __name__=='__main__':unittest.main()
