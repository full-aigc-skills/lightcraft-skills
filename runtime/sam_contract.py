"""SAM 3 身份与可用性只读评估；不下载、安装、接受许可或执行模型。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

LICENSE_URL='https://github.com/facebookresearch/sam3/blob/main/LICENSE'
REVISION='3c879f39826c281e95690f02c7821c4de09afae7'
FILES=(
 {'name':'model.safetensors','bytes':3439938512,'sha256':'6d06f0a5f84e435071fe6603e61d0b4cc7b40e0d39d487cfd4d67d8cc11cc14a','digestSource':'lightcraft upstream crates/segment/src/fetch/mod.rs; official gated API digest redacted'},
 {'name':'vocab.json','bytes':862328,'gitBlobSha1':'182766ce89b439768edadda342519f33802f5364','digestSource':'official Hugging Face Git tree'},
 {'name':'merges.txt','bytes':524619,'gitBlobSha1':'76e821f1b6f0a9709293c3b6b51ed90980b3166b','digestSource':'official Hugging Face Git tree'},
)

def resource(name):
    sibling=Path(__file__).with_name(name)
    return sibling if sibling.is_file() else Path(__file__).resolve().parents[1]/'skills/lightcraft-use/scripts'/name

def gateway():
    spec=importlib.util.spec_from_file_location('sam_gateway',resource('command_gateway.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False).encode()).hexdigest()

def manifest():
    return {'model':'facebook/sam3','revision':REVISION,'license':'SAM License (Meta)','licenseUrl':LICENSE_URL,'gated':'manual','files':[dict(row,sourceUrl=f'https://huggingface.co/facebook/sam3/resolve/{REVISION}/{row["name"]}') for row in FILES]}

def file_facts(directory):
    """只检查现有普通文件；流式读取权重，不打开链接或接受部分下载。"""
    rows=[]
    for expected in FILES:
        row={'name':expected['name'],'status':'NOT_CHECKED'}
        if directory is not None:
            path=Path(directory)/expected['name'];row['path']=str(path.absolute())
            if Path(directory).is_symlink() or path.is_symlink():row['status']='NOT_REGULAR'
            elif not path.exists():row['status']='MISSING'
            elif not path.is_file():row['status']='NOT_REGULAR'
            elif path.stat().st_size!=expected['bytes']:row['status']='SIZE_MISMATCH'
            else:
                before=path.stat();sha=hashlib.sha256();git=hashlib.sha1(f'blob {before.st_size}\0'.encode())
                with path.open('rb') as stream:
                    while chunk:=stream.read(1024*1024):sha.update(chunk);git.update(chunk)
                after=path.stat();row.update(bytes=before.st_size,sha256=sha.hexdigest(),gitBlobSha1=git.hexdigest())
                if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):row['status']='CHANGED_DURING_READ'
                elif expected.get('sha256',row['sha256'])!=row['sha256'] or expected.get('gitBlobSha1',row['gitBlobSha1'])!=row['gitBlobSha1']:row['status']='DIGEST_MISMATCH'
                else:row['status']='IDENTITY_MATCH'
        rows.append(row)
    return rows

def assess(snapshot,status=None,model_dir=None):
    """用户提供的状态只记录为 reported；匹配身份不能证明实际推理通过。"""
    lock=gateway().strict_json(resource('runtime.lock.json').read_text())
    if not isinstance(snapshot,dict) or snapshot.get('domain')!='lightcraft' or snapshot.get('mode')!='Headless' or snapshot.get('executionAllowed') is not True:raise ValueError('sam_live_snapshot_required')
    identity=snapshot.get('executableIdentity')
    if not isinstance(identity,dict) or identity.get('status')!='READY' or identity.get('version')!=lock['resolvedVersion'] or identity.get('binarySha256') not in {row['binarySha256'] for row in lock['artifacts'].values()}:raise ValueError('sam_runtime_identity_mismatch')
    commands=snapshot.get('commands')
    if not isinstance(commands,list) or any(not isinstance(row,dict) or not isinstance(row.get('id'),str) for row in commands):raise ValueError('sam_command_catalog_invalid')
    ids=[row['id'] for row in commands]
    if len(ids)!=len(set(ids)):raise ValueError('sam_duplicate_command')
    present='segment.model.status' in ids;feature='UNKNOWN';blockers=[]
    if not present:
        if status is not None:raise ValueError('sam_status_without_command')
        blockers.append('status_command_absent')
    elif status is None:blockers.append('status_not_observed')
    else:
        if not isinstance(status,dict) or any(type(status.get(key)) is not bool for key in ('available','installed','loaded','busy','analyzing')):raise ValueError('sam_status_boolean_required')
        if type(status.get('sizeBytes')) is not int or status['sizeBytes']!=FILES[0]['bytes'] or status.get('license')!='SAM License (Meta)' or status.get('licenseUrl')!=LICENSE_URL:raise ValueError('sam_status_model_identity_mismatch')
        if not status['available'] and (status['installed'] or status['loaded'] or status['busy'] or status['analyzing']):raise ValueError('sam_status_inconsistent')
        feature='REPORTED_ENABLED' if status['available'] else 'REPORTED_DISABLED'
        if not status['available']:blockers.append('build_reports_unavailable')
        if not status['installed']:blockers.append('build_reports_not_installed')
        blockers.append('status_not_bound_to_native_receipt')
    facts=file_facts(model_dir);verified=all(row['status']=='IDENTITY_MATCH' for row in facts)
    if not verified:blockers.append('model_identity_not_verified')
    blockers+=['download_authorization_not_granted','execution_authorization_not_granted','real_segmentation_not_verified']
    model=manifest()
    return {'schemaVersion':1,'reportKind':'sam-readonly-assessment','readOnly':True,'snapshot':snapshot,'snapshotSha256':digest(snapshot),'runtimeIdentity':identity,'statusCommandPresent':present,'compileFeature':feature,'reportedStatus':status,'statusSha256':digest(status),'modelManifest':model,'modelManifestSha256':digest(model),'modelFiles':facts,'modelIdentityVerified':verified,'blockers':blockers,'authorization':{'download':'NOT_GRANTED','execution':'NOT_GRANTED'},'downloadAllowed':False,'executionAllowed':False,'deliveryAllowed':False,'automaticReplay':False,'completeAcceptance':False,'scope':'user-supplied facts; no native receipt attestation or inference acceptance'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('snapshot',type=Path);parser.add_argument('--status',type=Path);parser.add_argument('--model-dir',type=Path);args=parser.parse_args()
    try:
        read=gateway().strict_json
        print(json.dumps(assess(read(args.snapshot.read_text()),read(args.status.read_text()) if args.status else None,args.model_dir),ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError,TypeError) as error:
        print(json.dumps({'error':str(error),'executionAllowed':False,'downloadAllowed':False,'automaticReplay':False},ensure_ascii=False));return 1
if __name__=='__main__':raise SystemExit(main())
