"""真实 RAW 样本验收；仅消费已验证安装，不自动下载或安装。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/lightcraft-use/scripts'


def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def decode_mode(photo):
    """当前 catalog.query 的 previewOnly 是原因字符串或 null；缺字段不推断。"""
    if not isinstance(photo,dict) or photo.get('kind')!='raw' or 'previewOnly' not in photo:return 'UNKNOWN'
    value=photo['previewOnly']
    if isinstance(value,str) and value.strip():return 'PREVIEW_FALLBACK'
    if value is None:return 'FULL_RAW_REPORTED'
    return 'UNKNOWN'


def validate(manifest,runtime_home,workdir):
    runtime_home=Path(runtime_home).resolve()
    lock=json.loads((SCRIPTS/'runtime.lock.json').read_text())
    installed=load('bootstrap').doctor(lock,runtime_home)
    if installed['status']!='READY':raise ValueError('verified_runtime_required_no_install')
    workdir=Path(workdir).resolve();workdir.mkdir(parents=True,exist_ok=False)
    outputs=[]
    for index,sample in enumerate(manifest['samples']):
        record=dict(sample,nativeAcceptance='STARTED',decodeMode='UNKNOWN',visual='NOT_RUN')
        source=Path(sample['path']).resolve()
        folder=workdir/str(index);folder.mkdir();library=folder/'library';exports=folder/'exports';exports.mkdir()
        def step(command,**params):return {'command':command,'params':params}
        def run(name,steps):
            plan=folder/(name+'-plan.json');plan.write_text(json.dumps({'domain':'lightcraft','steps':steps}))
            argv=[sys.executable,'-I','-B',str(SCRIPTS/'commands.py'),'run',str(plan),'--runtime-home',str(runtime_home),'--require-installed','--library',str(library),'--input',str(source),'--output-root',str(exports),'--output',str(folder/name)]
            result=subprocess.run(argv,capture_output=True,text=True)
            if result.returncode:raise ValueError('raw_native_failed: '+result.stdout[-2000:]+result.stderr[-1000:])
            gateway=load('command_gateway');read=gateway.read_receipt(folder/name/'receipt.json');receipt=read['receipt']
            if not read.get('compatible') or receipt.get('status')!='NATIVE_EXIT_ZERO_REVIEW_REQUIRED' or receipt.get('protocolComplete') is not True:
                raise ValueError('raw_execution_unconfirmed')
            plan_sha=hashlib.sha256(json.dumps({'domain':'lightcraft','steps':steps},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            expected_inputs=gateway.capture_inputs([source])
            if (receipt.get('planSha256')!=plan_sha or receipt.get('libraryPath')!=str(library)
                    or receipt.get('skillResourceSha256')!=gateway.capture_resources(SCRIPTS)
                    or receipt.get('inputSha256')!=expected_inputs or receipt.get('inputAfterSha256')!=expected_inputs):
                raise ValueError('raw_execution_identity_mismatch')
            rows=receipt.get('steps',[])
            if len(rows)!=len(steps) or any(row.get('index')!=i or row.get('command')!=steps[i]['command'] or row.get('status')!='SUCCEEDED' for i,row in enumerate(rows)):
                raise ValueError('raw_step_evidence_incomplete')
            return receipt
        try:
            if load('artifacts').sha(source)!=sample['sha256']:raise ValueError('raw_sample_changed')
            imported=run('import',[step('library.import',paths=[str(source)],mode='add'),step('catalog.query',limit=10)])
            report=imported['steps'][0]['native']['result']
            if report.get('failed') or not report.get('imported'):raise ValueError('raw_not_imported')
            photo_id=report['imported'][0]
            edited=run('edit-export',[step('library.select',ids=[photo_id],active=photo_id),step('develop.set',control='light.exposure',value=.25),step('develop.get',id=photo_id),step('app.export',path=str(exports/'raw-preview.png'),format='png',width=256),step('catalog.query',limit=10),step('photo.inspect',id=photo_id)])
            photos=edited['steps'][4]['native']['result']['photos']
            photo=next(p for p in photos if p['id']==photo_id)
            record['decodeMode']=decode_mode(photo)
            record['previewOnlyReason']=photo.get('previewOnly')
            settings=edited['steps'][2]['native']['result']
            reopened=run('reopen',[step('library.select',ids=[photo_id],active=photo_id),step('photo.inspect',id=photo_id),step('develop.get',id=photo_id),step('library.info')])
            if reopened.get('runId')==edited.get('runId') or reopened['steps'][2]['native']['result']!=settings:raise ValueError('raw_reopen_settings_mismatch')
            before=edited['steps'][5]['native']['result'];after=reopened['steps'][1]['native']['result']
            identity=before.get('source')
            if (before.get('id')!=photo_id or before.get('id')!=after.get('id') or not isinstance(identity,dict)
                    or identity!=after.get('source') or identity.get('type')!='file' or identity.get('path')!=str(source)):raise ValueError('raw_reopen_photo_mismatch')
            info=reopened['steps'][3]['native']['result']
            if not isinstance(info,dict) or info.get('persistent') is not True or info.get('unsavedOps')!=0:raise ValueError('raw_reopen_persistence_unconfirmed')
            record['artifact']=load('artifacts').verify(exports/'raw-preview.png',exports,{'format':'png','width':256})
            if record['artifact']['technicalStatus']!='PASS':raise ValueError('raw_export_mismatch')
            if load('artifacts').sha(source)!=sample['sha256']:raise ValueError('raw_original_changed')
            status={'FULL_RAW_REPORTED':'PASS','PREVIEW_FALLBACK':'PASS_WITH_PREVIEW_FALLBACK','UNKNOWN':'UNCONFIRMED'}[record['decodeMode']]
            record.update(nativeAcceptance=status,fullRawAcceptance='REPORTED_BY_RUNTIME' if record['decodeMode']=='FULL_RAW_REPORTED' else 'NOT_PROVEN',photoId=photo_id,observedCamera=photo.get('camera'),receipts={name:str(folder/name/'receipt.json') for name in ('import','edit-export','reopen')})
        except (ValueError,OSError,KeyError,TypeError,StopIteration,subprocess.SubprocessError) as error:
            record.update(nativeAcceptance='FAIL_OR_UNSUPPORTED',error=str(error))
        outputs.append(record)
    evidence={'schemaVersion':1,'runtimeIdentity':installed,'samples':outputs,'scope':'仅记录所测相机和变体，不代表全部 RAW','visual':'NOT_RUN'}
    (workdir/'raw-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    return evidence


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--runtime-home',type=Path,required=True);parser.add_argument('--workdir',type=Path,required=True);parser.add_argument('--allow-native',action='store_true')
    args=parser.parse_args()
    if not args.allow_native:parser.error('explicit_native_validation_required')
    result=validate(json.loads(args.manifest.read_text()),args.runtime_home,args.workdir)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['samples'] and all(r['nativeAcceptance'] in ('PASS','PASS_WITH_PREVIEW_FALLBACK') for r in result['samples']) else 1)
