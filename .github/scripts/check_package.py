"""Check an independently extracted Git archive, without site packages or user data."""
import subprocess
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    with tempfile.TemporaryDirectory(prefix='bjx-package-') as temp:
        temp = Path(temp)
        archive = temp / 'package.zip'
        subprocess.run(['git', 'archive', '--format=zip', '--output', str(archive), 'HEAD'], cwd=ROOT, check=True)
        target = temp / 'extracted'
        target.mkdir()
        with zipfile.ZipFile(archive) as zipped:
            for name in zipped.namelist():
                if not (target.resolve() / name).resolve().is_relative_to(target.resolve()):
                    raise ValueError('Unsafe archive path')
                if name.startswith('local-data/') or name.endswith('.env'):
                    raise ValueError('Private files included in release archive')
            zipped.extractall(target)
        for filename in ('vendor/announcement_versions.py', 'vendor/compare_original_versions.py',
                         'licenses/research-workbench-MIT.txt', 'THIRD_PARTY_NOTICES.md'):
            if not (target / filename).is_file():
                raise ValueError('Dependency/attribution missing from package')
        for mode, example in [('scenarios', 'scenarios'), ('facts', 'facts'), ('ledger', 'ledger'), ('versions', 'versions'), ('compare-cash', 'compare-cash'), ('freeze','freeze'), ('archive','archive'),('public-sample','public-sample')]:
            destination = temp / ('report-' + mode)
            subprocess.run([sys.executable, '-S', 'bjx.py', mode, f'examples/{example}.json',
                            '--out-dir', str(destination)], cwd=target, check=True)
            subprocess.run([sys.executable, '-S', 'bjx.py', 'verify', str(destination)], cwd=target, check=True)
        destination=temp/'report-calendar'
        subprocess.run([sys.executable, '-S', 'bjx.py', 'calendar', 'data/bse-2026-schedule.json', '--out-dir', str(destination)],cwd=target,check=True)
        subprocess.run([sys.executable, '-S', 'bjx.py', 'verify', str(destination)],cwd=target,check=True)
        review_input=temp/'review-input.json'
        review_input.write_text(json.dumps(dict(frozen_bundle=str(temp/'report-freeze'),actual_bundle=str(temp/'report-archive'),comparison_values={'issue_price':{'value':18,'unit':'CNY/share'}})),encoding='utf-8')
        destination=temp/'report-review'
        subprocess.run([sys.executable,'-S','bjx.py','review',str(review_input),'--out-dir',str(destination)],cwd=target,check=True)
        subprocess.run([sys.executable,'-S','bjx.py','verify',str(destination)],cwd=target,check=True)
    print('Portable package examples and content binding passed; no source or visual certification.')


if __name__ == '__main__':
    main()
