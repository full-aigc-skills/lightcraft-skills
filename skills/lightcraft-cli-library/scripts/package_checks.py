"""分发资源与 Markdown 引用校验；不启动原生或宿主。"""
from pathlib import Path
import re


def markdown(root):
    root=Path(root);count=0
    files=list((root/'skills').rglob('*.md'))
    files += list((root/'docs').glob('*.md')) + list(root.glob('README*.md')) + list(root.glob('THIRD_PARTY*.md'))
    for path in files:
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            if re.match(r'[a-z]+://|#',target):continue
            relative=target.split('#')[0]
            resolved=(path.parent/relative).resolve()
            if not resolved.exists():raise ValueError('markdown_reference_missing: '+str(path)+' -> '+target)
            if path.is_relative_to(root/'skills'):
                own=root/'skills'/path.relative_to(root/'skills').parts[0]
                if not resolved.is_relative_to(own.resolve()):raise ValueError('cross_skill_relative_reference: '+str(path))
            count+=1
    return count


def skills(root, expected, canonical=None):
    root=Path(root)
    actual=sorted(p.name for p in (root/'skills').iterdir() if p.is_dir())
    if actual!=sorted(expected):raise ValueError('skill_set_mismatch')
    for name in expected:
        directory=root/'skills'/name
        if any(p.is_symlink() for p in directory.rglob('*')) or directory.is_symlink():raise ValueError('skill_symlink')
        text=(directory/'SKILL.md').read_text()
        if not text.startswith('---\n') or text.count('\n---\n')!=1:raise ValueError('skill_frontmatter_invalid')
        front=text.split('---',2)[1]
        keys=re.findall(r'^(\w+):',front,re.M)
        if len(keys)!=len(set(keys)) or 'name: '+name+'\n' not in front or not re.search(r'^description: .+',front,re.M):
            raise ValueError('skill_frontmatter_invalid')
        if len(text.splitlines())>=500:raise ValueError('skill_too_long')
        for required in ['references/runtime.md','references/workflow.md','examples/scenarios.md','agents/openai.yaml']:
            if not (directory/required).is_file():raise ValueError('skill_resource_missing: '+name+'/'+required)
        if canonical:
            for source in Path(canonical).iterdir():
                if source.is_file() and (directory/'scripts'/source.name).read_bytes()!=source.read_bytes():raise ValueError('independent_resource_drift')
    return {'skills':len(expected),'markdownReferences':markdown(root),'structure':'PASS'}
