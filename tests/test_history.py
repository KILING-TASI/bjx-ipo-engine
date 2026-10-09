import copy
import json
import tempfile
import unittest
from pathlib import Path
from history import archive, freeze, review
from audit import publish

ROOT=Path(__file__).resolve().parents[1]


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.f=json.loads((ROOT/'examples/freeze.json').read_text(encoding='utf-8'))
        self.a=json.loads((ROOT/'examples/archive.json').read_text(encoding='utf-8'))

    def test_backfilled_assumptions_are_not_genuine_predictions(self):
        r=freeze(self.f)
        self.assertEqual(r['record_kind'],'historical_reconstruction')
        self.assertFalse(r['externally_timestamped'])

    def test_source_information_after_cutoff_and_naive_clock_fail(self):
        for stamp in ['2026-01-11T00:00:00+08:00','2026-01-09T00:00:00']:
            s=copy.deepcopy(self.f);s['information_sources'][0]['available_at']=stamp
            with self.subTest(stamp=stamp),self.assertRaises(ValueError):freeze(s)

    def test_future_declared_information_cutoff_fails(self):
        self.f['information_cutoff']='2099-01-01T00:00:00+08:00'
        with self.assertRaises(ValueError):freeze(self.f)

    def test_conflict_missing_and_refund_boundary_preserved(self):
        self.a['fields']['issue_price'].append(dict(self.a['fields']['issue_price'][0],value=19))
        r,_=archive(self.a)
        self.assertEqual(r['fields']['issue_price']['status'],'conflict')
        self.assertEqual(r['fields']['listing_date']['status'],'missing')
        self.assertEqual(r['residual_allocation'],'unknown')
        self.assertIn('not broker',r['refund_boundary'])

    def test_public_claims_require_bound_original_and_accounts_remain_paused(self):
        self.a['input_kind']='public_disclosure'
        with self.assertRaises(ValueError):archive(self.a)
        self.a['input_kind']='account'
        with self.assertRaises(ValueError):archive(self.a)

    def test_separate_review_does_not_change_freeze_and_checks_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            f,a=Path(tmp)/'frozen',Path(tmp)/'actual'
            publish(f,'freeze',self.f,freeze(self.f))
            r,attachments=archive(self.a);publish(a,'archive',self.a,r,artifacts=attachments)
            before=(f/'result.json').read_bytes()
            spec=dict(frozen_bundle=str(f),actual_bundle=str(a),comparison_values={
                'issue_price':{'value':18,'unit':'CNY/share'},
                'online_allocation_rate':{'value':.00033,'unit':'fraction'}})
            out=review(spec)
            self.assertAlmostEqual(out['comparisons'][1]['signed_error_frozen_minus_actual'],.00003)
            self.assertEqual((f/'result.json').read_bytes(),before)
            spec['comparison_values']['issue_price']['value']=17
            with self.assertRaises(ValueError):review(spec)
            (a/'result.json').write_text('changed')
            with self.assertRaises(ValueError):review(spec)

    def test_missing_actual_rate_stays_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            f,a=Path(tmp)/'f',Path(tmp)/'a'
            publish(f,'freeze',self.f,freeze(self.f))
            self.a['fields']['online_allocation_rate']=[]
            r,_=archive(self.a);publish(a,'archive',self.a,r)
            out=review(dict(frozen_bundle=str(f),actual_bundle=str(a),comparison_values={'online_allocation_rate':{'value':.00033,'unit':'fraction'}}))
            self.assertIsNone(out['comparisons'][0]['signed_error_frozen_minus_actual'])

    def test_multi_issue_cash_and_frozen_opportunity_rate_are_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            f,a=Path(tmp)/'f',Path(tmp)/'a'
            publish(f,'freeze',self.f,freeze(self.f))
            r,_=archive(self.a);publish(a,'archive',self.a,r)
            cash=json.loads((ROOT/'examples/compare-cash.json').read_text(encoding='utf-8'))
            spec=dict(frozen_bundle=str(f),actual_bundle=str(a),comparison_values={},cash_basis='teaching',cash_comparison=cash,opportunity_cost_rate=.02)
            out=review(spec)
            self.assertEqual(out['cash_reconstruction']['first_minus_second_cash_profit'],'45.10')
            self.assertAlmostEqual(float(out['opportunity_cost_sensitivity'][0]['opportunity_cost']),3200*.02/365)
            spec['opportunity_cost_rate']=.03
            with self.assertRaises(ValueError):review(spec)


if __name__=='__main__':unittest.main()
