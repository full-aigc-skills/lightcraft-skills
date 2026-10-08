"""从唯一维护源生成六份自包含运行资源；--check 只检查漂移。"""
import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def generate(check=False):
    files = sorted(p for p in (ROOT / 'runtime').iterdir() if p.is_file())
    drift = []
    for name in json.loads((ROOT / 'skill-suite.json').read_text())['skills']:
        destination = ROOT / 'skills' / name / 'scripts'
        for source in files:
            target = destination / source.name
            if target.is_symlink():
                raise ValueError('generated_resource_symlink: ' + str(target))
            if not target.exists() or target.read_bytes() != source.read_bytes():
                drift.append(str(target.relative_to(ROOT)))
                if not check:
                    destination.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
    if check and drift:
        raise ValueError('generated_resource_drift: ' + ', '.join(drift))
    return {'resources': len(files), 'changed': len(drift), 'check': check}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    print(json.dumps(generate(parser.parse_args().check)))
