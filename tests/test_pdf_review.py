import importlib.util
import tempfile
import unittest
from pathlib import Path
from audit import bind_fact_sources, digest
from bjx import run
from research import facts


@unittest.skipUnless(importlib.util.find_spec('pypdf'), 'optional pypdf not installed')
class PDFReviewTests(unittest.TestCase):
    def pdf(self, path, text=None):
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
        writer = PdfWriter()
        page = writer.add_blank_page(width=400, height=400)
        if text:
            font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
            page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
            stream = DecodedStreamObject()
            stream.set_data(f'BT /F1 12 Tf 10 300 Td ({text}) Tj ET'.encode('ascii'))
            page[NameObject('/Contents')] = stream
        with path.open('wb') as handle:
            writer.write(handle)

    def test_pdf_difference_is_page_located_and_not_semantic_certification(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp)/'a.pdf', Path(tmp)/'b.pdf'
            self.pdf(a, 'DEMO 920001 price 18')
            self.pdf(b, 'DEMO 920001 price 19')
            result, artifacts = run('compare-pdf', dict(before=str(a), after=str(b), issuer_name='DEMO', security='920001'))
            self.assertEqual(len(result['changes']), 1)
            self.assertEqual(result['changes'][0]['before'][0]['page'], 1)
            self.assertFalse(result['semanticReviewComplete'])
            self.assertEqual(result['beforeHash'], digest(artifacts['before.pdf']))

    def test_blank_scanned_page_and_wrong_issuer_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp)/'a.pdf', Path(tmp)/'b.pdf'
            self.pdf(a, 'DEMO 920001 price 18')
            self.pdf(b)
            spec = dict(before=str(a), after=str(b), issuer_name='DEMO', security='920001')
            with self.assertRaises(ValueError):
                run('compare-pdf', spec)
            self.pdf(b, 'OTHER 920002 price 19')
            with self.assertRaises(ValueError):
                run('compare-pdf', spec)


class FactBindingTests(unittest.TestCase):
    def test_original_hash_binds_bytes_without_resolving_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            blob = b'%PDF-1.4\nteaching bytes only'
            path = Path(tmp)/'a.pdf'
            path.write_bytes(blob)
            spec = dict(security='DEMO', rule_version='teaching', source_files=[dict(id='original', path=str(path),
                        sha256=digest(blob), url='https://www.bse.cn/test.pdf')], fields={'price': [dict(
                        value=18, unit='CNY/share', basis='original', source='https://www.bse.cn/test.pdf',
                        document_date='2026-10-09', retrieved_at='2026-10-09T00:00:00+08:00', locator='page 1',
                        source_id='original', document_sha256=digest(blob))]})
            result, artifacts = bind_fact_sources(spec, facts(spec))
            self.assertEqual(artifacts['original-000.pdf'], blob)
            self.assertIsNone(result['fields']['price']['resolved_value'])
            self.assertEqual(result['source_bindings']['original']['status'], 'bytes_bound_not_verified')
            spec['source_files'][0]['sha256'] = '0'*64
            with self.assertRaises(ValueError):
                bind_fact_sources(spec, facts(spec))

    def test_unbound_candidate_hash_rejected(self):
        spec = dict(security='DEMO', rule_version='teaching', fields={'price': [dict(
                    value=18, unit='CNY', basis='assumption', source='teaching', document_sha256='0'*64)]})
        with self.assertRaises(ValueError):
            bind_fact_sources(spec, facts(spec))


if __name__ == '__main__':
    unittest.main()
