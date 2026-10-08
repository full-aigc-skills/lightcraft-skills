"""RAW 样本身份与结果分层；假文件仅用于失败回归。"""
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
def contract():
 spec=importlib.util.spec_from_file_location('raw_contract',ROOT/'runtime/raw_contract.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def sample(path):
 return {'sampleId':'nikon-d2h','make':'Nikon','model':'D2H','variant':'12bit compressed','license':'CC0-1.0','licenseUrl':'https://creativecommons.org/publicdomain/zero/1.0/','sourceUrl':'https://raw.pixls.us/getfile.php/5227','catalogUrl':'https://raw.pixls.us/','path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

class RawContract(unittest.TestCase):
 def test_metadata_size_hash_and_unique_identity_required(self):
  with tempfile.TemporaryDirectory() as temp:
   file=Path(temp)/'sample.nef';file.write_bytes(b'unit fixture');good=sample(file);api=contract()
   self.assertEqual(api.validate_manifest({'schemaVersion':1,'samples':[good]})['samples'][0]['sampleId'],'nikon-d2h')
   for key,value in [('model',''),('variant',''),('license',''),('sha256','0'*64),('bytes',True),('bytes',999),('sourceUrl','http://raw.pixls.us/x')]:
    bad=dict(good);bad[key]=value
    with self.subTest(key=key),self.assertRaises(ValueError):api.validate_manifest({'schemaVersion':1,'samples':[bad]})
   with self.assertRaises(ValueError):api.validate_manifest({'schemaVersion':1,'samples':[good,good]})
 def test_symlink_is_rejected_before_resolve(self):
  with tempfile.TemporaryDirectory() as temp:
   file=Path(temp)/'sample.nef';file.write_bytes(b'unit');row=sample(file);alias=Path(temp)/'alias.nef';alias.symlink_to(file);row['path']=str(alias)
   with self.assertRaises(ValueError):contract().validate_manifest({'schemaVersion':1,'samples':[row]})
 def test_camera_brand_aliases_do_not_allow_wrong_model(self):
  row={'make':'Nikon','model':'D2H'};api=contract()
  self.assertTrue(api.camera_matches(row,'NIKON CORPORATION NIKON D2H'))
  self.assertFalse(api.camera_matches(row,'Canon Canon EOS 7D'))
  self.assertFalse(api.camera_matches(row,'NIKON D2X'))
  self.assertFalse(api.camera_matches(row,None))
 def test_preview_reason_is_not_boolean_or_extension(self):
  api=contract()
  self.assertEqual(api.decode_mode({'kind':'raw','previewOnly':None}),'FULL_RAW_REPORTED')
  self.assertEqual(api.decode_mode({'kind':'raw','previewOnly':'Canon sRAW/mRAW'}),'PREVIEW_FALLBACK')
  for photo in [{'kind':'raw'},{'kind':'raw','previewOnly':False},{'kind':'raw','previewOnly':''},{'kind':'image','previewOnly':None}]:self.assertEqual(api.decode_mode(photo),'UNKNOWN')
 def test_only_explicit_native_unsupported_import_counts(self):
  api=contract();path='/sample.nef'
  for reason in ['unsupported raw (compression) without an embedded preview','RawOther files are not supported yet']:
   receipt={'status':'FAILED_OR_PARTIAL','protocolComplete':True,'steps':[{'command':'library.import','status':'PARTIAL','native':{'ok':True,'result':{'imported':[],'duplicates':[],'failed':[[path,reason]]}}}]}
   self.assertIsNotNone(api.unsupported_reason(receipt,path))
   receipt['steps'][0]['native']['result']['failed'][0][1]='Permission denied';self.assertIsNone(api.unsupported_reason(receipt,path))
   receipt['status']='UNKNOWN';self.assertIsNone(api.unsupported_reason(receipt,path))
 def test_catalog_entry_cannot_claim_other_variant(self):
  with tempfile.TemporaryDirectory() as temp:
   file=Path(temp)/'sample.nef';file.write_bytes(b'unit');row=sample(file);entry=Path(temp)/'entry.json';data=['Nikon','D2H','OTHER',0,'',row['licenseUrl'],'',row['sourceUrl']+' '+row['sha256']];entry.write_text(json.dumps(data))
   row.update(catalogEntryPath=str(entry),catalogEntrySha256=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest())
   with self.assertRaisesRegex(ValueError,'catalog'):contract().validate_manifest({'schemaVersion':1,'samples':[row]})

if __name__=='__main__':unittest.main()
