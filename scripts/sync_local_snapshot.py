"""同步未发布的本地插件快照；预检旧摘要，不覆盖漂移或已发布来源。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import os
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def inventory(root):
    """拒绝链接后计算技能文件摘要。"""
    entries=sorted(root.rglob('*'))
    if any(p.is_symlink() for p in entries):raise ValueError('snapshot_symlink')
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in entries if p.is_file() and '__pycache__' not in p.parts}


def sync(plugin):
    """仅对当前领域的未发布且未漂移快照做正常增量复制。"""
    domain=ROOT.name.removesuffix('-skills')
    metadata=plugin/'candidate-source.json'
    lock=json.loads(metadata.read_text())
    manifest=json.loads((plugin/'plugin.json').read_text())
    if (manifest['name']!=domain or lock.get('sourceProject')!=ROOT.name or lock.get('sourceStatus')!='local-unpublished-candidate' or lock.get('releaseTag') is not None):raise ValueError('not_current_local_candidate')
    current=inventory(plugin/'skills')
    if current!=lock['skillFileSha256']:raise ValueError('preserve_modified_plugin_snapshot')
    old_suite=json.loads((plugin/'source-suite.json').read_text())
    suite=json.loads((ROOT/'skill-suite.json').read_text())
    if lock.get('sourceVersion')!=old_suite['version'] or lock.get('managedSkills')!=old_suite['skills']:raise ValueError('source_identity_mismatch')
    if suite['skills']!=old_suite['skills']:raise ValueError('source_skill_set_change_requires_review')
    incoming=inventory(ROOT/'skills')
    if set(current)-set(incoming):raise ValueError('source_removal_requires_review')
    for relative,digest in incoming.items():
        if current.get(relative)==digest:continue
        target=plugin/'skills'/relative
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=current[relative]:raise ValueError('concurrent_snapshot_change')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'skills'/relative,target)
    if inventory(plugin/'skills')!=incoming:raise ValueError('snapshot_copy_mismatch')
    lock['skillFileSha256']=incoming
    lock.update(schemaVersion=1,sourceVersion=suite['version'],managedSkills=suite['skills'])
    # 元数据写入均为原子替换；中断导致身份不一致时校验失败，不伪造可用快照。
    for target,data in [(plugin/'source-suite.json',suite),(metadata,lock)]:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=target.parent,delete=False) as stream:
            temporary=Path(stream.name);json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,target)
    return {'domain':domain,'skills':len(list((ROOT/'skills').glob('*/SKILL.md'))),'sourceRelease':'UNPUBLISHED','snapshot':'PASS'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plugin-root',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(sync(args.plugin_root),ensure_ascii=False))
