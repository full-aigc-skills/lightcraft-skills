"""三领域原生命令查询与单会话计划入口；标准库实现，不解析 shell。"""
import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone

DOMAINS=('lightcraft','printcraft','designcraft')


def strict_json(text):
    """拒绝重复字段及非 JSON 的 NaN/Infinity，避免计划歧义。"""
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('duplicate_json_field: '+k)
            result[k]=v
        return result
    def invalid(value):raise ValueError('nonfinite_json_number: '+value)
    def number(value):
        parsed=float(value)
        if not math.isfinite(parsed):invalid(value)
        return parsed
    return json.loads(text,object_pairs_hook=pairs,parse_constant=invalid,parse_float=number)


def normalize(domain,raw):
    """保留完整原生目录；文本参数说明不升级为 JSON Schema。"""
    if domain not in DOMAINS or not isinstance(raw,list) or not raw:raise ValueError('invalid_native_catalog')
    rows=[];seen=set()
    for item in raw:
        if not isinstance(item,dict):raise ValueError('invalid_native_catalog_entry')
        identifier=item.get('name' if domain=='printcraft' else 'id')
        if not isinstance(identifier,str) or not identifier:raise ValueError('invalid_command_id')
        if identifier in seen:raise ValueError('duplicate_command: '+identifier)
        seen.add(identifier)
        menu=item.get('menu',[])
        if not isinstance(menu,list) or any(not isinstance(x,str) for x in menu):raise ValueError('invalid_menu')
        schema=item.get('input_schema') if domain=='printcraft' else None
        if domain=='printcraft' and not isinstance(schema,dict):raise ValueError('missing_native_input_schema')
        rows.append({'id':identifier,'title':item.get('label',identifier),'description':item.get('description',''),
                     'category':(menu[0] if menu else identifier.split('.')[0].split('_')[0]),
                     'parameterGuidance':item.get('params',''),'inputSchema':schema,
                     'parameterValidation':'schema-subset' if schema is not None else 'native-only',
                     'observedEnabled':item.get('enabled'),'native':item})
    return rows


def validate_schema_definition(schema,depth=0):
    """先遍历完整定义；未选分支或未提供属性不能隐藏未知约束。"""
    if depth>48:raise ValueError('schema_depth_exceeded')
    if isinstance(schema,bool):return
    if not isinstance(schema,dict):raise ValueError('invalid_native_schema')
    allowed={'$schema','title','description','default','examples','type','properties','required','additionalProperties','items','minimum','maximum','exclusiveMinimum','exclusiveMaximum','minItems','maxItems','minLength','maxLength','enum','const','pattern','anyOf','oneOf','allOf'}
    if set(schema)-allowed:raise ValueError('unsupported_schema_constraint: '+','.join(sorted(set(schema)-allowed)))
    if 'type' in schema:
        types=schema['type'];types=[types] if isinstance(types,str) else types
        supported={'object','array','string','boolean','integer','number','null'}
        if not isinstance(types,list) or not types or any(not isinstance(t,str) or t not in supported for t in types):raise ValueError('unsupported_schema_type')
        if len(set(types))!=len(types):raise ValueError('invalid_native_schema')
    if 'properties' in schema:
        if not isinstance(schema['properties'],dict):raise ValueError('invalid_native_schema')
        for child in schema['properties'].values():validate_schema_definition(child,depth+1)
    if 'required' in schema:
        required=schema['required']
        if not isinstance(required,list) or any(not isinstance(k,str) for k in required) or len(set(required))!=len(required):raise ValueError('invalid_native_schema')
    for key in ('items','additionalProperties'):
        if key in schema:validate_schema_definition(schema[key],depth+1)
    for key in ('anyOf','oneOf','allOf'):
        if key in schema:
            if not isinstance(schema[key],list) or not schema[key]:raise ValueError('invalid_native_schema')
            for child in schema[key]:validate_schema_definition(child,depth+1)
    for key in ('minimum','maximum','exclusiveMinimum','exclusiveMaximum'):
        if key in schema and (type(schema[key]) not in (int,float) or (isinstance(schema[key],float) and not math.isfinite(schema[key]))):raise ValueError('invalid_native_schema')
    for key in ('minItems','maxItems','minLength','maxLength'):
        if key in schema and (type(schema[key]) is not int or schema[key]<0):raise ValueError('invalid_native_schema')
    if 'enum' in schema and (not isinstance(schema['enum'],list) or not schema['enum']):raise ValueError('invalid_native_schema')
    if 'pattern' in schema:
        if not isinstance(schema['pattern'],str):raise ValueError('invalid_native_schema')
        try:re.compile(schema['pattern'])
        except re.error as error:raise ValueError('invalid_native_schema: pattern') from error


def json_equal(left,right,depth=0):
    """JSON数字按值比较，布尔值保持独立，容器递归遵守同一规则。"""
    if depth>48:raise ValueError('schema_depth_exceeded')
    if type(left) in (int,float) and type(right) in (int,float):return left==right
    if type(left) is not type(right):return False
    if isinstance(left,dict):return left.keys()==right.keys() and all(json_equal(v,right[k],depth+1) for k,v in left.items())
    if isinstance(left,list):return len(left)==len(right) and all(json_equal(a,b,depth+1) for a,b in zip(left,right))
    return left==right


def validate_schema(schema,value,path='$',depth=0):
    """校验原生 schema 的明确支持子集；未知约束拒绝，不宣称通用 JSON Schema。"""
    if depth>48:raise ValueError('schema_depth_exceeded')
    if depth==0:validate_schema_definition(schema)
    if schema is True:return
    if schema is False:raise ValueError('parameter_schema_false: '+path)
    if not isinstance(schema,dict):raise ValueError('unsupported_native_schema')
    allowed={'$schema','title','description','default','examples','type','properties','required','additionalProperties','items','minimum','maximum','exclusiveMinimum','exclusiveMaximum','minItems','maxItems','minLength','maxLength','enum','const','pattern','anyOf','oneOf','allOf'}
    unknown=set(schema)-allowed
    if unknown:raise ValueError('unsupported_schema_constraint: '+','.join(sorted(unknown)))
    for key in ('anyOf','oneOf','allOf'):
        if key in schema:
            branches=schema[key]
            if not isinstance(branches,list) or not branches:raise ValueError('invalid_native_schema')
            matches=0
            for branch in branches:
                try:validate_schema(branch,value,path,depth+1);matches+=1
                except ValueError:pass
            if (key=='anyOf' and not matches) or (key=='oneOf' and matches!=1) or (key=='allOf' and matches!=len(branches)):
                raise ValueError('schema_branch_mismatch: '+path)
    types={'object':lambda v:isinstance(v,dict),'array':lambda v:isinstance(v,list),'string':lambda v:isinstance(v,str),'boolean':lambda v:isinstance(v,bool),'integer':lambda v:isinstance(v,int) and not isinstance(v,bool),'number':lambda v:isinstance(v,(int,float)) and not isinstance(v,bool) and (not isinstance(v,float) or math.isfinite(v)),'null':lambda v:v is None}
    wanted=schema.get('type');wanted=[wanted] if isinstance(wanted,str) else wanted
    if wanted is not None:
        if not isinstance(wanted,list) or any(t not in types for t in wanted):raise ValueError('unsupported_schema_type')
        if not any(types[t](value) for t in wanted):raise ValueError('parameter_type_mismatch: '+path)
    same=json_equal
    if 'enum' in schema and not any(same(value,x) for x in schema['enum']):raise ValueError('parameter_enum_mismatch: '+path)
    if 'const' in schema and not same(value,schema['const']):raise ValueError('parameter_const_mismatch: '+path)
    if isinstance(value,dict):
        props=schema.get('properties',{});required=schema.get('required',[])
        if not isinstance(props,dict) or not isinstance(required,list):raise ValueError('invalid_native_schema')
        if any(k not in value for k in required):raise ValueError('required_parameter_missing: '+path)
        for key,item in value.items():
            if key in props:validate_schema(props[key],item,path+'.'+key,depth+1)
            elif schema.get('additionalProperties') is False:raise ValueError('unknown_parameter: '+path+'.'+key)
            elif isinstance(schema.get('additionalProperties'),dict):validate_schema(schema['additionalProperties'],item,path+'.'+key,depth+1)
    elif isinstance(value,list):
        if len(value)<schema.get('minItems',0) or len(value)>schema.get('maxItems',1000000):raise ValueError('parameter_array_length: '+path)
        if 'items' in schema:
            for index,item in enumerate(value):validate_schema(schema['items'],item,f'{path}[{index}]',depth+1)
    elif isinstance(value,str):
        if len(value)<schema.get('minLength',0) or len(value)>schema.get('maxLength',1000000):raise ValueError('parameter_string_length: '+path)
        if 'pattern' in schema and not re.search(schema['pattern'],value):raise ValueError('parameter_pattern_mismatch: '+path)
    elif isinstance(value,(int,float)) and not isinstance(value,bool):
        if isinstance(value,float) and not math.isfinite(value):raise ValueError('nonfinite_json_number')
        for key,op in (('minimum',lambda a,b:a<b),('maximum',lambda a,b:a>b),('exclusiveMinimum',lambda a,b:a<=b),('exclusiveMaximum',lambda a,b:a>=b)):
            if key in schema and op(value,schema[key]):raise ValueError('parameter_number_range: '+path)


def validate_shape(domain,plan):
    """只接受本领域、已发现命令与对象参数；状态前置条件由真实会话判断。"""
    if not isinstance(plan,dict) or set(plan)-{'domain','steps'} or plan.get('domain')!=domain:raise ValueError('plan_domain_or_fields_invalid')
    steps=plan.get('steps')
    if not isinstance(steps,list) or not 1<=len(steps)<=1000:raise ValueError('plan_steps_invalid')
    for step in steps:
        if not isinstance(step,dict) or set(step)!={'command','params'} or not isinstance(step['command'],str) or not isinstance(step['params'],dict):raise ValueError('plan_step_invalid')
    return steps


def check_plan(domain,rows,plan):
    """校验目录中的实际命令和可用 schema；原生会话前置条件保持待执行。"""
    steps=validate_shape(domain,plan)
    index={r['id']:r for r in rows};native_only=False
    for step in steps:
        if not isinstance(step,dict) or set(step)!={'command','params'} or not isinstance(step['command'],str) or not isinstance(step['params'],dict):raise ValueError('plan_step_invalid')
        row=index.get(step['command'])
        if row is None:raise ValueError('unknown_command: '+step['command'])
        if row['inputSchema'] is not None:validate_schema(row['inputSchema'],step['params'])
        else:native_only=True
    return {'structuralCheck':'PASS','steps':len(steps),'nativeParameterValidation':'NOT_RUN','schemaSubsetCheck':'NOT_AVAILABLE' if native_only else 'PASS','execution':'NOT_RUN'}


def native_script(domain,steps):
    """整个计划只启动一个原生会话，保留文档 ID 与跨步骤状态。"""
    if domain=='printcraft':return [{'tool':s['command'],'args':s['params']} for s in steps]
    return steps


def file_sha(path):
    """以流方式计算输入摘要；不执行文件内容。"""
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def capture_inputs(paths):
    """登记调用者显式输入及目录内普通文件，拒绝链接与缺失输入。"""
    result={}
    for raw in paths:
        root=Path(raw).expanduser().absolute()
        if root.is_symlink() or not root.exists():raise ValueError('input_missing_or_symlink: '+str(root))
        entries=sorted(root.rglob('*')) if root.is_dir() else [root]
        if len(entries)>100000:raise ValueError('input_manifest_too_large')
        for path in entries:
            if path.is_symlink():raise ValueError('input_symlink: '+str(path))
            if path.is_dir():continue
            if not path.is_file():raise ValueError('input_not_regular_file: '+str(path))
            result[str(path)]=file_sha(path)
    return result


def capture_resources(script_dir):
    """把当前技能执行资源绑定到回执，不能借用兄弟技能的身份。"""
    names=tuple(sorted(p.name for p in script_dir.iterdir() if p.suffix in ('.py','.json')))
    result={}
    for name in names:
        path=script_dir/name
        if path.is_symlink() or not path.is_file():raise ValueError('skill_resource_missing_or_symlink: '+name)
        result[name]=file_sha(path)
    return result


def write_receipt(path,receipt):
    """同目录暂存、刷盘并原子替换；中断不留下半个JSON回执。"""
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix='.receipt-',delete=False) as stream:
            temporary=Path(stream.name)
            stream.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
            stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path)
    finally:
        if temporary is not None and temporary.exists():temporary.unlink()


def output_text(value):
    """保留超时返回的部分日志，兼容subprocess的bytes和str。"""
    return value.decode('utf-8',errors='replace') if isinstance(value,bytes) else value or ''


def parse_results(steps, lines, exit_code, unknown=False):
    """顺序匹配实际 JSONL；失败后的停止仅在完整可信协议时可确定。"""
    results=[];errors=[];failed=False;not_saved=False;partial=False;total_bytes=0
    for line in lines:
        total_bytes+=len(line.encode('utf-8'))
        if total_bytes>16*1024*1024:
            errors.append('result_budget_exceeded_full_log_retained');unknown=True;break
        if not line.strip():continue
        try:
            if len(line)>4*1024*1024:raise ValueError('result_line_too_large')
            row=strict_json(line);index=len(results)
            if (not isinstance(row,dict) or index>=len(steps) or row.get('command')!=steps[index]['command']
                    or type(row.get('ok')) is not bool or failed):raise ValueError('result_sequence_mismatch')
            applied=not row['ok'] and ('saved in memory but not written to disk' in str(row.get('error','')) or 'NotSaved' in str(row.get('error','')))
            partial_import=row['ok'] and row['command']=='library.import' and isinstance(row.get('result'),dict) and bool(row['result'].get('failed'))
            partial=partial or partial_import
            status='PARTIAL' if partial_import else 'SUCCEEDED' if row['ok'] else 'APPLIED_NOT_SAVED' if applied else 'FAILED'
            failed=not row['ok'];not_saved=not_saved or applied
            results.append({'index':index,'command':row['command'],'status':status,'native':row})
        except (ValueError,TypeError) as error:
            errors.append(str(error));unknown=True
    if len(results)!=len(steps) and not (failed and exit_code not in (0,None)):unknown=True
    if failed and exit_code==0:unknown=True
    for index in range(len(results),len(steps)):
        results.append({'index':index,'command':steps[index]['command'],'status':'NOT_EXECUTED' if failed and not unknown else 'UNKNOWN'})
    status=('UNKNOWN' if unknown else 'PERSISTENCE_UNCONFIRMED' if not_saved else 'FAILED_OR_PARTIAL' if failed or partial or exit_code!=0 else 'NATIVE_EXIT_ZERO_REVIEW_REQUIRED')
    return {'status':status,'steps':results,'protocolErrors':errors,'protocolComplete':not unknown}


def preflight_writes(plan, originals, output_root=None):
    """检查已知写入路径及原片别名；无法推断的副作用不伪装成沙箱。"""
    targets=[]
    for step in plan['steps']:
        command=step['command'];params=step['params']
        if command=='library.import' and params.get('mode','add')=='move':
            for raw in params.get('paths',[]):
                source=Path(raw).expanduser().resolve()
                if any(source==Path(p).resolve() or source in Path(p).resolve().parents for p in originals):raise ValueError('move_conflicts_with_preserved_original')
        if command in ('app.export','export.checkTarget','preset.export','curve.exportPresets','photo.editExternal'):
            for key in ('path','dir'):
                if not params.get(key):continue
                target=Path(params[key]).expanduser().absolute()
                if target.is_symlink():raise ValueError('write_target_symlink_or_alias')
                target=target.resolve()
                if output_root and not target.is_relative_to(Path(output_root).resolve()):raise ValueError('write_outside_output_root')
                for original in originals:
                    source=Path(original)
                    if target==source.resolve() or (target.exists() and source.exists() and target.samefile(source)):raise ValueError('write_conflicts_with_preserved_original')
                if target.exists() and (key=='path' or not target.is_dir() or any(target.iterdir())):raise ValueError('output_conflict_requires_new_target')
                targets.append(str(target))
        if command=='app.export':
            fmt=params.get('format','').lower();depth=params.get('bitDepth')
            if depth and fmt in ('jpg','jpeg') and depth!=8:raise ValueError('format_bit_depth_incompatible')
    return targets


def read_receipt(path):
    """旧记录只读；未知版本不转换为可继续执行的状态。"""
    receipt=strict_json(Path(path).read_text())
    if not isinstance(receipt,dict):raise ValueError('receipt_invalid')
    compatible=receipt.get('schemaVersion')==1
    if compatible:
        schema=strict_json(Path(__file__).with_name('execution-receipt.schema.json').read_text())
        validate_schema(schema,receipt)
    return {'readOnly':True,'compatible':compatible,'receipt':receipt,'automaticReplay':False}


def bounded_lines(path):
    """逐行有界读取，超长行令协议失败，避免 stdout 全量进入内存。"""
    with Path(path).open(encoding='utf-8',errors='replace') as stream:
        while line:=stream.readline(4*1024*1024+1):
            yield line
            if len(line)>4*1024*1024:break


def main(domain,script_dir):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('list','describe','check','run','inspect','discover','doctor'))
    parser.add_argument('argument',nargs='?')
    parser.add_argument('--catalog',type=Path,help='显式离线原生JSON目录；不能用于执行')
    parser.add_argument('--runtime-home',type=Path)
    parser.add_argument('--archive',type=Path)
    parser.add_argument('--require-installed',action='store_true',help='只消费已有且校验通过的安装，缺失时不安装')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--library',type=Path)
    parser.add_argument('--import',dest='imports',type=Path,action='append',default=[])
    parser.add_argument('--root',type=Path)
    parser.add_argument('--input',dest='inputs',type=Path,action='append',default=[],help='显式登记需保全的输入；可重复，不改变原生参数')
    parser.add_argument('--output-root',type=Path,help='已知写入目标的允许根目录，不是沙箱')
    parser.add_argument('--timeout',type=float,default=600)
    parser.add_argument('--stop-file',type=Path)
    args=parser.parse_args()
    try:
        if args.action=='inspect':
            print(json.dumps(read_receipt(args.argument),ensure_ascii=False));return 0
        if args.action=='doctor':
            prefix=[sys.executable,'-I','-B',str(script_dir/'bootstrap.py'),'--no-install']
            if args.runtime_home:prefix+=['--runtime-home',str(args.runtime_home)]
            return subprocess.run(prefix).returncode
        plan=None
        # 在安装前检查计划的 JSON、领域与结构；实际目录存在后再检查命令。
        if args.action in ('check','run'):
            if args.argument is None:raise ValueError('plan_required')
            plan=strict_json(Path(args.argument).read_text())
            validate_shape(domain,plan)
        if args.action=='run' and (args.catalog is not None or args.output is None or args.output.exists()):raise ValueError('run_requires_live_catalog_and_new_output')
        if args.action=='describe' and args.argument is None:raise ValueError('command_id_required')
        if domain!='designcraft' and args.source:raise ValueError('source_only_for_designcraft')
        if domain!='lightcraft' and (args.library or args.imports):raise ValueError('library_only_for_lightcraft')
        if domain!='printcraft' and args.root:raise ValueError('root_only_for_printcraft')
        prefix=[sys.executable,'-I','-B',str(script_dir/'cli.py')]
        if args.runtime_home:prefix+=['--runtime-home',str(args.runtime_home)]
        if args.archive:prefix+=['--archive',str(args.archive)]
        if args.require_installed:prefix+=['--require-installed']
        input_paths=args.inputs+([args.source] if args.source else [])+args.imports
        input_sha=capture_inputs(input_paths) if args.action=='run' else {}
        resources=capture_resources(script_dir) if args.action=='run' else {}
        if args.action=='run':preflight_writes(plan,input_sha,args.output_root)
        if args.catalog:raw=strict_json(args.catalog.read_text())
        else:
            discovery=['tools'] if domain=='printcraft' else ['commands']+(['--json'] if domain=='lightcraft' else [])
            observed=subprocess.run(prefix+['--',*discovery],capture_output=True,text=True,timeout=900)
            if observed.returncode:raise ValueError('native_catalog_failed: '+observed.stdout.strip()+observed.stderr.strip())
            raw=strict_json(observed.stdout)
        rows=normalize(domain,raw)
        if args.action in ('list','discover'):
            reply={'domain':domain,'count':len(rows),'commands':rows,'catalogSource':'offline-explicit' if args.catalog else 'live-native'}
            if args.action=='discover':
                reply.update(schemaVersion=1,mode='offline',executableIdentity=None,executionAllowed=False,controls=None)
                if not args.catalog:
                    controls=subprocess.run(prefix+['--','controls','--json'],capture_output=True,text=True,timeout=900)
                    if controls.returncode:raise ValueError('native_controls_failed')
                    import importlib.util
                    spec=importlib.util.spec_from_file_location('bootstrap',script_dir/'bootstrap.py')
                    bootstrap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bootstrap)
                    runtime_home=args.runtime_home or os.environ.get('CRAFT_RUNTIME_HOME',str(Path.home()/'.local/share/craft-runtimes'))
                    identity=bootstrap.doctor(strict_json((script_dir/'runtime.lock.json').read_text()),runtime_home)
                    if identity['status']!='READY':raise ValueError('discovery_runtime_identity_unconfirmed')
                    reply.update(mode='Headless',executableIdentity=identity,executionAllowed=True,controls=strict_json(controls.stdout))
                reply['catalogSha256']=hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()
                reply['controlsSha256']=hashlib.sha256(json.dumps(reply['controls'],sort_keys=True).encode()).hexdigest()
                reply['observedAt']=datetime.now(timezone.utc).isoformat()
        elif args.action=='describe':
            matches=[r for r in rows if r['id']==args.argument]
            if not matches:raise ValueError('unknown_command: '+args.argument)
            reply=matches[0]
        else:
            reply=check_plan(domain,rows,plan)
            if args.action=='run':
                if args.stop_file and args.stop_file.exists():raise ValueError('stop_requested_before_native_edit')
                if capture_inputs(input_paths)!=input_sha:raise ValueError('input_changed_before_native_edit')
                if capture_resources(script_dir)!=resources:raise ValueError('skill_resources_changed_before_native_edit')
                preflight_writes(plan,input_sha,args.output_root)
                args.output.mkdir(parents=True)
                script=args.output/'native-plan.json'
                script_data=native_script(domain,plan['steps'])
                if domain=='printcraft':script.write_text(json.dumps(script_data,ensure_ascii=False)+'\n')
                else:script.write_text(''.join(json.dumps(s,ensure_ascii=False)+'\n' for s in script_data))
                argv=['script',str(script)] if domain=='designcraft' else ['run','--script',str(script)]
                if args.source:argv+=['--in',str(args.source)]
                if args.library:argv+=['--library',str(args.library)]
                for source in args.imports:argv+=['--import',str(source)]
                if args.root:argv+=['--root',str(args.root)]
                receipt={'domain':domain,'status':'STARTED','argv':prefix+['--',*argv],'catalogSha256':hashlib.sha256(json.dumps(raw,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'planSha256':hashlib.sha256(json.dumps(plan,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'automaticReplay':False,'completeAcceptance':False,'inputSha256':input_sha,'runtimeLockSha256':resources['runtime.lock.json'],'skillResourceSha256':resources}
                receipt.update(schemaVersion=1,runId=str(uuid.uuid4()),startedAt=datetime.now(timezone.utc).isoformat(),steps=[],libraryPath=str(args.library.resolve()) if args.library else None,outputRoot=str(args.output_root.resolve()) if args.output_root else None,libraryBeforeSha256=capture_inputs([args.library]) if args.library and args.library.exists() else None)
                target=args.output/'receipt.json';write_receipt(target,receipt)
                try:
                    # cli.py owns the sole native deadline; outer wait has no competing timeout.
                    supervised=prefix+['--supervised','--logs-dir',str(args.output/'logs'),'--timeout',str(args.timeout),'--',*argv]
                    if args.stop_file:supervised=prefix+['--supervised','--logs-dir',str(args.output/'logs'),'--timeout',str(args.timeout),'--stop-file',str(args.stop_file),'--',*argv]
                    result=subprocess.run(supervised,capture_output=True,text=True)
                    envelope=None
                    try:
                        candidate=strict_json(result.stdout)
                        if isinstance(candidate,dict) and (candidate.get('schemaVersion')==1 or candidate.get('result')=='unknown'):
                            envelope=candidate
                    except ValueError:pass
                    unknown=bool(envelope and (envelope.get('status')=='UNKNOWN' or envelope.get('result')=='unknown' or envelope.get('logComplete') is False))
                    stdout=output_text(envelope.get('stdout')) if envelope else result.stdout
                    stderr=output_text(envelope.get('stderr')) if envelope else result.stderr
                    code=envelope.get('exitCode',result.returncode) if envelope else result.returncode
                    log_path=args.output/'logs/stdout.log'
                    lines=bounded_lines(log_path) if log_path.exists() else stdout.splitlines()
                    if envelope and envelope.get('status')=='NOT_STARTED' and envelope.get('nativeProcessStarted') is False:
                        receipt.update(status='FAILED_OR_PARTIAL',protocolComplete=True,protocolErrors=[],steps=[{'index':i,'command':s['command'],'status':'NOT_EXECUTED'} for i,s in enumerate(plan['steps'])])
                    else:receipt.update(parse_results(plan['steps'],lines,code,unknown))
                    receipt.update(exitCode=code,stdout=stdout,stderr=stderr,process=envelope,runtimeIdentity=envelope.get('runtimeIdentity') if envelope else None)
                except (OSError,subprocess.SubprocessError,KeyboardInterrupt) as error:
                    receipt.update(status='UNKNOWN',error=str(error),stdout=output_text(getattr(error,'stdout',None)),stderr=output_text(getattr(error,'stderr',None)))
                try:
                    receipt['inputAfterSha256']=capture_inputs(input_paths)
                    if receipt['inputAfterSha256']!=input_sha and receipt['status']!='UNKNOWN':receipt['status']='INPUT_CHANGED_REVIEW_REQUIRED'
                    receipt['skillResourceAfterSha256']=capture_resources(script_dir)
                    if receipt['skillResourceAfterSha256']!=resources and receipt['status']!='UNKNOWN':receipt['status']='SKILL_CHANGED_REVIEW_REQUIRED'
                except (OSError,ValueError) as error:
                    receipt['preservationCheckError']=str(error)
                    if receipt['status']!='UNKNOWN':receipt['status']='INPUT_OR_SKILL_CHANGED_REVIEW_REQUIRED'
                if args.library and args.library.exists():
                    try:receipt['libraryAfterSha256']=capture_inputs([args.library])
                    except (OSError,ValueError) as error:receipt['libraryIdentityError']=str(error)
                receipt['endedAt']=datetime.now(timezone.utc).isoformat()
                write_receipt(target,receipt);reply=receipt
                if receipt['status']!='NATIVE_EXIT_ZERO_REVIEW_REQUIRED':print(json.dumps(reply,ensure_ascii=False));return 1
        print(json.dumps(reply,ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError,subprocess.SubprocessError,TypeError) as error:
        print(json.dumps({'error':str(error),'result':'failed','automaticReplay':False},ensure_ascii=False));return 1
