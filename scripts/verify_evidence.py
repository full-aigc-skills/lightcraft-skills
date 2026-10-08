"""验证报告绑定当前源码；旧报告不能证明变更后通过。"""
import argparse
import hashlib
import json
from pathlib import Path


def fingerprint(root):
    root=Path(root);files={}
    for directory in ('runtime','skills','scripts','tests','schemas','.codex-plugin','.github','licenses','examples'):
        for path in sorted((root/directory).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py','.json','.md','.yaml','.yml','.txt'):
                files[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ('plugin.json','skill-suite.json','source-suite.json','candidate-source.json','local-components.json','README.md','LICENSE','THIRD_PARTY_NOTICES.md'):
        path=root/name
        if path.is_file():files[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted((root/'docs').rglob('*.md')):
        if 'verification' not in path.relative_to(root/'docs').parts:
            files[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()


def validate(root, report):
    if report.get('schemaVersion')!=1:raise ValueError('evidence_schema_unsupported')
    if report.get('sourceFingerprint')!=fingerprint(root):raise ValueError('evidence_stale_source_changed')
    layers=report.get('layers',{})
    for layer in ('structure','mock','native','host','visual','platform','remoteCI'):
        if layer not in layers or layers[layer].get('status') not in ('PASS','FAIL','NOT_RUN','BLOCKED'):
            raise ValueError('evidence_layer_missing: '+layer)
        if layers[layer]['status']=='PASS' and not layers[layer].get('evidence'):
            raise ValueError('evidence_pass_without_artifact: '+layer)
    return {'source':'CURRENT','layers':{k:v['status'] for k,v in layers.items()}}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args();print(json.dumps(validate(args.root,json.loads(args.report.read_text())),ensure_ascii=False))
