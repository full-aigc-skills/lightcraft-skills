"""显式固定三领域原生制品的协议验收；不安装、不修改其他仓库或启动宿主。"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk:=stream.read(1024*1024):digest.update(chunk)
    return digest.hexdigest()
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'runtime'/(name+'.py'));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def json_objects(text):
    decoder=json.JSONDecoder();rows=[];remaining=text.strip()
    while remaining:
        value,end=decoder.raw_decode(remaining);rows.append(value);remaining=remaining[end:].strip()
    return rows
def plan_hash(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workdir',required=True,type=Path);parser.add_argument('--allow-native',action='store_true');parser.add_argument('--node',default='node');parser.add_argument('--contract',type=Path,default=ROOT/'runtime/craft_exchange.ts')
    for domain in ('lightcraft','designcraft','printcraft'):
        parser.add_argument('--'+domain+'-cli',required=True,type=Path);parser.add_argument('--'+domain+'-lock',required=True,type=Path)
    args=parser.parse_args()
    if not args.allow_native:parser.error('requires_existing_native_execution_authorization')
    work=args.workdir.resolve();work.mkdir(parents=True,exist_ok=False);runtime={};catalogs={};identities=[];records=[];artifacts=[];requests=[]
    supervisor=module('native_process');contract=args.contract.resolve();contract_files={str(p):sha(p) for p in contract.parent.iterdir() if p.name in ('craft_exchange.ts','exchange-craft-task-v1.json','exchange-craft-artifact-v1.json','exchange-protocol.lock.json')}
    acceptance_files={str(p):sha(p) for p in [Path(__file__).resolve(),ROOT/'runtime/native_process.py',ROOT/'runtime/command_gateway.py']}
    runtime_locks={str(getattr(args,domain+'_lock').resolve()):sha(getattr(args,domain+'_lock')) for domain in ('lightcraft','designcraft','printcraft')}
    def run_native(domain,name,argv):
        executable=runtime[domain]
        if sha(executable)!=next(row['sha256'] for row in identities if row['pluginId']==domain):raise ValueError('binary_changed_before_execution')
        result=supervisor.supervise([str(executable),*argv],work/(name+'-logs'),120,tee=False)
        write(work/(name+'-process.json'),result)
        if result.get('status')!='EXITED' or result.get('exitCode')!=0 or result.get('logComplete') is not True:raise ValueError('native_not_confirmed: '+name+' '+result.get('stderr',''))
        return (work/(name+'-logs/stdout.log')).read_text()
    # 在原生运行前按本地明确锁核对三个已有制品；不调用安装器。
    for domain in ('lightcraft','designcraft','printcraft'):
        path=getattr(args,domain+'_cli').resolve();lock=json.loads(getattr(args,domain+'_lock').read_text());expected=lock['artifacts']['darwin-arm64']
        if lock['artifact']!=domain+'-cli' or sha(path)!=expected['binarySha256']:raise ValueError('fixed_binary_required: '+domain)
        runtime[domain]=path;identities.append({'pluginId':domain,'pluginVersion':'lightcraft-exchange-local-acceptance','cliVersion':lock['resolvedVersion'],'sha256':expected['binarySha256'],'mode':'headless','capabilitySnapshotSha256':'0'*64})
        version=run_native(domain,domain+'-version',['--version']).strip()
        if version.splitlines()[0]!=expected['versionOutput']:raise ValueError('native_version_mismatch')
        catalog=json.loads(run_native(domain,domain+'-catalog',['tools'] if domain=='printcraft' else ['commands','--json'] if domain=='lightcraft' else ['commands']))
        if not isinstance(catalog,list) or not catalog:raise ValueError('native_catalog_missing')
        catalogs[domain]=catalog;identities[-1]['capabilitySnapshotSha256']=plan_hash(catalog);write(work/(domain+'-catalog.json'),catalog)
    policy={'schemaVersion':1,'runtimes':identities};write(work/'policy.json',policy)
    step=lambda command,**params:{'command':command,'params':params}
    def artifact(path,asset,task,inputs):
        digest=sha(path);value={'protocolVersion':'craft-artifact/v1','assetId':asset,'version':digest,'sha256':digest,'bytes':path.stat().st_size,'mediaType':'image/png' if path.suffix=='.png' else 'application/pdf','producerTaskId':task,'sourceRefs':[{'assetId':a['assetId'],'version':a['version'],'sha256':a['sha256']} for a in inputs],'nativeProjectRef':None,'renditions':[],'dependencies':[],'technicalMetadata':{},'lossReportRef':None,'evidenceRefs':[],'location':str(path.relative_to(work))}
        return value
    def execute(domain,name,steps,inputs,options):
        payload={'schemaVersion':'craft-native-plan/v1','plan':{'domain':domain,'steps':steps}}
        request={'protocolVersion':'craft-task/v1','taskId':name,'idempotencyKey':name,'planHash':plan_hash(payload),'inputRefs':[{'assetId':a['assetId'],'version':a['version'],'sha256':a['sha256']} for a in inputs],'expectedRevision':plan_hash(module('command_gateway').capture_inputs([library])) if '--library' in options and library.exists() else None,'runtimeIdentity':next(row for row in identities if row['pluginId']==domain),'authorizationRef':'explicit-local-native-protocol-acceptance','budget':{'currency':'USD','maxMinorUnits':0,'maxRevisions':2,'maxExternalCalls':0},'deadline':'2099-01-01T00:00:00.000Z','payload':payload}
        request_file=work/(name+'-request.json');write(request_file,request)
        bundle=work/(name+'-preflight.json');write(bundle,{'operation':'task','request':request,'policy':policy,'inputs':[{'root':str(work),'artifact':a} for a in inputs]})
        checked=subprocess.run([args.node,str(contract),str(bundle)],capture_output=True,text=True)
        if checked.returncode:raise ValueError('protocol_preflight_failed: '+checked.stdout)
        write(work/(name+'-preflight-result.json'),json.loads(checked.stdout))
        gateway=module('command_gateway');gateway.check_plan(domain,gateway.normalize(domain,catalogs[domain]),payload['plan'])
        input_sha={a['location']:sha(work/a['location']) for a in inputs}
        native=work/(name+'-native.json');native_data=gateway.native_script(domain,steps)
        native.write_text(json.dumps(native_data)+'\n' if domain=='printcraft' else ''.join(json.dumps(row)+'\n' for row in native_data))
        argv=['script',str(native)] if domain=='designcraft' else ['run','--script',str(native)]
        stdout=run_native(domain,name,argv+options)
        if any(sha(work/location)!=digest for location,digest in input_sha.items()):raise ValueError('upstream_input_changed')
        requests.append(request);records.append({'taskId':name,'domain':domain,'requestSha256':sha(request_file),'inputSha256':input_sha,'nativeScriptSha256':sha(native),'argv':argv+options,'process':str(work/(name+'-process.json'))})
        return stdout
    # 合成输入为验收夹具，不使用品牌、字体或用户原片。
    spec=importlib.util.spec_from_file_location('fixture',ROOT/'scripts/native_acceptance.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    original=work/'original.png';fixture.gradient(original);original_sha=sha(original);library=work/'library';original_artifact=artifact(original,'original-photo','fixture',[]);artifacts.append(original_artifact)
    imported=execute('lightcraft','photo-import',[step('library.import',paths=[str(original)],mode='add'),step('catalog.query',limit=10)],[original_artifact],['--library',str(library)])
    rows=[json.loads(line) for line in imported.splitlines() if line.strip()];report=rows[0]['result']
    if rows[0].get('ok') is not True or report.get('failed') or report.get('duplicates') or len(report.get('imported',[]))!=1:raise ValueError('photo_import_not_confirmed')
    identifier=report['imported'][0]
    photo=work/'photo.png'
    output=execute('lightcraft','photo',[step('library.select',ids=[identifier],active=identifier),step('develop.set',control='light.exposure',value=1),step('app.export',path=str(photo),format='png',width=96),step('library.info')],[original_artifact],['--library',str(library)])
    rows=[json.loads(line) for line in output.splitlines() if line.strip()]
    if len(rows)!=4 or any(row.get('ok') is not True for row in rows):raise ValueError('photo_export_not_confirmed')
    if rows[-1]['result'].get('persistent') is not True or rows[-1]['result'].get('unsavedOps')!=0:raise ValueError('photo_persistence_not_confirmed')
    facts=module('artifacts').verify(photo,work,{'format':'png','width':96,'height':64,'bitDepth':8})
    if facts['technicalStatus']!='PASS':raise ValueError('photo_decode_failed')
    photo_artifact=artifact(photo,'developed-photo','photo',[original_artifact]);artifacts.append(photo_artifact)
    pdf=work/'layout.pdf';project=work/'page.designcraft'
    layout_stdout=execute('designcraft','layout',[step('file.new',width=96,height=64,pages=1,facingPages=False,margins=0),step('file.place',path=str(photo),x=0,y=0,width=96),step('file.saveAs',path=str(project)),step('file.exportPdf',path=str(pdf)),step('document.inspect')],[photo_artifact],[])
    if not pdf.is_file() or not project.is_file():raise ValueError('layout_outputs_missing')
    layout_result=json.loads(layout_stdout)
    if layout_result.get('completed')!=5 or len(layout_result.get('results',[]))!=5 or any(key in layout_result for key in ('error','failedIndex','failedCommand')):raise ValueError('layout_steps_not_confirmed')
    saved,exported,inspected=layout_result['results'][2:]
    if saved.get('path')!=str(project) or saved.get('bytes')!=project.stat().st_size or exported.get('path')!=str(pdf) or exported.get('bytes')!=pdf.stat().st_size or exported.get('pages')!=1 or exported.get('warnings') or inspected.get('dirty') is not False or inspected.get('pageCount')!=1:raise ValueError('layout_business_result_mismatch')
    layout_artifact=artifact(pdf,'layout-pdf','layout',[photo_artifact]);layout_artifact['nativeProjectRef']={'assetId':'layout-native','version':sha(project),'sha256':sha(project),'location':project.name};artifacts.append(layout_artifact)
    delivered=work/'delivery.pdf'
    pdf_stdout=execute('printcraft','pdf',[step('doc_open',path=str(pdf)),step('doc_info',doc=1),step('doc_save',doc=1,path=str(delivered),full=True)],[layout_artifact],[])
    pdf_results=json_objects(pdf_stdout)
    if len(pdf_results)!=3 or pdf_results[0].get('doc')!=1 or pdf_results[0].get('pages')!=1 or len(pdf_results[1].get('pages',[]))!=1 or pdf_results[2].get('path')!=str(delivered) or pdf_results[2].get('bytes')!=delivered.stat().st_size or pdf_results[2].get('document',{}).get('dirty') is not False:raise ValueError('pdf_steps_not_confirmed')
    info=json.loads(run_native('printcraft','pdf-reopen',['info',str(delivered)]))
    if info.get('pages')!=1:raise ValueError('pdf_reopen_failed')
    artifacts.append(artifact(delivered,'delivery-pdf','pdf',[layout_artifact]))
    if sha(original)!=original_sha:raise ValueError('original_changed')
    if any(sha(Path(path))!=digest for path,digest in contract_files.items()):raise ValueError('contract_resources_changed')
    if any(sha(runtime[row['pluginId']])!=row['sha256'] for row in identities):raise ValueError('native_binary_changed')
    if any(sha(Path(path))!=digest for path,digest in dict(acceptance_files,**runtime_locks).items()):raise ValueError('acceptance_or_lock_changed')
    result={'status':'PASS','acceptanceFiles':acceptance_files,'runtimeLocks':runtime_locks,'scope':'three-domain native outputs and public protocol preflight only','runtimeIdentity':identities,'contractFiles':contract_files,'originalSha256':original_sha,'records':records,'requests':requests,'artifacts':artifacts,'root':str(work),'photoFacts':facts,'pdfReopen':info,'artcraftHost':'NOT_RUN','artcraftScheduler':'NOT_RUN','visual':'NOT_RUN','mobile':'NOT_RUN','automaticReplay':False,'completeAcceptance':False}
    write(work/'native-exchange-report.json',result);print(json.dumps({'status':'PASS','report':str(work/'native-exchange-report.json')}))
if __name__=='__main__':main()
