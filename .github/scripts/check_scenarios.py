"""Actual offline CLI reports with hand-derived expectations; no other repository."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def hashes(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}


def value_at(result, path):
    for part in path.split('.'):
        result = result[int(part)] if isinstance(result, list) else result[part]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--fixture', default='examples/scenario-acceptance.json')
    args = parser.parse_args()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=False)
    fixture = ROOT / args.fixture
    spec = json.loads(fixture.read_bytes())
    receipts = []
    for case in spec['cases']:
        folder = out / case['id']; folder.mkdir()
        source = folder / 'input.json'
        source.write_text(json.dumps(case['input'], ensure_ascii=False, indent=2), encoding='utf-8')
        (folder / 'expected.json').write_text(json.dumps(case['expected'], ensure_ascii=False, indent=2), encoding='utf-8')
        command = [sys.executable, '-S', str(ROOT / 'bjx.py'), case['mode'], str(source),
                   '--out-dir', str(folder / 'report')]
        actual = subprocess.run(command, cwd=ROOT, capture_output=True)
        assert actual.returncode == case['expected_exit'], (case['id'], actual.stderr)
        result = json.loads((folder / 'report/result.json').read_bytes())
        for key, expected in case['expected'].items():
            observed = value_at(result, key)
            if isinstance(expected, float):
                assert math.isclose(observed, expected, rel_tol=1e-10, abs_tol=1e-8), (case['id'], key, observed)
            else:
                assert observed == expected, (case['id'], key, observed)
        if case['id'] == 'residual-unknown':
            assert 'weighted' not in result
            assert any('unknown' in text for text in result['warnings'])
            assert result['scenarios'][0]['residual_extra_100_share_sensitivity'] is not None
        if case['expected_exit']:
            assert result.get('message') and result.get('next_step')
        manifest = json.loads((folder / 'report/manifest.json').read_bytes())
        assert manifest['method_version'] == '0.2.0-alpha.8'
        before = hashes(folder / 'report')
        repeat = subprocess.run(command, cwd=ROOT, capture_output=True)
        assert repeat.returncode != 0 and before == hashes(folder / 'report'), case['id']
        receipts.append({'id': case['id'], 'sample_kind': case['sample_kind'], 'basis': case['basis'],
                         'expected': case['expected'], 'actual_result': result,
                         'exit': actual.returncode, 'command': command,
                         'stdout': actual.stdout.decode('utf-8'),
                         'stderr': actual.stderr.decode('utf-8'),
                         'method_version': manifest['method_version'],
                         'existing_output_rejected_unchanged': True, 'files': before})
    (out / 'acceptance.json').write_text(json.dumps({'schema': spec['schema'],
        'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'real_sample_count': spec['real_sample_count'], 'scope': spec.get('scope'),
        'status': 'passed', 'cases': receipts,
        'limits': 'Declared budgets/cash assumptions; no original PDFs, account, calibrated forecast or visual certification'},
        ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(len(receipts)) + ' hand-derived CLI scenario reports passed; old outputs unchanged')


if __name__ == '__main__':
    main()
