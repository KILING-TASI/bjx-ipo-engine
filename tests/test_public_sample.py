import copy
import json
import tempfile
import unittest
from pathlib import Path
from public_sample import replay_sample
from audit import load

ROOT=Path(__file__).resolve().parents[1]


class PublicSampleTests(unittest.TestCase):
    def setUp(self):
        self.spec=load(ROOT/'examples/public-sample.json')
        self.spec['sample']=str(ROOT/self.spec['sample'])
        self.spec['calendar_schedule']=str(ROOT/self.spec['calendar_schedule'])

    def test_public_rate_reconciliation_and_hypothetical_occupancy(self):
        r,a=replay_sample(self.spec)
        self.assertEqual(r['source_verification'],'saved_review_record_not_rechecked')
        self.assertEqual(r['proportional_shares'],200)
        self.assertEqual(r['frozen_amount'],'9999288.00')
        self.assertEqual(r['individual_actual_allocation'],'unknown')
        self.assertEqual(r['opportunity_cost_assumption']['retained_principal'],'2808.00')
        self.assertEqual(r['opportunity_cost_assumption']['capital_days'],'20032272.00')
        self.assertEqual(a,{})

    def test_missing_refund_cash_assumption_does_not_infer_T_plus_two(self):
        self.spec.pop('refund_available_date_assumption')
        r,_=replay_sample(self.spec)
        self.assertIsNone(r['cash_reconstruction'])
        self.assertIsNone(r['opportunity_cost_assumption'])

    def test_refund_before_announced_date_is_rejected(self):
        self.spec['refund_available_date_assumption']='2026-03-17'
        with self.assertRaises(ValueError):replay_sample(self.spec)

    def test_modified_review_value_and_unit_are_not_silently_accepted(self):
        sample=load(self.spec['sample'])
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'changed.json'
            sample['fields']['issue_price']['value']=9
            path.write_text(json.dumps(sample),encoding='utf-8')
            self.spec['sample']=str(path)
            with self.assertRaises(ValueError):replay_sample(self.spec)

    def test_missing_original_or_wrong_original_bytes_fail(self):
        self.spec['source_files']={}
        with self.assertRaises(ValueError):replay_sample(self.spec)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.pdf';path.write_bytes(b'%PDF-1.4 fake')
            self.spec['source_files']={k:str(path) for k in ['offer','result','listing']}
            with self.assertRaises(ValueError):replay_sample(self.spec)

    def test_announced_share_count_and_quoted_precision_must_reconcile(self):
        sample=load(self.spec['sample'])
        sample['fields']['online_issue_shares'].update(value=19793000,text_anchor='19,793,000')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'changed.json';path.write_text(json.dumps(sample),encoding='utf-8')
            self.spec['sample']=str(path)
            with self.assertRaises(ValueError):replay_sample(self.spec)


if __name__=='__main__':unittest.main()
