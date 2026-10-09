"""Check packaged Markdown file links and versions, without probing external services."""
import re
from pathlib import Path
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[2]


def main():
    errors=[];count=0
    for path in sorted(ROOT.rglob('*.md')):
        if any(part in ('.git','local-data','__pycache__') for part in path.relative_to(ROOT).parts):continue
        content=path.read_text(encoding='utf-8')
        if content.count('```')%2:errors.append(f'Unclosed code fence: {path.relative_to(ROOT)}')
        body=re.sub(r'```.*?```','',content,flags=re.S)
        for target in re.findall(r'\]\(([^)]+)\)',body):
            target=target.strip().strip('<>')
            if target.startswith(('https://','http://','mailto:','#')):continue
            name=unquote(target.split('#',1)[0])
            if not name:continue
            candidate=(path.parent/name).resolve()
            if not candidate.is_relative_to(ROOT.resolve()) or not candidate.is_file():errors.append(f'Broken/escaping file link: {path.relative_to(ROOT)} -> {target}')
            count+=1
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    method=re.search(r"METHOD_VERSION = '([^']+)'",(ROOT/'audit.py').read_text(encoding='utf-8')).group(1)
    if method not in readme:errors.append('README does not identify current calculation version')
    for filename in ('DISCLAIMER.md','THIRD_PARTY_NOTICES.md','CHANGELOG.md','data/bse-2026-schedule.json','data/public-samples/920188.json'):
        if not (ROOT/filename).is_file():errors.append('Required documentation/resource missing: '+filename)
    if errors:raise ValueError('\n'.join(errors))
    print(f'Markdown file links ({count}), required resources and calculation-version reference passed; external URL/semantic checks not certified.')


if __name__=='__main__':main()
