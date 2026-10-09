import copy
import json
import tempfile
import unittest
from pathlib import Path
from comparison import compare_cash
from audit import publish, verify
from research import ledger

ROOT = Path(__file__).resolve().parents[1]


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT/'examples/compare-cash.json').read_text(encoding='utf-8'))

    def test_same_period_cash_profit_and_locked_capital_days(self):
        result = compare_cash(self.spec)
        self.assertEqual(result['comparison_status'], 'comparable_declared_cash')
        first, second = result['plans']
        self.assertEqual(first['realized_cash_profit'], '50.00')
        self.assertEqual(second['realized_cash_profit'], '4.90')
        self.assertEqual(result['first_minus_second_cash_profit'], '45.10')
        self.assertEqual(first['locked_capital_days'], '3200.00')
        self.assertEqual(second['locked_capital_days'], '1000.00')
        self.assertEqual(second['paid_separate_fees'], '0.10')
        self.assertEqual(result['calendar_days'], 8)

    def test_unsettled_principal_is_not_a_loss_or_rank(self):
        self.spec['plans'][0]['events'].pop()
        result = compare_cash(self.spec)
        self.assertEqual(result['comparison_status'], 'incomplete_not_ranked')
        self.assertEqual(result['plans'][0]['status'], 'unsettled_principal')
        self.assertIsNone(result['plans'][0]['realized_cash_profit'])
        self.assertIsNone(result['first_minus_second_cash_profit'])
        self.assertEqual(result['plans'][0]['locked_capital_days'], '3200.00')

    def test_conflict_has_no_period_end_or_capital_day_estimate(self):
        self.spec['plans'][0]['events'][0]['amount'] = '1001.00'
        result = compare_cash(self.spec)
        first = result['plans'][0]
        self.assertEqual(first['status'], 'cash_conflict')
        self.assertIsNone(first['closing_cash'])
        self.assertIsNone(first['locked_capital_days'])
        self.assertIsNone(result['first_minus_second_cash_profit'])

    def test_out_of_period_and_calendar_shortfall_rejected(self):
        for key, value in [('start', '2026-10-13'), ('end', '2026-10-21')]:
            spec = copy.deepcopy(self.spec)
            spec[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                compare_cash(spec)

    def test_injected_costs_currency_or_plan_capital_rejected(self):
        for field, value in [('annual_cash_cost_rate', .02), ('currency', 'USD')]:
            spec = copy.deepcopy(self.spec)
            spec[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                compare_cash(spec)
        self.spec['plans'][0]['initial_cash'] = 2000
        with self.assertRaises(ValueError):
            compare_cash(self.spec)

    def test_losses_and_no_income_are_preserved(self):
        self.spec['plans'][0]['events'][-1]['amount'] = '0.00'
        self.spec['plans'][1]['events'] = []
        result = compare_cash(self.spec)
        self.assertEqual(result['plans'][0]['realized_cash_profit'], '-200.00')
        self.assertEqual(result['plans'][1]['realized_cash_profit'], '0.00')
        self.assertEqual(result['first_minus_second_cash_profit'], '-200.00')

    def test_fee_cash_constraint_is_checked_before_release(self):
        spec = dict(initial_cash='1000.00', calendar=self.spec['calendar'], events=copy.deepcopy(self.spec['plans'][1]['events']))
        spec['events'][-1]['date'] = '2026-10-12'
        self.assertFalse(ledger(spec)['executable'])

    def test_decimal_amounts_and_fees_do_not_accumulate_binary_rounding(self):
        self.spec['initial_cash'] = '1000.10'
        result = compare_cash(self.spec)
        self.assertEqual(result['plans'][1]['closing_cash'], '1005.00')
        self.assertEqual(result['plans'][1]['account_period_cash_return'], '0.004899510048995100489951004900')

    def test_comparison_bundle_is_bound_with_incomplete_status_in_report(self):
        self.spec['plans'][0]['events'].pop()
        result = compare_cash(self.spec)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'report'
            publish(out, 'compare-cash', self.spec, result)
            self.assertEqual(verify(out)['status'], 'content_matches_manifest')
            text = (out/'report.md').read_text(encoding='utf-8')
            self.assertIn('不比较盈亏优劣', text)


if __name__ == '__main__':
    unittest.main()
