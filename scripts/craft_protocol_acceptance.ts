/** 用 ArtCraft 实际公共协议实现复核三领域产物；不启动宿主或重放任务。 */
import {readFile,writeFile,readdir,stat} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
const [producerValue,reportValue,contractValue]=process.argv.slice(2);
if(!producerValue||!reportValue||!contractValue)throw new Error('three_explicit_paths_required');
const producer=resolve(producerValue),reportPath=resolve(reportValue),contractPath=resolve(contractValue);
const hash=(value:Buffer|string)=>createHash('sha256').update(value).digest('hex');
const inventory=async()=>{const result:Record<string,string>={};async function visit(path:string){for(const entry of await readdir(join(producer,path),{withFileTypes:true})){if(entry.isSymbolicLink())throw new Error('producer_source_symlink');const name=path+'/'+entry.name;if(entry.isDirectory())await visit(name);else if(entry.isFile())result[name]=hash(await readFile(join(producer,name)));}}await visit('src');await visit('schemas');result['package.json']=hash(await readFile(join(producer,'package.json')));return result;};
const before=await inventory(),commit=execFileSync('git',['-C',producer,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
const own=await import(pathToFileURL(contractPath).href);
const load=(name:string)=>import(pathToFileURL(join(producer,'src',name)).href);
const {validateTask,verifyArtifact,planHash}=await load('protocol/contracts.ts');
const {invalidated}=await load('protocol/dependency_graph.ts');
const {TaskLedger}=await load('harness/task_ledger.ts');

const reportBytes=await readFile(reportPath),report=JSON.parse(reportBytes.toString()),policy={schemaVersion:1,runtimes:report.runtimeIdentity};
assert.equal(report.status,'PASS');
const schemaLock=JSON.parse(await readFile(new URL('exchange-protocol.lock.json',pathToFileURL(contractPath)),'utf8'));
for(const [name,digest] of Object.entries(schemaLock.schemaSha256)){
 const originalName=name.replace('exchange-','');assert.equal(hash(await readFile(join(producer,'schemas',originalName))),digest,'current schema compatibility changed');
 assert.equal(hash(execFileSync('git',['-C',producer,'show',schemaLock.commit+':schemas/'+originalName])),digest,'pinned schema blob mismatch');
}
const artifactById=new Map(report.artifacts.map((artifact:any)=>[artifact.assetId,artifact]));
const ledger=new TaskLedger(join(report.root,'protocol-acceptance.sqlite'));
const planned:any[]=[];
try{
 for(const request of report.requests){
  validateTask(request);assert.equal(planHash(request.payload),request.planHash);assert.equal(own.planHash(request.payload),request.planHash);
  const inputs=request.inputRefs.map((ref:any)=>{const artifact=artifactById.get(ref.assetId);assert.ok(artifact);return artifact;});
  own.checkTask(request,policy,inputs);
  const row=ledger.register('lightcraft-local-protocol-acceptance',request.taskId,request);assert.equal(row.state,'planned');planned.push({taskId:request.taskId,state:row.state});
 }
 for(const artifact of report.artifacts){await verifyArtifact(artifact,report.root);await own.verifyArtifact(artifact,report.root);}
 const tasks=new Map(report.requests.map((request:any)=>[request.taskId,request]));
 const node=(id:string,parents:string[])=>({id,dependsOn:parents,request:tasks.get(id),inputs:tasks.get(id).inputRefs.map((ref:any)=>artifactById.get(ref.assetId))});
 const previous=[node('photo',[]),node('layout',['photo']),node('pdf',['layout']),{...node('photo-import',[]),id:'unrelated'}];
 const current=structuredClone(previous);current[0].request.payload.plan.steps[1].params.value+=1;current[0].request.planHash=planHash(current[0].request.payload);
 const result=own.invalidation(previous,current,policy),official=[...invalidated(current,['photo'])];
 assert.deepEqual(result.invalidated,official);assert.deepEqual(result.invalidated,['photo','layout','pdf']);assert.deepEqual(result.reusable,['unrelated']);
 const numbers=[{v:-0},{v:1e-7},{v:0.000001},{v:0.25},{'😀':true,'\ue000':'中文'}];for(const value of numbers)assert.equal(own.planHash(value),planHash(value));
 assert.deepEqual(await inventory(),before,'producer source changed during acceptance');
 assert.equal(hash(await readFile(reportPath)),hash(reportBytes));
 const output={status:'PASS',scope:'actual ArtCraft public validation and planned ledger; native three-domain results; not scheduler/host acceptance',producerCommit:commit,producerVersion:JSON.parse(await readFile(join(producer,'package.json'),'utf8')).version,producerSourceSha256:before,nativeReportSha256:hash(reportBytes),schemaLock,plannedTasks:planned,artifactCount:report.artifacts.length,domains:report.runtimeIdentity.map((row:any)=>row.pluginId),invalidation:result,canonicalDifferentialCount:numbers.length,artcraftScheduler:'NOT_RUN',host:'NOT_RUN',visual:'NOT_RUN',automaticReplay:false,completeAcceptance:false};
 await writeFile(join(report.root,'protocol-acceptance.json'),JSON.stringify(output,null,2)+'\n');
 console.log(JSON.stringify({status:'PASS',report:join(report.root,'protocol-acceptance.json')}));
}finally{ledger.close();}
