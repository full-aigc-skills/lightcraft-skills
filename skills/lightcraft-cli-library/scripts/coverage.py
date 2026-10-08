"""把能力快照映射到六技能所有者；目录覆盖不是运行验收。"""
import argparse
import hashlib
import json
from pathlib import Path


def report(snapshot, tested=None):
    groups={'library.':'lightcraft-cli-library','photo.':'lightcraft-cli-library','catalog.':'lightcraft-cli-library',
            'develop.':'lightcraft-cli-develop','preset.':'lightcraft-cli-develop','curve.':'lightcraft-cli-develop',
            'edit.':'lightcraft-cli-develop','export.':'lightcraft-cli-export','app.export':'lightcraft-cli-export',
            'engine.':'lightcraft-cli','ui.':'lightcraft-cli'}
    observed=[]
    tested=tested or {}
    for row in snapshot['commands']:
        identifier=row['id']
        owner=next((owner for prefix,owner in groups.items() if identifier.startswith(prefix)),None)
        observed.append({'command':identifier,'owner':owner,'mode':snapshot.get('mode'),
                         'sideEffects':'native-guidance-required','example':'examples/scenarios.md' if owner else None,
                         'verification':tested.get(identifier,'NOT_RUN'),'coverage':'ASSIGNED' if owner else 'UNASSIGNED'})
    return {'schemaVersion':1,'snapshotSha256':hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest(),
            'binaryIdentity':snapshot.get('executableIdentity'),'mode':snapshot.get('mode'),'commands':observed,
            'uncovered':[r['command'] for r in observed if not r['owner']],'runtimeAcceptance':'NOT_IMPLIED'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('snapshot',type=Path)
    args=parser.parse_args();print(json.dumps(report(json.loads(args.snapshot.read_text())),ensure_ascii=False,indent=2))
