#!/usr/bin/env python3
"""从当前独立技能安装/核验固定 CLI，然后按 argv 调用；不依赖 PATH 或兄弟技能。"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
sys.dont_write_bytecode=True
ALLOWED={'render', 'help', '-h', '-V', 'snapshot', 'controls', '--help', '--version', 'run', 'version', 'mcp', 'synth-merge', 'commands', 'merge'}
def setup_failure(runtime_home):
 """安装器缺失时也保留当前技能自身的恢复位置，不读取兄弟技能。"""
 return {'skill':'lightcraft-cli-setup','bootstrapScript':str(Path(__file__).with_name('bootstrap.py').resolve()),'runtimeHome':str(Path(runtime_home).expanduser().absolute()),'automaticRetry':False}
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--runtime-home',default=os.environ.get('CRAFT_RUNTIME_HOME',str(Path.home()/'.local/share/craft-runtimes')))
 parser.add_argument('--archive',type=Path)
 parser.add_argument('--require-installed',action='store_true',help='仅核验并使用已有运行时；缺失或损坏时拒绝，不调用安装器')
 parser.add_argument('--supervised',action='store_true',help='内部网关协议，输出监督结果而非原始 stdout')
 parser.add_argument('--logs-dir',type=Path)
 parser.add_argument('--timeout',type=float,default=600)
 parser.add_argument('--stop-file',type=Path)
 parser.add_argument('--requests',type=Path,help='固定只读 MCP 探测 JSONL；在启动前读入，不开放修改工具')
 parser.add_argument('arguments',nargs=argparse.REMAINDER)
 args=parser.parse_args();argv=args.arguments
 if argv[:1]==['--']:argv=argv[1:]
 if not argv or argv[0] not in ALLOWED:parser.error('unsupported_cli_subcommand: put the native subcommand first after --')
 installation_completed=False
 try:
  mode_path=Path(__file__).with_name('mode_contract.py');mode_spec=importlib.util.spec_from_file_location('mode_contract',mode_path)
  mode=importlib.util.module_from_spec(mode_spec);mode_spec.loader.exec_module(mode)
  requests,stdin_data=mode.requests_text(args.requests) if args.requests else (None,None)
  execution_mode=mode.inspect_mode(argv,requests)
  if execution_mode.get('scriptSha256'):
   index=argv.index('--script')+1
   with Path(argv[index]).open('rb') as stream:stdin_data=stream.read(1048577)
   if hashlib.sha256(stdin_data).hexdigest()!=execution_mode['scriptSha256']:raise ValueError('connect_script_changed_after_validation')
   argv=list(argv);argv[index]='-'
  path=Path(__file__).with_name('bootstrap.py');spec=importlib.util.spec_from_file_location('craft_bootstrap',path)
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  lock=json.loads(path.with_name('runtime.lock.json').read_text(encoding='utf-8'))
  if args.require_installed:
   if args.archive:raise ValueError('require_installed_conflicts_with_archive')
   installed=module.doctor(lock,args.runtime_home)
   if installed['status']!='READY':raise ValueError('require_installed_runtime_not_ready: '+installed['status'])
  else:installed=module.install(lock,args.runtime_home,args.archive)
  installation_completed=True
  supervisor_path=Path(__file__).with_name('native_process.py')
  supervisor_spec=importlib.util.spec_from_file_location('native_process',supervisor_path)
  supervisor=importlib.util.module_from_spec(supervisor_spec);supervisor_spec.loader.exec_module(supervisor)
  with tempfile.TemporaryDirectory(prefix='lightcraft-direct-') as temporary:
   logs=args.logs_dir or Path(temporary)
   options={'stdin_data':stdin_data} if stdin_data is not None else {}
   result=supervisor.supervise([installed['executable'],*argv],logs,args.timeout,tee=not args.supervised,stop_file=args.stop_file,**options)
  result['runtimeIdentity']={'version':json.loads(path.with_name('runtime.lock.json').read_text(encoding='utf-8'))['resolvedVersion'],'binarySha256':installed['binarySha256'],'executable':installed['executable'],**execution_mode}
  if stdin_data is not None:result['stdinSha256']=hashlib.sha256(stdin_data).hexdigest()
  if args.supervised:print(json.dumps(result,ensure_ascii=True))
  elif result['status']=='UNKNOWN':print(json.dumps({'result':'unknown','error':result.get('error'),'automaticReplay':False}))
  return result.get('exitCode',1) if result['status']=='EXITED' else 1
 except (ValueError,OSError,subprocess.SubprocessError) as error:
  reply={'error':str(error),'result':'unknown' if isinstance(error,subprocess.TimeoutExpired) else 'failed','schemaVersion':1,'status':'UNKNOWN' if isinstance(error,subprocess.TimeoutExpired) else 'NOT_STARTED','nativeProcessStarted':False,'automaticReplay':False}
  if not installation_completed:reply['dependencySetup']=setup_failure(args.runtime_home)
  print(json.dumps(reply));return 1
if __name__=='__main__':raise SystemExit(main())
