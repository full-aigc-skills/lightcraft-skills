"""独立技能、确定性运行资源与分发材料校验。"""
import importlib.util
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def validate():
    suite=json.loads((ROOT/'skill-suite.json').read_text(encoding='utf-8'))
    spec=importlib.util.spec_from_file_location('checks',ROOT/'runtime/package_checks.py')
    checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
    result=checks.skills(ROOT,suite['skills'],ROOT/'runtime')
    for name in ['LICENSE','licenses/Apache-2.0.txt','THIRD_PARTY_NOTICES.md']:
        if not (ROOT/name).is_file():raise ValueError('distribution_material_missing: '+name)
    lock=json.loads((ROOT/'runtime/runtime.lock.json').read_text(encoding='utf-8'))
    if lock['artifact']!='lightcraft-cli' or lock['resolvedVersion']!=suite['nativeVersion']:raise ValueError('runtime_identity_mismatch')
    for item in lock['artifacts'].values():
        for key in ('archiveSha256','binarySha256'):
            if not re.fullmatch('[0-9a-f]{64}',item[key]):raise ValueError('invalid_checksum')
    return dict(result,domain='lightcraft',nativeInstallation='NOT_RUN',modelDispatch='NOT_RUN')


if __name__=='__main__':print(json.dumps(validate(),ensure_ascii=True))
