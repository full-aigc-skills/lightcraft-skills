/** ArtCraft 公共协议消费快照；只校验交接与计算失效，不启动原生进程。 */
import {readFileSync,createReadStream} from 'node:fs';
import {readFile,realpath,stat} from 'node:fs/promises';
import {dirname,resolve,relative,isAbsolute} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
const root=dirname(fileURLToPath(import.meta.url));
const hash=(value:Buffer|string)=>createHash('sha256').update(value).digest('hex');
const domains=['lightcraft','designcraft','printcraft'];
const lock=JSON.parse(readFileSync(resolve(root,'exchange-protocol.lock.json'),'utf8'));
for(const name of ['exchange-craft-task-v1.json','exchange-craft-artifact-v1.json'])if(hash(readFileSync(resolve(root,name)))!==lock.schemaSha256?.[name])throw new Error('protocol_schema_drift');
const taskSchema=JSON.parse(readFileSync(resolve(root,'exchange-craft-task-v1.json'),'utf8'));
const artifactSchema=JSON.parse(readFileSync(resolve(root,'exchange-craft-artifact-v1.json'),'utf8'));

/** 使用与 ArtCraft 相同的 Node JSON 数值、键排序与摘要语义。 */
export function planHash(value:any):string {
 function canonical(item:any,depth=0):string {
  if(depth>64)throw new Error('protocol_depth_limit');
  if(item===null || typeof item==='boolean' || typeof item==='string')return JSON.stringify(item);
  if(typeof item==='number'){
   if(!Number.isFinite(item) || (Number.isInteger(item)&&!Number.isSafeInteger(item)))throw new Error('unsafe_number');
   return JSON.stringify(item);
  }
  if(Array.isArray(item))return '['+item.map(child=>canonical(child,depth+1)).join(',')+']';
  if(typeof item!=='object' || Object.getPrototypeOf(item)!==Object.prototype)throw new Error('non_json_value');
  return '{'+Object.keys(item).sort().map(key=>JSON.stringify(key)+':'+canonical(item[key],depth+1)).join(',')+'}';
 }
 return hash(canonical(value));
}

/** 除 JSON 语法外拒绝重复键，避免输入与摘要对同一字段产生不同解释。 */
export function parseUnique(text:string):any {
 if(Buffer.byteLength(text)>16*1024*1024)throw new Error('protocol_input_limit');
 const result=JSON.parse(text),tokens=text.match(/"(?:\\[\s\S]|[^"\\])*"|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null|[{}\[\]:,]/g)??[];
 let index=0;
 function scan(depth=0):void {
  if(depth>64)throw new Error('protocol_depth_limit');
  const token=tokens[index++];
  if(token==='{'){
   const keys=new Set<string>();
   while(tokens[index]!=='}'){
    const key=JSON.parse(tokens[index++]);if(keys.has(key))throw new Error('duplicate_json_field');keys.add(key);index++;scan(depth+1);
    if(tokens[index]===',')index++;
   }index++;
  }else if(token==='['){while(tokens[index]!==']'){scan(depth+1);if(tokens[index]===',')index++;}index++;}
 }
 scan();planHash(result);return result;
}

/** 仅解释固定快照实际采用的 schema 词汇，不加载外部 schema。 */
function check(schema:any,value:any,path='$'):void {
 const fail=()=>{throw new Error('protocol_invalid: '+path);};
 if(schema.anyOf){if(!schema.anyOf.some((child:any)=>{try{check(child,value,path);return true;}catch{return false;}}))fail();return;}
 if('const' in schema&&!isDeepStrictEqual(value,schema.const))fail();
 if(schema.enum&&!schema.enum.some((item:any)=>isDeepStrictEqual(item,value)))fail();
 if(schema.type==='null'&&value!==null || schema.type==='boolean'&&typeof value!=='boolean' || schema.type==='integer'&&!Number.isSafeInteger(value) || schema.type==='string'&&typeof value!=='string' || schema.type==='array'&&!Array.isArray(value) || schema.type==='object'&&(!value||typeof value!=='object'||Array.isArray(value)))fail();
 if(typeof value==='number'&&((schema.minimum!==undefined&&value<schema.minimum)||(schema.maximum!==undefined&&value>schema.maximum)))fail();
 if(typeof value==='string'){
  if((schema.minLength!==undefined&&[...value].length<schema.minLength)||(schema.maxLength!==undefined&&[...value].length>schema.maxLength)||(schema.pattern&&!new RegExp(schema.pattern).test(value)))fail();
  if(schema.format==='date-time'&&(!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?Z$/.test(value)||!Number.isFinite(Date.parse(value))||new Date(value).toISOString().slice(0,19)!==value.slice(0,19)))fail();
 }
 if(Array.isArray(value)&&schema.items)value.forEach((item,index)=>check(schema.items,item,path+'['+index+']'));
 if(schema.type==='object'){
  for(const key of schema.required??[])if(!Object.hasOwn(value,key))fail();
  for(const key of Object.keys(value))if(Object.hasOwn(schema.properties??{},key))check(schema.properties[key],value[key],path+'.'+key);else if(schema.additionalProperties===false)fail();
 }
}
function versions(artifacts:any[]):void {
 const seen=new Map<string,string>();
 for(const artifact of artifacts)for(const reference of [artifact,...(artifact.sourceRefs??[]),artifact.nativeProjectRef,...(artifact.renditions??[]),...(artifact.dependencies??[]).map((row:any)=>row.assetRef),artifact.lossReportRef,...(artifact.evidenceRefs??[])].filter(Boolean)){
  const key=JSON.stringify([reference.assetId,reference.version]);
  if(seen.has(key)&&seen.get(key)!==reference.sha256)throw new Error('artifact_version_conflict');seen.set(key,reference.sha256);
 }
}
function checkArtifact(value:any):void {
 check(artifactSchema,value);planHash(value);versions([value]);
 if(value.technicalMetadata.durationTicks!==undefined&&!value.technicalMetadata.timeBase)throw new Error('timebase_required');
 for(const item of value.dependencies)if(item.packaged?item.missingReason!==null:item.missingReason===null)throw new Error('dependency_packaging_invalid');
}

/** 兼容表是调用方配置；任务自身的版本声明不构成授权或信任。 */
export function checkTask(request:any,policy:any,inputs:any[],allowExpired=false):Record<string,any> {
 check(taskSchema,request);planHash(request);
 if(!policy||policy.schemaVersion!==1||!Array.isArray(policy.runtimes)||!policy.runtimes.length)throw new Error('trusted_runtime_policy_required');
 if(!domains.includes(request.runtimeIdentity.pluginId)||!policy.runtimes.some((row:any)=>isDeepStrictEqual(row,request.runtimeIdentity)))throw new Error('runtime_compatibility_mismatch');
 if(request.runtimeIdentity.mode!=='headless')throw new Error('exchange_mode_unsupported');
 if(!allowExpired&&Date.parse(request.deadline)<=Date.now())throw new Error('task_deadline_expired');
 if(planHash(request.payload)!==request.planHash)throw new Error('plan_hash_mismatch');
 const payload=request.payload,plan=payload.plan;
 if(payload.schemaVersion!=='craft-native-plan/v1'||Object.keys(payload).some(key=>!['schemaVersion','plan'].includes(key))||!plan||plan.domain!==request.runtimeIdentity.pluginId||Object.keys(plan).some(key=>!['domain','steps'].includes(key))||!Array.isArray(plan.steps)||plan.steps.length<1||plan.steps.length>1000)throw new Error('domain_plan_invalid');
 for(const step of plan.steps)if(!step||Object.keys(step).sort().join(',')!=='command,params'||typeof step.command!=='string'||!step.command||!step.params||typeof step.params!=='object'||Array.isArray(step.params))throw new Error('domain_step_invalid');
 if(!Array.isArray(inputs))throw new Error('input_artifacts_required');
 inputs.forEach(checkArtifact);versions(inputs);
 const refs=inputs.map(item=>({assetId:item.assetId,version:item.version,sha256:item.sha256}));
 if(new Set(refs.map(item=>item.assetId)).size!==refs.length||!isDeepStrictEqual(refs,request.inputRefs))throw new Error('input_version_binding_mismatch');
 return {status:'TASK_PREFLIGHT_ONLY',domain:plan.domain,plan:structuredClone(plan),inputRefs:structuredClone(refs),protocolSource:structuredClone(lock),executionAllowed:false,automaticReplay:false};
}

async function allowedPath(base:string,location:string):Promise<string> {
 if(typeof location!=='string'||!location||isAbsolute(location)||/[\\:\x00]/.test(location)||location.split('/').some(part=>['','..','.'].includes(part)))throw new Error('artifact_location_invalid');
 const directory=await realpath(base),path=await realpath(resolve(directory,location)),difference=relative(directory,path);
 if(!difference||difference==='..'||difference.startsWith('../')||isAbsolute(difference))throw new Error('artifact_location_escape');return path;
}
async function fileIdentity(path:string):Promise<{sha256:string;bytes:number;prefix:Buffer}> {
 const before=await stat(path);if(!before.isFile())throw new Error('artifact_not_regular');
 const digest=createHash('sha256');let bytes=0,prefix=Buffer.alloc(0);
 for await(const chunk of createReadStream(path)){const value=Buffer.from(chunk);digest.update(value);bytes+=value.length;if(prefix.length<4096)prefix=Buffer.concat([prefix,value.subarray(0,4096-prefix.length)]);}
 const after=await stat(path);if(before.ino!==after.ino||before.dev!==after.dev||before.mtimeMs!==after.mtimeMs||before.size!==after.size)throw new Error('artifact_changed_during_read');
 return {sha256:digest.digest('hex'),bytes,prefix};
}

/** 验证文件与引用身份；复杂格式/图像解码仍交给领域及 ArtCraft 专业验证器。 */
export async function verifyArtifact(value:any,base:string):Promise<any> {
 checkArtifact(value);const path=await allowedPath(base,value.location),facts=await fileIdentity(path);
 if(facts.sha256!==value.sha256||facts.bytes!==value.bytes)throw new Error('artifact_digest_mismatch');
 const mime=value.mediaType,p=facts.prefix;
 if(!['application/octet-stream','application/json','application/pdf','image/png','image/jpeg'].includes(mime))throw new Error('exchange_media_unsupported');
 if(mime==='image/png'&&!p.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))||mime==='image/jpeg'&&!(p[0]===255&&p[1]===216&&p[2]===255)||mime==='application/pdf'&&p.subarray(0,5).toString()!=='%PDF-')throw new Error('artifact_media_signature_mismatch');
 if(mime==='application/json')parseUnique(await readFile(path,'utf8'));
 if(value.lossReportRef!==null)throw new Error('exchange_loss_report_requires_domain_verifier');
 for(const ref of [value.nativeProjectRef,...value.renditions,...value.evidenceRefs].filter(Boolean))if((await fileIdentity(await allowedPath(base,ref.location))).sha256!==ref.sha256)throw new Error('artifact_reference_mismatch');
 return structuredClone(value);
}

function ordered(nodes:any[]):string[] {
 if(!Array.isArray(nodes)||nodes.length>1000)throw new Error('dependency_graph_invalid');
 const byId=new Map<string,any>(),state=new Map<string,number>(),order:string[]=[];
 for(const node of nodes){if(!node||typeof node.id!=='string'||!node.id||byId.has(node.id)||Object.keys(node).some(key=>!['id','dependsOn','request','inputs'].includes(key))||!Array.isArray(node.dependsOn)||node.dependsOn.some((key:any)=>typeof key!=='string')||new Set(node.dependsOn).size!==node.dependsOn.length)throw new Error('dependency_graph_invalid');byId.set(node.id,node);}
 function visit(id:string):void {if(!byId.has(id))throw new Error('dependency_missing');if(state.get(id)===1)throw new Error('dependency_cycle');if(state.get(id)===2)return;state.set(id,1);for(const parent of byId.get(id).dependsOn)visit(parent);state.set(id,2);order.push(id);}
 for(const id of byId.keys())visit(id);return order;
}

/** 失效是一项计算结果；不能自行重放任务、删除节点或授予执行权。 */
export function invalidation(previous:any[],current:any[],policy:any):Record<string,any> {
 const oldOrder=ordered(previous),order=ordered(current),before=new Map<string,string>(),after=new Map<string,string>();
 if(oldOrder.some(id=>!order.includes(id)))throw new Error('implicit_node_removal_rejected');
 const combined:any[]=[];
 for(const [nodes,target] of [[previous,before],[current,after]] as const){
  const all:any[]=[];
  for(const node of nodes){checkTask(node.request,policy,node.inputs,true);all.push(...node.inputs);const r=node.request;target.set(node.id,planHash({dependsOn:node.dependsOn,payload:r.payload,inputRefs:r.inputRefs,runtimeIdentity:r.runtimeIdentity,expectedRevision:r.expectedRevision,authorizationRef:r.authorizationRef,budget:r.budget}));}
  versions(all);combined.push(...all);
 }
 versions(combined);
 const changed=order.filter(id=>before.get(id)!==after.get(id)),affected=new Set(changed),byId=new Map(current.map(node=>[node.id,node]));
 for(const id of order)if(byId.get(id).dependsOn.some((parent:string)=>affected.has(parent)))affected.add(id);
 return {schemaVersion:1,changed,invalidated:order.filter(id=>affected.has(id)),reusable:order.filter(id=>!affected.has(id)),previousFingerprint:Object.fromEntries(before),currentFingerprint:Object.fromEntries(after),automaticReplay:false,executionAllowed:false};
}

/** 显式 JSON 文件入口；不会安装依赖或执行输入提供的命令。 */
export async function inspectBundle(bundle:any):Promise<any> {
 if(!bundle||typeof bundle!=='object'||Array.isArray(bundle))throw new Error('exchange_bundle_invalid');
 if(bundle.operation==='artifact'&&Object.keys(bundle).sort().join(',')==='artifact,operation,root')return {status:'ARTIFACT_IDENTITY_ONLY',artifact:await verifyArtifact(bundle.artifact,bundle.root),technicalAcceptance:'NOT_PROVEN',executionAllowed:false,automaticReplay:false};
 if(bundle.operation==='task'&&Object.keys(bundle).sort().join(',')==='inputs,operation,policy,request'){
  if(!Array.isArray(bundle.inputs))throw new Error('input_artifacts_required');
  const inputs=[];for(const item of bundle.inputs){if(!item||Object.keys(item).sort().join(',')!=='artifact,root')throw new Error('input_binding_invalid');inputs.push(await verifyArtifact(item.artifact,item.root));}
  return checkTask(bundle.request,bundle.policy,inputs);
 }
 if(bundle.operation==='invalidate'&&Object.keys(bundle).sort().join(',')==='current,operation,policy,previous')return invalidation(bundle.previous,bundle.current,bundle.policy);
 throw new Error('exchange_operation_invalid');
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
 try{if(Number(process.versions.node.split('.')[0])<24)throw new Error('node24_required');if(process.argv.length!==3)throw new Error('explicit_bundle_path_required');console.log(JSON.stringify(await inspectBundle(parseUnique(await readFile(process.argv[2],'utf8'))),null,2));}
 catch(error){console.log(JSON.stringify({error:(error as Error).message,executionAllowed:false,automaticReplay:false}));process.exitCode=1;}
}
