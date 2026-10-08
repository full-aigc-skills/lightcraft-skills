"""照片领域结果转换和局部设置约束；不替代原生运行证据。"""
import copy
import math


def import_summary(report, photos):
    """保留导入、重复和失败；照片 ID 到路径来自实际库查询。"""
    if not isinstance(report, dict) or not isinstance(photos, list): raise ValueError('invalid_import_report')
    required = {'imported','duplicates','failed'}
    if not required <= report.keys() or any(not isinstance(report[k], list) for k in required):
        raise ValueError('incomplete_import_report')
    known = {}
    for photo in photos:
        if not isinstance(photo,dict) or 'id' not in photo: continue
        source=photo.get('source')
        source_path=source.get('path') if isinstance(source,dict) and source.get('type')=='file' else None
        path=photo.get('path',source_path)
        if not isinstance(path,str) or not path: continue
        if source_path is not None and source_path!=path: raise ValueError('photo_source_path_conflict')
        if photo['id'] in known: raise ValueError('duplicate_photo_identity')
        known[photo['id']]=dict(photo,path=path)
    ids=list(report['imported']);unresolved_duplicates=[]
    for duplicate in report['duplicates']:
        identifier=duplicate.get('existing',duplicate.get('id')) if isinstance(duplicate,dict) else None
        if type(identifier) is not int: unresolved_duplicates.append(duplicate)
        elif identifier not in ids: ids.append(identifier)
    if any(type(identifier) is not int for identifier in ids):raise ValueError('invalid_import_photo_id')
    unresolved=[identifier for identifier in ids if identifier not in known]
    status='PARTIAL' if report['failed'] else 'IDENTITY_UNCONFIRMED' if unresolved or unresolved_duplicates else 'REPORTED'
    return {'schemaVersion':1,'status':status,
            'imported':report['imported'],'duplicates':report['duplicates'],'failed':report['failed'],
            'photos':[known[i] for i in ids if i in known], 'unresolvedIds':unresolved,'unresolvedDuplicates':unresolved_duplicates,
            'moved':report.get('moved',[]),'kept':report.get('kept',[]),'persistence':'REOPEN_REQUIRED'}


def apply_local_changes(baseline, values, controls):
    """对显式控件应用局部补丁；越界拒绝，不依赖原生静默 clamp。"""
    if not isinstance(baseline,dict) or not isinstance(values,dict) or not values: raise ValueError('settings_patch_invalid')
    index = {r['id']:r for r in controls if isinstance(r,dict) and 'id' in r}
    result = copy.deepcopy(baseline)
    for key,value in values.items():
        control = index.get(key)
        if not control or type(value) not in (int,float) or not math.isfinite(value):
            raise ValueError('unknown_or_invalid_control: '+key)
        if 'min' not in control or 'max' not in control: raise ValueError('control_range_missing')
        if not control['min']<=value<=control['max']: raise ValueError('control_out_of_range: '+key)
        parts=key.split('.'); cursor=result
        for part in parts[:-1]:
            if not isinstance(cursor,dict) or part not in cursor: raise ValueError('baseline_control_missing: '+key)
            cursor=cursor[part]
        if not isinstance(cursor,dict) or parts[-1] not in cursor: raise ValueError('baseline_control_missing: '+key)
        cursor[parts[-1]]=value
    return result


def compare_reopen(before_photos, reopened_photos, expected_settings, reopened_settings):
    """独立会话调用者提供观测；不生成虚假的原生会话记录。"""
    keys=lambda rows:{(p['id'],p['path']) for p in rows}
    return {'schemaVersion':1,'photoIdentity':'PASS' if keys(before_photos)==keys(reopened_photos) else 'FAIL',
            'settings':'PASS' if expected_settings==reopened_settings else 'FAIL',
            'nativeSessionEvidence':'CALLER_MUST_BIND_RECEIPTS'}
