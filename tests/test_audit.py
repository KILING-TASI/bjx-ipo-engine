import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from audit import (MAX_BYTES, SafeRedirect, capture, digest, loads, publish, safe_url, verify)
from bjx import main, run
from engine import evaluate

ROOT = Path(__file__).resolve().parents[1]


class Response(io.BytesIO):
    headers = {'Content-Type': 'application/pdf'}

    def geturl(self):
        return 'https://www.bse.cn/test.pdf'


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT / 'examples/scenarios.json').read_text(encoding='utf-8'))

    def test_strict_json_rejects_duplicate_and_nonfinite(self):
        for payload in ('{"capital":1,"capital":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e9999}'):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                loads(payload)

    def test_bundle_verification_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'report'
            publish(out, 'scenarios', self.spec, evaluate(self.spec))
            self.assertEqual(verify(out)['status'], 'content_matches_manifest')
            manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['stages']['source_verification'], 'not_performed')
            (out / 'report.md').write_text('changed', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Content differs'):
                verify(out)

    def test_report_is_content_bound_and_escaped(self):
        self.spec['scenarios'][0]['id'] = '<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'report'
            publish(out, 'scenarios', self.spec, evaluate(self.spec))
            page = (out / 'report.html').read_text(encoding='utf-8')
            self.assertNotIn('<script>', page)
            self.assertIn('&lt;script&gt;', page)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'report'
            out.mkdir()
            (out / 'mine.txt').write_text('keep')
            with self.assertRaises(FileExistsError):
                publish(out, 'scenarios', self.spec, evaluate(self.spec))
            self.assertEqual((out / 'mine.txt').read_text(), 'keep')

    def test_manifest_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'report'
            publish(out, 'scenarios', self.spec, evaluate(self.spec))
            path = out / 'manifest.json'
            manifest = json.loads(path.read_text())
            manifest['files']['../secret.txt'] = dict(sha256='x', size=1)
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                verify(out)

    def test_unregistered_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'report'
            publish(out, 'scenarios', self.spec, evaluate(self.spec))
            (out / 'extra.txt').write_text('unknown')
            with self.assertRaisesRegex(ValueError, 'Unregistered'):
                verify(out)

    def test_capture_is_explicit_and_allowlisted(self):
        with self.assertRaisesRegex(ValueError, '--online'):
            run('capture', {'url': 'https://www.bse.cn/test.pdf'})
        for url in ['http://www.bse.cn/a', 'https://localhost/a', 'https://www.bse.cn.evil.com/a',
                    'https://user:password@www.bse.cn/a', 'https://www.bse.cn:444/a', 'https://www.bse.cn/a\n']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                safe_url(url)
        with self.assertRaises(ValueError):
            SafeRedirect().redirect_request(None, None, 302, '', {}, 'https://127.0.0.1/')

    def test_capture_preserves_bytes_and_expected_hash(self):
        blob = b'%PDF-1.4\nteaching'
        with patch('audit.build_opener') as opener:
            opener.return_value.open.return_value = Response(blob)
            result, artifacts = capture(dict(url='https://www.bse.cn/test.pdf', expected_sha256=digest(blob)))
        self.assertEqual(artifacts['source.pdf'], blob)
        self.assertEqual(result['sha256'], digest(blob))
        self.assertEqual(result['source_verification'], 'not_performed')
        with patch('audit.build_opener') as opener:
            opener.return_value.open.return_value = Response(blob)
            with self.assertRaisesRegex(ValueError, 'hash changed'):
                capture(dict(url='https://www.bse.cn/test.pdf', expected_sha256='0'*64))

    def test_pdf_error_page_and_source_size_rejected(self):
        for blob in (b'<html>denied</html>', b'x'*(MAX_BYTES+1), b''):
            with patch('audit.build_opener') as opener:
                opener.return_value.open.return_value = Response(blob)
                with self.assertRaises(ValueError):
                    capture(dict(url='https://www.bse.cn/test.pdf'))

    def test_failed_workflow_preserves_failure_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'input.json'
            source.write_text('{"capital":1}', encoding='utf-8')
            out = Path(tmp) / 'failure'
            with patch('sys.stdout', new_callable=io.StringIO):
                code = main(['scenarios', str(source), '--out-dir', str(out)])
            self.assertEqual(code, 2)
            self.assertEqual(verify(out)['status'], 'content_matches_manifest')
            manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['status'], 'blocked')
            self.assertEqual(manifest['stages']['calculation'], 'not_performed')

    def test_title_lead_never_confirms_supersession(self):
        spec = json.loads((ROOT / 'examples/versions.json').read_text(encoding='utf-8'))
        result, _ = run('versions', spec)
        self.assertEqual(result['status'], 'needs-body-review')
        self.assertFalse(result['groups'][0]['supersessionConfirmed'])
        spec['documents'][0]['security'] = 'OTHER'
        with self.assertRaises(ValueError):
            run('versions', spec)

    def test_empty_title_search_does_not_certify_no_correction(self):
        result, _ = run('versions', {'security': 'DEMO-A', 'documents': []})
        self.assertIn('absence is not proof', result['scope'])


if __name__ == '__main__':
    unittest.main()
