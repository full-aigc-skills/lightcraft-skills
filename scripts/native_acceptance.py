"""固定制品原生验收驱动；仅在获授权后用 --allow-install 启动。"""
import argparse
import hashlib
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import zlib

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/lightcraft-use/scripts'


def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def gradient(path):
    width,height=96,64
    def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data))
    pixels=b''.join(b'\x00'+b''.join(bytes([x*2,y*3,100]) for x in range(width)) for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b''))


def native(workdir,archive=None):
    workdir=Path(workdir).resolve();workdir.mkdir(parents=True,exist_ok=False)
    runtime=workdir/'runtime';library=workdir/'library';originals=workdir/'originals';originals.mkdir()
    exports=workdir/'exports';exports.mkdir()
    source=originals/'gradient.png';gradient(source)
    jpeg=originals/'gradient.jpg'
    inputs={}
    reply={'schemaVersion':1,'startedAt':datetime.now(timezone.utc).isoformat(),'workdir':str(workdir),'nativeStatus':'STARTED','visual':'NOT_RUN','host':'NOT_RUN','RAW':'NOT_RUN'}
    def command(argv):
        result=subprocess.run([sys.executable,'-I','-B',*argv],capture_output=True,text=True)
        if result.returncode:raise ValueError('native_acceptance_command_failed: '+result.stdout[-4000:]+result.stderr[-2000:])
        return json.loads(result.stdout)
    def run(name,steps):
        plan=workdir/(name+'-plan.json');plan.write_text(json.dumps({'domain':'lightcraft','steps':steps}))
        command([str(SCRIPTS/'commands.py'),'run',str(plan),'--runtime-home',str(runtime),'--require-installed','--library',str(library),'--input',str(originals),'--output-root',str(exports),'--output',str(workdir/name)])
        gateway=load('command_gateway');read=gateway.read_receipt(workdir/name/'receipt.json');receipt=read['receipt']
        if not read.get('compatible') or receipt.get('status')!='NATIVE_EXIT_ZERO_REVIEW_REQUIRED' or receipt.get('protocolComplete') is not True:raise ValueError('native_execution_unconfirmed')
        plan_sha=hashlib.sha256(json.dumps({'domain':'lightcraft','steps':steps},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if (receipt.get('planSha256')!=plan_sha or receipt.get('libraryPath')!=str(library)
                or receipt.get('skillResourceSha256')!=gateway.capture_resources(SCRIPTS)
                or receipt.get('inputSha256')!=inputs or receipt.get('inputAfterSha256')!=inputs):raise ValueError('native_execution_identity_mismatch')
        rows=receipt.get('steps',[])
        if len(rows)!=len(steps) or any(row.get('index')!=i or row.get('command')!=steps[i]['command'] or row.get('status')!='SUCCEEDED' for i,row in enumerate(rows)):raise ValueError('native_step_evidence_incomplete')
        return receipt
    def step(command,**params):return {'command':command,'params':params}
    try:
        subprocess.run(['sips','-s','format','jpeg',str(source),'--out',str(jpeg)],check=True,capture_output=True)
        inputs=load('command_gateway').capture_inputs([originals]);reply['inputs']=inputs
        argv=[str(SCRIPTS/'bootstrap.py'),'--runtime-home',str(runtime)]
        if archive:argv+=['--archive',str(archive)]
        reply['installation']=command(argv)
        reply['capabilities']=command([str(SCRIPTS/'commands.py'),'discover','--runtime-home',str(runtime),'--require-installed'])
        required={'library.import','library.select','catalog.query','photo.inspect','develop.get','develop.set','app.export','library.info'}
        observed={r['id'] for r in reply['capabilities']['commands']}
        if not required<=observed:raise ValueError('fixed_release_missing_commands: '+str(sorted(required-observed)))
        first=run('import',[step('library.import',paths=[str(source),str(jpeg)],mode='add'),step('catalog.query',limit=100)])
        imported=first['steps'][0]['native']['result']
        ids=imported.get('imported',[])
        if imported.get('failed') or imported.get('duplicates') or len(ids)!=2 or len(set(ids))!=2 or any(type(i) is not int for i in ids):raise ValueError('synthetic_import_failed')
        reply.update(photos=[],artifacts=[],receipts={'import':str(workdir/'import/receipt.json')})
        observed_sources=set()
        for photo_id in ids:
            edit_name='photo-'+str(photo_id)+'-edit-export';reopen_name='photo-'+str(photo_id)+'-reopen'
            before_path=exports/('before-'+str(photo_id)+'.png');png_path=exports/('edited-'+str(photo_id)+'.png');jpeg_path=exports/('edited-'+str(photo_id)+'.jpg')
            edit=run(edit_name,[step('library.select',ids=[photo_id],active=photo_id),step('photo.inspect',id=photo_id),step('develop.get',id=photo_id),step('app.export',path=str(before_path),format='png',width=60),step('develop.set',control='light.exposure',value=.5),step('develop.get',id=photo_id),step('app.export',path=str(png_path),format='png',width=60),step('app.export',path=str(jpeg_path),format='jpeg',width=60)])
            baseline=edit['steps'][2]['native']['result'];settings=edit['steps'][5]['native']['result']
            desired=load('photo_workflows').apply_local_changes(baseline,{'light.exposure':.5},reply['capabilities']['controls'])
            if settings!=desired:raise ValueError('unrelated_settings_changed')
            reopen=run(reopen_name,[step('library.select',ids=[photo_id],active=photo_id),step('photo.inspect',id=photo_id),step('develop.get',id=photo_id),step('library.info')])
            if reopen['runId']==edit['runId'] or reopen['steps'][2]['native']['result']!=settings:raise ValueError('reopen_settings_mismatch')
            old=edit['steps'][1]['native']['result'];new=reopen['steps'][1]['native']['result']
            identity=old.get('source',{})
            if (old.get('id')!=photo_id or old.get('id')!=new.get('id') or identity!=new.get('source')
                    or identity.get('type')!='file' or identity.get('path') not in inputs):raise ValueError('reopen_photo_identity_mismatch')
            observed_sources.add(identity['path'])
            info=reopen['steps'][3]['native']['result']
            if info.get('persistent') is not True or info.get('unsavedOps')!=0:raise ValueError('reopen_persistence_unconfirmed')
            if load('command_gateway').capture_inputs([originals])!=inputs:raise ValueError('originals_changed')
            facts=[load('artifacts').verify(path,exports,{'width':60,'format':fmt,'bitDepth':8}) for path,fmt in [(before_path,'png'),(png_path,'png'),(jpeg_path,'jpeg')]]
            if any(r['technicalStatus']!='PASS' for r in facts):raise ValueError('export_fact_mismatch')
            reply['photos'].append({'photoId':photo_id,'source':identity,'baselineSettings':baseline,'settings':settings,'artifacts':facts,'libraryInfo':info})
            reply['artifacts'].extend(facts)
            reply['receipts'].update({name:str(workdir/name/'receipt.json') for name in (edit_name,reopen_name)})
        if observed_sources!=set(inputs):raise ValueError('synthetic_input_coverage_incomplete')
        reply.update(nativeStatus='PASS',scope='两个合成 PNG/JPEG 输入均独立显影、前后导出及第二会话重开；视觉仍未验收')
    except (ValueError,OSError,KeyError,TypeError,IndexError,AttributeError,subprocess.SubprocessError) as error:
        reply.update(nativeStatus='FAIL',error=str(error))
    reply['endedAt']=datetime.now(timezone.utc).isoformat()
    (workdir/'native-evidence.json').write_text(json.dumps(reply,ensure_ascii=False,indent=2)+'\n')
    return reply


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workdir',type=Path,required=True);parser.add_argument('--archive',type=Path);parser.add_argument('--allow-install',action='store_true')
    args=parser.parse_args()
    if not args.allow_install:parser.error('requires_runtime_install_authorization_and_allow_install')
    result=native(args.workdir,args.archive);print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['nativeStatus']=='PASS' else 1)
