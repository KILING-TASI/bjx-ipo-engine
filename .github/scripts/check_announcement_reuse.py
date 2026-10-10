"""Explicit local selected-announcement acceptance; never downloads or publishes PDFs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
from io import BytesIO


def check(header, blob, historical=False):
    if header['schema'] != 'bjx-announcement-sidecar.v1':
        raise ValueError('Unsupported sidecar version')
    if hashlib.sha256(blob).hexdigest() != header['sha256']:
        raise ValueError('Original file digest mismatch')
    sample = header['native_payload']
    original = sample['documents']['result']
    if (header['sha256'], header['official_url'], header['source_version']['announcement_number']) != (
            original['sha256'], original['url'], original['announcement_number']):
        raise ValueError('Sidecar and native source version conflict')
    if header['publisher'] != sample['issuer_name']:
        raise ValueError('Publisher identity conflict')
    for key, native_key in [('body_date', 'body_date'), ('url_path_date', 'file_path_date'),
                            ('retrieved_at', 'retrieved_at')]:
        if header['times'][key]['value'] != original[native_key]:
            raise ValueError('Sidecar and native time conflict: ' + key)
    for key in ['published_at', 'historical_available_at']:
        record = header['times'][key]
        if record['value'] is not None or not record.get('reason'):
            raise ValueError('Pinned sample has unknown time; unsupported assertion: ' + key)
    if historical and header['times']['historical_available_at']['value'] is None:
        raise ValueError('Historical availability unknown; prospective use rejected')
    from pypdf import PdfReader
    pages = [re.sub(r'\s+', '', page.extract_text() or '')
             for page in PdfReader(BytesIO(blob)).pages]
    opening = ''.join(pages[:5])
    if sample['issuer_name'] not in opening or sample['security'] not in opening:
        raise ValueError('Parsed issuer/security mismatch')
    if header['source_version']['announcement_number'] not in opening:
        raise ValueError('Parsed announcement number mismatch')
    checked = []
    for name, field in sample['fields'].items():
        if field['source_id'] == 'result':
            if field['text_anchor'] not in pages[field['page'] - 1]:
                raise ValueError('Selected semantic anchor missing: ' + name)
            checked.append(name)
    return {'status': 'selected_text_anchors_matched', 'fields': checked,
            'sha256': header['sha256'], 'historical_available_at': None,
            'limits': 'Three result-page anchors only; no new visual, full corrections, account or trusted publication-clock verification'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-file', required=True)
    parser.add_argument('--out-file', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    header_path = root / 'examples/announcement-sidecar.json'
    raw = header_path.read_bytes()
    header = json.loads(raw)
    blob = Path(args.source_file).read_bytes()
    result = check(header, blob)
    assert header['native_payload'] == json.loads((root / 'data/public-samples/920188.json').read_bytes())
    failures = []
    for name in ['tampered_digest', 'version_conflict', 'unknown_historical_time']:
        altered = copy.deepcopy(header)
        if name == 'tampered_digest':
            altered['sha256'] = '0' * 64
        elif name == 'version_conflict':
            altered['source_version']['announcement_number'] = '2026-999'
        try:
            check(altered, blob, historical=name == 'unknown_historical_time')
        except ValueError as exc:
            failures.append({'case': name, 'status': 'rejected', 'reason': str(exc)})
        else:
            raise AssertionError('Negative case accepted: ' + name)
    receipt = {'consumer': 'bjx-selected-issuance-fields',
               'header_sha256': hashlib.sha256(raw).hexdigest(),
               'source_sha256': hashlib.sha256(blob).hexdigest(),
               'parse_library': 'pypdf', 'result': result, 'negative_cases': failures,
               'native_payload_equal': True, 'cross_repository_status': 'pending_external_receipts'}
    with Path(args.out_file).open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print('Selected original parsed; native payload preserved; three negative cases rejected')


if __name__ == '__main__':
    main()
