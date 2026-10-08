"""只读复核六目标归档与当前运行资源；不安装、不执行原生 CLI。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PureWindowsPath


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def require(condition,reason):
    if not condition:raise ValueError(reason)


def verify(source, evidence, run):
    def load(name):
        spec=importlib.util.spec_from_file_location(name,source/'runtime'/(name+'.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    gateway=load('command_gateway');images=load('artifacts');photos=load('photo_workflows')
    lock=read(source/'runtime/runtime.lock.json');resources=gateway.capture_resources(source/'runtime')
    require(run['status']=='completed' and run['conclusion']=='success','native_ci_not_success')
    require(len(run['jobs'])==6 and all(j['conclusion']=='success' for j in run['jobs']),'native_jobs_not_all_success')
    results=[]
    for target,expected in lock['artifacts'].items():
        root=evidence/('native-'+target);report=read(root/'native-evidence.json');windows=target.startswith('windows-')
        basename=lambda value:PureWindowsPath(value).name if windows else Path(value).name
        require(report['platform']==target and report['nativeStatus']=='PASS','native_target_not_pass')
        require(report['acceptanceDriverSha256']==sha(source/'scripts/native_acceptance.py'),'driver_identity_changed')
        require(report['runtimeLockSha256']==sha(source/'runtime/runtime.lock.json'),'lock_identity_changed')
        require(report['installation']['binarySha256']==expected['binarySha256'],'binary_identity_changed')
        require(len(report['photos'])==2 and len(report['artifacts'])==6 and len(report['inputs'])==2,'native_scope_incomplete')
        original_names=set()
        for path,digest in report['inputs'].items():
            name=basename(path);require(name not in original_names,'duplicate_original_alias');original_names.add(name)
            require(sha(root/'originals'/name)==digest,'original_digest_changed')
        require(original_names=={'gradient.png','gradient.jpg'},'original_scope_changed')
        artifacts=[]
        for item in report['artifacts']:
            path=root/'exports'/basename(item['path'])
            require(sha(path)==item['sha256'],'artifact_digest_changed')
            observed=images.verify(path,root/'exports',{'width':60,'format':item['format'],'bitDepth':8})
            require(observed['technicalStatus']=='PASS' and observed['height']==item['height'],'artifact_decode_failed')
            artifacts.append({'name':path.name,'sha256':sha(path),'decoder':observed['decoder']})
        receipts=[];run_ids=set()
        require(len(report['receipts'])==5,'receipt_scope_incomplete')
        for name in report['receipts']:
            path=root/name/'receipt.json';receipt=read(path);plan=read(root/(name+'-plan.json'))
            require(receipt['status']=='NATIVE_EXIT_ZERO_REVIEW_REQUIRED' and receipt['protocolComplete'] and receipt['exitCode']==0,'receipt_not_success')
            require(receipt['skillResourceSha256']==resources and receipt['skillResourceAfterSha256']==resources,'current_resource_mismatch')
            require(receipt['runtimeLockSha256']==report['runtimeLockSha256'],'receipt_lock_mismatch')
            require(receipt['runtimeIdentity']['binarySha256']==expected['binarySha256'] and receipt['runtimeIdentity']['version']==lock['resolvedVersion'],'receipt_binary_mismatch')
            require(receipt['inputSha256']==report['inputs'] and receipt['inputAfterSha256']==report['inputs'],'receipt_input_mismatch')
            require(receipt['planSha256']==hashlib.sha256(json.dumps(plan,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'plan_digest_mismatch')
            require(len(receipt['steps'])==len(plan['steps']) and all(row['index']==i and row['command']==plan['steps'][i]['command'] and row['status']=='SUCCEEDED' and row['native']['ok'] is True for i,row in enumerate(receipt['steps'])),'step_scope_mismatch')
            process=receipt['process'];require(process['status']=='EXITED' and process['exitCode']==0 and process['logComplete'],'process_not_complete')
            for channel in ('stdout','stderr'):
                require((root/name/'logs'/(channel+'.log')).read_bytes().decode('utf-8')==receipt[channel],'process_log_mismatch')
            require(receipt['runId'] not in run_ids,'session_reused');run_ids.add(receipt['runId'])
            receipts.append({'name':name,'sha256':sha(path),'stepCount':len(receipt['steps']),'planSha256':receipt['planSha256']})
        for photo in report['photos']:
            require(photo['settings']==photos.apply_local_changes(photo['baselineSettings'],{'light.exposure':.5},report['capabilities']['controls']),'unrelated_setting_changed')
            require(photo['libraryInfo']['persistent'] is True and photo['libraryInfo']['unsavedOps']==0,'persistence_not_confirmed')
        signature='NOT_AVAILABLE_IN_OFFICIAL_LINUX_RELEASE'
        if windows:
            require(report['processBits']==(32 if target=='windows-x86' else 64),'process_architecture_mismatch')
            facts=read(root/'windows-signature.json');signature=facts['status']
            require(signature=='Valid' and facts['binarySha256']==expected['binarySha256'],'windows_signature_invalid')
            dependencies=(root/'windows-dependencies.txt').read_text(encoding='utf-8-sig');require('kernel32.dll' in dependencies.lower(),'windows_dependencies_missing')
        else:
            platform=(root/'posix-platform.txt').read_text(encoding='utf-8');require(expected['binarySha256'] in platform,'posix_binary_identity_missing')
            dependencies=(root/'posix-dependencies.txt').read_text(encoding='utf-8');require(dependencies and 'not found' not in dependencies,'posix_dependencies_unresolved')
            if target.startswith('darwin-'):
                text=(root/'posix-signature.txt').read_text(encoding='utf-8');require('valid on disk' in text and 'TeamIdentifier=DJ6XS33FX8' in text,'macos_signature_unconfirmed');signature='codesign-strict-valid'
        results.append({'platform':target,'status':'PASS','hostMachine':report['hostMachine'],'processBits':report['processBits'],'reportSha256':sha(root/'native-evidence.json'),'binarySha256':expected['binarySha256'],'signature':signature,'receipts':receipts,'artifacts':artifacts})
    return {'status':'PASS','sourceCommit':run['headSha'],'runtimeResources':resources,'targets':results,'scope':'six fixed CLI native targets; plugin snapshot, desktop host, SAM and mobile acceptance remain separate'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--evidence',type=Path,required=True);parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(verify(args.source.resolve(),args.evidence.resolve(),read(args.run)),ensure_ascii=True,indent=2))
