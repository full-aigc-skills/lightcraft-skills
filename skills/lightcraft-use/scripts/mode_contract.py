"""固定 CLI 的模式与只读 Connect 边界；不复制原生命令解释器。"""
import hashlib
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlsplit

READ_COMMANDS={'library.info','library.state','catalog.query','photo.inspect','develop.get','develop.controls','engine.commands'}


def gateway():
    path=Path(__file__).with_name('command_gateway.py')
    spec=importlib.util.spec_from_file_location('session_gateway',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def probe_requests():
    """返回固定的只读 MCP 生命周期和实际库查询；不导出修改工具。"""
    return [{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'lightcraft-readonly-probe','version':'1'}}},
            {'jsonrpc':'2.0','method':'notifications/initialized','params':{}},
            {'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}},
            {'jsonrpc':'2.0','id':3,'method':'resources/read','params':{'uri':'lightcraft://library'}}]


def is_probe_requests(rows):
    """严格保留 JSON 类型，不把布尔 ID 当成整数 ID。"""
    return json.dumps(rows,sort_keys=True,allow_nan=False)==json.dumps(probe_requests(),sort_keys=True)


def requests_text(path):
    """只接受固定探测事务，拒绝额外工具调用和重复字段。"""
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>1048576:raise ValueError('invalid_bounded_readonly_requests')
    with path.open('rb') as stream:data=stream.read(1048577)
    if len(data)>1048576:raise ValueError('invalid_bounded_readonly_requests')
    rows=[gateway().strict_json(line) for line in data.decode('utf-8').splitlines() if line.strip()]
    if not is_probe_requests(rows):raise ValueError('invalid_bounded_readonly_requests')
    return rows,data


def inspect_mode(argv,requests=None):
    """在安装或执行前检查连接模式；修改路径因原生重试而拒绝。"""
    action=argv[0];connect=None;headless=False;headless_data=False;script=None;script_sha=None;remaining=[];i=1
    if action not in ('run','mcp'):
        if requests is not None:raise ValueError('requests_only_for_mcp')
        return {'mode':'Headless','transport':'process','connectAddress':None,'readOnly':False,'nativeMayRetryReads':False}
    while i<len(argv):
        arg=argv[i]
        if arg=='--':remaining=argv[i+1:];break
        if arg=='--connect' or arg.startswith('--connect='):
            if connect is not None:raise ValueError('duplicate_connect')
            if '=' in arg:connect=arg.split('=',1)[1]
            elif i+1<len(argv) and ':' in argv[i+1] and '=' not in argv[i+1] and not argv[i+1].startswith('--'):
                i+=1;connect=argv[i]
            else:connect='127.0.0.1:7980'
        elif arg in ('--headless','--demo'):
            headless=True
        elif arg in ('--library','--import','--script'):
            i+=1
            if i>=len(argv):raise ValueError('native_option_value_missing: '+arg)
            if arg=='--script':
                if script is not None:raise ValueError('duplicate_native_script')
                script=argv[i]
            else:headless_data=True
        elif arg in ('--compact','--keep-going'):pass
        elif arg.startswith('--'):raise ValueError('unsupported_native_mode_option: '+arg)
        elif action=='run':remaining=argv[i:];break
        else:headless_data=True
        i+=1
    if connect is not None:
        if headless or headless_data:raise ValueError('mode_conflict_connect_headless')
        try:
            parsed=urlsplit('//'+connect)
            if not parsed.hostname or not parsed.port or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:raise ValueError()
        except ValueError:raise ValueError('invalid_connect_address') from None
        if action=='mcp':
            if not is_probe_requests(requests):raise ValueError('connect_mcp_requires_bounded_readonly_requests')
        else:
            commands=[]
            if script is not None:
                if script=='-':raise ValueError('connect_stdin_script_not_auditable')
                path=Path(script)
                if path.is_symlink() or not path.is_file() or path.stat().st_size>1048576:raise ValueError('connect_script_invalid')
                with path.open('rb') as stream:data=stream.read(1048577)
                if len(data)>1048576:raise ValueError('connect_script_invalid')
                script_sha=hashlib.sha256(data).hexdigest()
                for line in data.decode('utf-8').splitlines():
                    if not line.strip() or line.lstrip().startswith('#'):continue
                    row=gateway().strict_json(line)
                    if not isinstance(row,dict) or set(row)-{'command','method','params'} or ('command' in row)==('method' in row) or not isinstance(row.get('params',{}),dict):raise ValueError('connect_script_invalid')
                    commands.append(row.get('command',row.get('method')))
            if remaining:
                commands.append(remaining[0])
                commands.extend(a for a in remaining[1:] if '=' not in a)
            if not commands or any(command not in READ_COMMANDS for command in commands):raise ValueError('connect_write_unsupported_native_retry')
    if requests is not None and (action!='mcp' or not is_probe_requests(requests)):raise ValueError('invalid_bounded_readonly_requests')
    return {'mode':'Connect' if connect is not None else 'Headless','transport':'stdio-mcp' if action=='mcp' else 'jsonl-run',
            'connectAddress':connect,'readOnly':connect is not None or requests is not None,'nativeMayRetryReads':connect is not None,'scriptSha256':script_sha}


def classify_probe(requests,replies,version):
    """按 MCP ID 核对响应，沿用执行层的 UNKNOWN 和 NotSaved 分类。"""
    if not is_probe_requests(requests) or not isinstance(replies,list):raise ValueError('invalid_probe_protocol')
    expected=[r for r in requests if 'id' in r]
    steps=[{'command':'mcp:'+r['method'],'params':r['params']} for r in expected]
    rows=[];failed=False;protocol_unknown=len(replies)!=len(expected)
    for i,reply in enumerate(replies):
        if (i>=len(expected) or not isinstance(reply,dict) or reply.get('jsonrpc')!='2.0' or type(reply.get('id')) is not int
                or reply['id']!=expected[i]['id'] or ('error' in reply)==('result' in reply)):
            protocol_unknown=True;break
        value=reply.get('result');error=reply.get('error')
        if error is not None and not isinstance(error,dict):protocol_unknown=True;break
        if error is None:
            if not isinstance(value,dict):protocol_unknown=True;break
            if i==0:
                server=value.get('serverInfo')
                if not isinstance(server,dict) or server.get('name')!='lightcraft' or server.get('version')!=version:protocol_unknown=True
            if i==1 and not isinstance(value.get('tools'),list):protocol_unknown=True
            if i==2:
                contents=value.get('contents')
                if not isinstance(contents,list) or len(contents)!=1:protocol_unknown=True
                else:
                    content=contents[0]
                    try:
                        if not isinstance(content,dict) or content.get('uri')!='lightcraft://library' or not isinstance(gateway().strict_json(content.get('text','')),dict):protocol_unknown=True
                    except (TypeError,ValueError):protocol_unknown=True
        bad='error' in reply
        row={'command':steps[i]['command'],'ok':not bad}
        if bad:row['error']=str(reply['error'].get('message','unknown MCP error'))
        else:row['result']=reply['result']
        rows.append(json.dumps(row));failed=failed or bad
        if bad:break
    result=gateway().parse_results(steps,rows,1 if failed else 0,protocol_unknown)
    result['mcpReplies']=replies
    result['backendQuery']='PASS' if result['status']=='NATIVE_EXIT_ZERO_REVIEW_REQUIRED' else 'NOT_CONFIRMED'
    return result
