"""逐样本 RAW 来源、相机与解码事实；不下载、不安装、不执行原生程序。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def gateway():
 spec=importlib.util.spec_from_file_location('raw_gateway',Path(__file__).with_name('command_gateway.py'))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def digest(value):
 return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False).encode()).hexdigest()


def validate_manifest(manifest):
 """在所有执行之前核对全部样本身份和许可记录；不把记录视为自动下载授权。"""
 if not isinstance(manifest,dict) or set(manifest)!={'schemaVersion','samples'} or type(manifest.get('schemaVersion')) is not int or manifest['schemaVersion']!=1:raise ValueError('raw_manifest_schema_invalid')
 rows=manifest['samples']
 if not isinstance(rows,list) or not 1<=len(rows)<=64:raise ValueError('raw_manifest_samples_invalid')
 required={'sampleId','make','model','variant','license','licenseUrl','sourceUrl','catalogUrl','path','bytes','sha256'};seen=set();paths=set();hashes=set()
 for row in rows:
  if not isinstance(row,dict) or not required<=set(row) or set(row)-required-{'catalogEntryPath','catalogEntrySha256'}:raise ValueError('raw_sample_metadata_missing')
  for name in required-{'bytes'}:
   if not isinstance(row[name],str) or not row[name].strip():raise ValueError('raw_sample_metadata_invalid: '+name)
  if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,100}',row['sampleId']) or row['sampleId'] in seen:raise ValueError('raw_sample_identity_duplicate_or_invalid')
  seen.add(row['sampleId'])
  if type(row['bytes']) is not int or row['bytes']<=0 or not re.fullmatch('[0-9a-f]{64}',row['sha256']):raise ValueError('raw_sample_size_or_digest_invalid')
  for name in ('licenseUrl','sourceUrl','catalogUrl'):
   url=urlsplit(row[name])
   if url.scheme!='https' or not url.hostname or url.username or url.password or url.fragment:raise ValueError('raw_source_url_invalid')
  path=Path(row['path'])
  if path.is_symlink() or not path.is_file():raise ValueError('raw_sample_regular_file_required')
  if str(path.resolve()) in paths or row['sha256'] in hashes:raise ValueError('raw_sample_identity_duplicate_or_invalid')
  paths.add(str(path.resolve()));hashes.add(row['sha256'])
  if path.stat().st_size!=row['bytes'] or gateway().file_sha(path)!=row['sha256']:raise ValueError('raw_sample_changed')
  if 'catalogEntryPath' in row or 'catalogEntrySha256' in row:
   if not {'catalogEntryPath','catalogEntrySha256'}<=set(row):raise ValueError('raw_catalog_identity_missing')
   entry_path=Path(row['catalogEntryPath'])
   if entry_path.is_symlink() or not entry_path.is_file() or entry_path.stat().st_size>65536:raise ValueError('raw_catalog_entry_invalid')
   entry=gateway().strict_json(entry_path.read_text())
   if (digest(entry)!=row['catalogEntrySha256'] or not isinstance(entry,list) or len(entry)<8 or entry[:3]!=[row['make'],row['model'],row['variant']]
       or not isinstance(entry[5],str) or row['licenseUrl'] not in entry[5] or not isinstance(entry[7],str) or row['sha256'] not in entry[7] or row['sourceUrl'] not in entry[7]):raise ValueError('raw_catalog_metadata_mismatch')
 return manifest


def camera_matches(sample,observed):
 """仅消除已知厂商前缀/法人名称，不做型号模糊匹配。"""
 if not isinstance(observed,str) or not observed.strip():return False
 words=lambda value:re.sub(r'\s+',' ',value.strip().casefold())
 make=words(sample['make']);model=words(sample['model']);value=words(observed)
 aliases={'nikon':['nikon corporation','nikon'],'canon':['canon'],'blackmagic':['blackmagic design','blackmagic']}.get(make,[make])
 def strip(value):
  found=False
  while True:
   prefix=next((name+' ' for name in aliases if value.startswith(name+' ')),None)
   if prefix is None:return value,found
   value=value[len(prefix):];found=True
 model,_=strip(model);value,found=strip(value)
 return found and value==model


def decode_mode(photo):
 """原生 nullable previewOnly 原样分类；布尔或缺失字段一律未知。"""
 if not isinstance(photo,dict) or photo.get('kind')!='raw' or 'previewOnly' not in photo:return 'UNKNOWN'
 value=photo['previewOnly']
 if value is None:return 'FULL_RAW_REPORTED'
 if isinstance(value,str) and value.strip():return 'PREVIEW_FALLBACK'
 return 'UNKNOWN'


def unsupported_reason(receipt,source):
 """只识别完整回执内原生明确不支持的单文件导入，环境错误不算不支持。"""
 if not isinstance(receipt,dict) or receipt.get('status')!='FAILED_OR_PARTIAL' or receipt.get('protocolComplete') is not True:return None
 rows=receipt.get('steps',[])
 if not isinstance(rows,list) or not rows:return None
 row=rows[0]
 if not isinstance(row,dict) or not isinstance(row.get('native'),dict) or not isinstance(row['native'].get('result'),dict):return None
 native=row['native'];result=native['result']
 if row.get('command')!='library.import' or row.get('status')!='PARTIAL' or native.get('ok') is not True or result.get('imported') or result.get('duplicates'):return None
 failed=result.get('failed')
 if not isinstance(failed,list) or len(failed)!=1 or not isinstance(failed[0],list) or len(failed[0])!=2 or failed[0][0]!=source:return None
 reason=failed[0][1]
 if isinstance(reason,str) and (reason.startswith('unsupported raw (') or reason=='RawOther files are not supported yet'):return reason
 return None


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('manifest',type=Path);args=parser.parse_args()
 try:
  value=validate_manifest(gateway().strict_json(args.manifest.read_text()));print(json.dumps({'schemaVersion':1,'status':'PASS','samples':len(value['samples']),'manifestSha256':digest(value),'execution':'NOT_RUN'}))
 except (ValueError,OSError,TypeError,KeyError) as error:print(json.dumps({'error':str(error),'execution':'NOT_RUN'}));raise SystemExit(1)
