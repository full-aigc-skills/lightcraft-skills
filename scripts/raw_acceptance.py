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


def contract():
    spec=importlib.util.spec_from_file_location('raw_contract',ROOT/'runtime/raw_contract.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def decode_mode(photo):
    """保持旧调用入口，类型判断由可独立安装的样本契约维护。"""
    return contract().decode_mode(photo)


class NativeEvidenceError(ValueError):
    """携带原生失败回执，不能把异常文本直接解释为不支持。"""
    def __init__(self,receipt):
        super().__init__('raw_execution_not_success: '+str(receipt.get('status')))
        self.receipt=receipt


def validate(manifest,runtime_home,workdir,scripts_dir=None):
    policy=contract();manifest=policy.validate_manifest(manifest)
    script_dir=Path(scripts_dir).resolve() if scripts_dir is not None else SCRIPTS
    def native_module(name):
        if scripts_dir is None:return load(name)
        spec=importlib.util.spec_from_file_location('raw_native_'+name,script_dir/(name+'.py'))
        value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
    resources=native_module('command_gateway').capture_resources(script_dir)
    runtime_home=Path(runtime_home).resolve()
    lock=json.loads((script_dir/'runtime.lock.json').read_text())
    installed=native_module('bootstrap').doctor(lock,runtime_home)
    if installed['status']!='READY':raise ValueError('verified_runtime_required_no_install')
    workdir=Path(workdir).resolve();workdir.mkdir(parents=True,exist_ok=False)
    outputs=[]
    for index,sample in enumerate(manifest['samples']):
        record=dict(sample,nativeAcceptance='STARTED',decodeMode='UNKNOWN',fullRawAcceptance='NOT_PROVEN',visual='NOT_RUN',cameraIdentity='NOT_OBSERVED',receipts={},plans={})
        source=Path(sample['path']).resolve()
        folder=workdir/str(index);folder.mkdir();library=folder/'library';exports=folder/'exports';exports.mkdir()
        def step(command,**params):return {'command':command,'params':params}
        def run(name,steps):
            plan=folder/(name+'-plan.json');plan.write_text(json.dumps({'domain':'lightcraft','steps':steps}))
            argv=[sys.executable,'-I','-B',str(script_dir/'commands.py'),'run',str(plan),'--runtime-home',str(runtime_home),'--require-installed','--library',str(library),'--input',str(source),'--output-root',str(exports),'--output',str(folder/name)]
            record['receipts'][name]=str(folder/name/'receipt.json');record['plans'][name]={'domain':'lightcraft','steps':steps}
            result=subprocess.run(argv,capture_output=True,text=True)
            gateway=native_module('command_gateway');read=gateway.read_receipt(folder/name/'receipt.json');receipt=read['receipt']
            if not read.get('compatible') or receipt.get('protocolComplete') is not True:raise ValueError('raw_execution_unconfirmed')
            plan_sha=hashlib.sha256(json.dumps({'domain':'lightcraft','steps':steps},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            expected_inputs={str(source):sample['sha256']}
            if (receipt.get('planSha256')!=plan_sha or receipt.get('libraryPath')!=str(library)
                    or receipt.get('skillResourceSha256')!=resources
                    or receipt.get('inputSha256')!=expected_inputs or receipt.get('inputAfterSha256')!=expected_inputs
                    or receipt.get('skillResourceAfterSha256')!=resources or receipt.get('runtimeLockSha256')!=resources.get('runtime.lock.json')):
                raise ValueError('raw_execution_identity_mismatch')
            if receipt.get('status')!='NATIVE_EXIT_ZERO_REVIEW_REQUIRED':raise NativeEvidenceError(receipt)
            if result.returncode:raise ValueError('raw_wrapper_exit_mismatch')
            process=receipt.get('process',{})
            if process.get('status')!='EXITED' or process.get('exitCode')!=0 or process.get('logComplete') is not True:raise ValueError('raw_process_unconfirmed')
            rows=receipt.get('steps',[])
            if len(rows)!=len(steps) or any(row.get('index')!=i or row.get('command')!=steps[i]['command'] or row.get('status')!='SUCCEEDED' for i,row in enumerate(rows)):
                raise ValueError('raw_step_evidence_incomplete')
            return receipt
        try:
            if native_module('artifacts').sha(source)!=sample['sha256']:raise ValueError('raw_sample_changed')
            imported=run('import',[step('library.import',paths=[str(source)],mode='add'),step('catalog.query',limit=10)])
            report=imported['steps'][0]['native']['result']
            if report.get('failed') or not report.get('imported'):raise ValueError('raw_not_imported')
            if len(report['imported'])!=1 or type(report['imported'][0]) is not int or report['imported'][0]<=0 or report.get('duplicates'):raise ValueError('raw_import_identity_ambiguous')
            photo_id=report['imported'][0]
            edited=run('edit-export',[step('library.select',ids=[photo_id],active=photo_id),step('develop.set',control='light.exposure',value=.25),step('develop.get',id=photo_id),step('app.export',path=str(exports/'raw-preview.png'),format='png',width=256),step('catalog.query',limit=10),step('photo.inspect',id=photo_id)])
            photos=edited['steps'][4]['native']['result']['photos']
            photo=next(p for p in photos if p['id']==photo_id)
            record['decodeMode']=decode_mode(photo)
            record['previewOnlyReason']=photo.get('previewOnly')
            record['observedCamera']=photo.get('camera')
            record['cameraIdentity']='MATCH' if policy.camera_matches(sample,photo.get('camera')) else 'MISMATCH'
            if record['cameraIdentity']!='MATCH':raise ValueError('raw_camera_identity_mismatch')
            settings=edited['steps'][2]['native']['result']
            reopened=run('reopen',[step('library.select',ids=[photo_id],active=photo_id),step('photo.inspect',id=photo_id),step('develop.get',id=photo_id),step('library.info')])
            if reopened.get('runId')==edited.get('runId') or reopened['steps'][2]['native']['result']!=settings:raise ValueError('raw_reopen_settings_mismatch')
            before=edited['steps'][5]['native']['result'];after=reopened['steps'][1]['native']['result']
            identity=before.get('source')
            if (before.get('id')!=photo_id or before.get('id')!=after.get('id') or not isinstance(identity,dict)
                    or identity!=after.get('source') or identity.get('type')!='file' or identity.get('path')!=str(source)):raise ValueError('raw_reopen_photo_mismatch')
            info=reopened['steps'][3]['native']['result']
            if not isinstance(info,dict) or info.get('persistent') is not True or info.get('unsavedOps')!=0:raise ValueError('raw_reopen_persistence_unconfirmed')
            record['artifact']=native_module('artifacts').verify(exports/'raw-preview.png',exports,{'format':'png','width':256})
            if record['artifact']['technicalStatus']!='PASS':raise ValueError('raw_export_mismatch')
            if native_module('artifacts').sha(source)!=sample['sha256']:raise ValueError('raw_original_changed')
            status={'FULL_RAW_REPORTED':'PASS','PREVIEW_FALLBACK':'PASS_WITH_PREVIEW_FALLBACK','UNKNOWN':'UNCONFIRMED'}[record['decodeMode']]
            record.update(nativeAcceptance=status,fullRawAcceptance='REPORTED_BY_RUNTIME' if record['decodeMode']=='FULL_RAW_REPORTED' else 'NOT_PROVEN',photoId=photo_id,observedCamera=photo.get('camera'),receipts={name:str(folder/name/'receipt.json') for name in ('import','edit-export','reopen')})
        except NativeEvidenceError as error:
            reason=policy.unsupported_reason(error.receipt,str(source))
            record.update(nativeAcceptance='UNSUPPORTED' if reason is not None else 'UNCONFIRMED',error=reason or str(error))
        except (ValueError,OSError,KeyError,TypeError,StopIteration,subprocess.SubprocessError) as error:
            record.update(nativeAcceptance='FAILED',error=str(error))
        outputs.append(record)
    evidence={'schemaVersion':1,'reportKind':'raw-samples','manifest':manifest,'manifestSha256':policy.digest(manifest),'runtimeIdentity':installed,
              'executionScriptsRoot':str(script_dir),'executionResourceSha256':resources,'policySha256':hashlib.sha256((ROOT/'runtime/raw_contract.py').read_bytes()).hexdigest(),
              'samples':outputs,'scope':'仅记录所测相机和变体，不代表全部 RAW','visual':'NOT_RUN','automaticReplay':False,'completeAcceptance':False}
    (workdir/'raw-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    return evidence


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--runtime-home',type=Path,required=True);parser.add_argument('--workdir',type=Path,required=True);parser.add_argument('--allow-native',action='store_true');parser.add_argument('--scripts-dir',type=Path,help='显式配套执行资源，默认当前技能源；报告绑定实际资源摘要')
    args=parser.parse_args()
    if not args.allow_native:parser.error('explicit_native_validation_required')
    try:result=validate(contract().gateway().strict_json(args.manifest.read_text()),args.runtime_home,args.workdir,args.scripts_dir)
    except (ValueError,OSError,TypeError,KeyError) as error:print(json.dumps({'error':str(error),'nativeAcceptance':'NOT_STARTED','automaticReplay':False}));raise SystemExit(1)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['samples'] and all(r['nativeAcceptance'] in ('PASS','PASS_WITH_PREVIEW_FALLBACK') for r in result['samples']) else 1)
