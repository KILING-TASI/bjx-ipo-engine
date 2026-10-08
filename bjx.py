"""Unified CLI: research packages, source capture, version review and verification."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from audit import MAX_BYTES, bind_fact_sources, capture, load, publish, verify
from engine import evaluate
from research import facts, ledger
from vendor.announcement_versions import version_review


def run(mode, spec, online=False):
    if mode == 'scenarios':
        return evaluate(spec), {}
    if mode == 'ledger':
        return ledger(spec), {}
    if mode == 'facts':
        return bind_fact_sources(spec, facts(spec))
    if mode == 'versions':
        if not isinstance(spec.get('security'), str) or not spec['security'].strip():
            raise ValueError('Version review requires a security identity')
        items = spec['documents']
        for item in items:
            for field in ('security', 'title', 'date', 'url'):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise ValueError('Version leads require security, title, date and url')
            if item['security'] != spec['security']:
                raise ValueError('Version leads must refer to one security')
            date.fromisoformat(item['date'])
            parsed = urlsplit(item['url'])
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Version lead URL must be public HTTPS without credentials')
        return version_review(items), {}
    if mode == 'capture':
        if not online:
            raise ValueError('Source capture requires explicit --online')
        return capture(spec)
    if mode == 'compare-pdf':
        if not isinstance(spec.get('issuer_name'), str) or not spec['issuer_name'].strip():
            raise ValueError('Issuer name is required')
        import re
        if not isinstance(spec.get('security'), str) or not re.fullmatch(r'\d{6}', spec['security']):
            raise ValueError('PDF identity requires a six-digit security code')
        # Optional dependency is loaded only for this workflow.
        from vendor.compare_original_versions import compare, extract
        paths = [Path(spec[key]) for key in ('before', 'after')]
        for path in paths:
            if path.stat().st_size > MAX_BYTES:
                raise ValueError('PDF exceeds 10 MiB')
        blobs = [p.read_bytes() for p in paths]
        if not all(b.startswith(b'%PDF-') for b in blobs):
            raise ValueError('Both inputs must be PDF files')
        before = extract(paths[0], spec['issuer_name'], spec['security'])
        after = extract(paths[1], spec['issuer_name'], spec['security'])
        if any(len(record['lines']) > 20000 for record in (before, after)):
            raise ValueError('PDF extracted line limit exceeded')
        from audit import digest
        if [before['sha256'], after['sha256']] != [digest(b) for b in blobs]:
            raise ValueError('PDF changed during extraction')
        return compare(before, after), {'before.pdf': blobs[0], 'after.pdf': blobs[1]}
    raise ValueError('Unknown workflow')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['scenarios', 'ledger', 'facts', 'versions', 'capture', 'compare-pdf', 'verify'])
    parser.add_argument('input', help='input JSON, or research directory for verify')
    parser.add_argument('--out-dir')
    parser.add_argument('--online', action='store_true')
    args = parser.parse_args(argv)
    if args.mode == 'verify':
        if args.out_dir or args.online:
            parser.error('verify accepts only a bundle directory')
        try:
            result = verify(args.input)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(json.dumps({'status': 'failed', 'message': str(exc)}, ensure_ascii=False))
            return 2
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if not args.out_dir:
        parser.error('--out-dir is required and must be new')
    if Path(args.out_dir).exists():
        parser.error('output directory already exists; use a new directory')
    spec = {'input_path': str(args.input), 'input_status': 'not_loaded'}
    status = 'completed_with_limits'
    artifacts = {}
    try:
        if Path(args.input).stat().st_size > MAX_BYTES:
            raise ValueError('Input exceeds 10 MiB')
        spec = load(args.input)
        if not isinstance(spec, dict):
            raise ValueError('Input must be a JSON object')
        result, artifacts = run(args.mode, spec, args.online)
    except (OSError, ValueError, KeyError, TypeError, ImportError, RuntimeError, ArithmeticError) as exc:
        status = 'blocked'
        result = dict(message=str(exc), failure_kind=type(exc).__name__,
                      next_step='核对输入、来源访问及可选依赖；使用新的输出目录重试。缺少PDF组件时安装pypdf。')
    manifest = publish(args.out_dir, args.mode, spec, result, status, artifacts)
    print(json.dumps({'status': status, 'out_dir': args.out_dir, 'method_version': manifest['method_version']}, ensure_ascii=False))
    return 2 if status == 'blocked' else 0


if __name__ == '__main__':
    sys.exit(main())
