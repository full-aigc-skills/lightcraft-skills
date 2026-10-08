"""发行门禁：只读检查，不创建 Git 身份或发布。"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def check(report):
    load('validate_package').validate()
    load('verify_evidence').validate(ROOT,report)
    missing=[layer for layer in ('structure','mock','native','host','visual','platform') if report['layers'][layer]['status']!='PASS']
    git=subprocess.run(['git','rev-parse','--show-toplevel'],cwd=ROOT,capture_output=True,text=True)
    if git.returncode or Path(git.stdout.strip()).resolve()!=ROOT.resolve():missing.append('git_identity')
    if (ROOT/'candidate-source.json').exists():
        source=json.loads((ROOT/'candidate-source.json').read_text())
        if source.get('sourceStatus')!='published-immutable-release':missing.append('published_source_identity')
    return {'ready':not missing,'missing':missing,'published':False,'automaticPublish':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('report',type=Path)
    args=parser.parse_args();result=check(json.loads(args.report.read_text()))
    print(json.dumps(result,ensure_ascii=False));raise SystemExit(0 if result['ready'] else 1)
