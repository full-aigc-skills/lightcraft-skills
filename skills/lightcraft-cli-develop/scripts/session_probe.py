"""固定原生 MCP 的封闭只读探测；不安装、不重连、不重放修改。"""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import uuid


def load(name):
    path=Path(__file__).with_name(name+'.py')
    spec=importlib.util.spec_from_file_location('probe_'+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def probe(output,runtime_home=None,connect=None,library=None,timeout=30):
    """启动一次原生 MCP；协议可用与远端库查询分别登记。"""
    gateway=load('command_gateway');mode=load('mode_contract');scripts=Path(__file__).parent
    if connect is not None and library is not None:raise ValueError('mode_conflict_connect_headless')
    output=Path(output)
    if output.exists() or output.is_symlink():raise ValueError('probe_requires_new_output')
    if not 0<timeout<=86400:raise ValueError('invalid_timeout')
    requests=mode.probe_requests();native=['mcp','--compact']
    if connect is not None:native+=['--connect',connect]
    elif library is not None:native+=['--library',str(library)]
    identity=mode.inspect_mode(native,requests)
    output.mkdir(parents=True)
    data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in requests).encode()
    request_path=output/'requests.jsonl';request_path.write_bytes(data)
    sha=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    steps=[{'command':'mcp:'+r['method'],'params':r['params']} for r in requests if 'id' in r]
    resources=gateway.capture_resources(scripts)
    receipt={'schemaVersion':1,'receiptKind':'mcp-readonly-probe','domain':'lightcraft','runId':str(uuid.uuid4()),
             'status':'STARTED','startedAt':datetime.now(timezone.utc).isoformat(),'planSha256':sha({'domain':'lightcraft','steps':steps}),
             'requests':requests,'requestsSha256':hashlib.sha256(data).hexdigest(),'requestsPath':str(request_path.resolve()),
             'runtimeLockSha256':resources['runtime.lock.json'],'skillResourceSha256':resources,'inputSha256':{},
             'steps':[],'automaticReplay':False,'completeAcceptance':False,'readOnly':True,
             'backendQuery':'NOT_RUN','backendSessionIdentity':'NOT_PROVIDED_BY_NATIVE_PROTOCOL',
             'requestedMode':identity,'libraryPath':str(Path(library).resolve()) if library is not None else None}
    target=output/'receipt.json';gateway.write_receipt(target,receipt)
    argv=[sys.executable,'-I','-B',str(scripts/'cli.py'),'--require-installed','--supervised','--logs-dir',str(output/'logs'),
          '--timeout',str(timeout),'--requests',str(request_path)]
    if runtime_home is not None:argv+=['--runtime-home',str(runtime_home)]
    argv+=['--',*native];receipt['argv']=argv
    try:
        result=subprocess.run(argv,capture_output=True,text=True, encoding='utf-8')
        envelope=gateway.strict_json(result.stdout)
        if not isinstance(envelope,dict):raise ValueError('invalid_supervised_reply')
        receipt.update(process=envelope,runtimeIdentity=envelope.get('runtimeIdentity'))
        if envelope.get('status')=='NOT_STARTED' and envelope.get('nativeProcessStarted') is False:
            receipt.update(status='FAILED_OR_PARTIAL',protocolComplete=True,protocolErrors=[],
                           steps=[{'index':i,'command':s['command'],'status':'NOT_EXECUTED'} for i,s in enumerate(steps)])
        else:
            replies=[gateway.strict_json(line) for line in gateway.bounded_lines(output/'logs/stdout.log') if line.strip()]
            classified=mode.classify_probe(requests,replies,json.loads((scripts/'runtime.lock.json').read_text(encoding='utf-8'))['resolvedVersion'])
            receipt.update(classified)
            if (envelope.get('status')!='EXITED' or envelope.get('exitCode')!=0 or envelope.get('logComplete') is not True
                    or envelope.get('stdinSha256')!=receipt['requestsSha256'] or envelope.get('runtimeIdentity',{}).get('mode')!=identity['mode']):
                receipt.update(status='UNKNOWN',backendQuery='NOT_CONFIRMED',protocolComplete=False)
        if gateway.capture_resources(scripts)!=resources or request_path.read_bytes()!=data:
            receipt.update(status='UNKNOWN',backendQuery='NOT_CONFIRMED',protocolComplete=False,error='probe_resources_or_requests_changed')
    except (ValueError,OSError,TypeError,subprocess.SubprocessError,KeyboardInterrupt) as error:
        receipt.update(status='UNKNOWN',backendQuery='NOT_CONFIRMED',error=str(error),protocolComplete=False)
    receipt['endedAt']=datetime.now(timezone.utc).isoformat();gateway.write_receipt(target,receipt)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--runtime-home',type=Path)
    group=parser.add_mutually_exclusive_group();group.add_argument('--connect');group.add_argument('--library',type=Path)
    parser.add_argument('--timeout',type=float,default=30)
    args=parser.parse_args()
    try:
        result=probe(args.output,args.runtime_home,args.connect,args.library,args.timeout)
        print(json.dumps(result,ensure_ascii=True,indent=2));return 0 if result['status']=='NATIVE_EXIT_ZERO_REVIEW_REQUIRED' else 1
    except (ValueError,OSError,TypeError) as error:
        print(json.dumps({'error':str(error),'automaticReplay':False}));return 1


if __name__=='__main__':raise SystemExit(main())
