import json
import unittest
from pathlib import Path
from engine import evaluate
from audit import report


class SensitivityTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads((Path(__file__).resolve().parents[1]/'examples/scenarios.json').read_text(encoding='utf-8'))

    def test_breakeven_solves_both_commission_branches(self):
        for rate, minimum in [(0.00025,5),(.01,0)]:
            self.spec['fees'].update(commission_rate=rate,minimum_commission=minimum)
            row=evaluate(self.spec)['scenarios'][1]
            self.spec['scenarios'][1]['listing_return']=row['breakeven_listing_return']
            out=evaluate(self.spec)['scenarios'][1]
            self.assertAlmostEqual(out['net_profit'],0,places=8)

    def test_residual_allocation_can_increase_loss_and_is_not_in_expectation(self):
        result=evaluate(self.spec)
        low=result['scenarios'][0]
        self.assertIsNone(low['breakeven_listing_return'])
        extra=low['residual_extra_100_share_sensitivity']
        self.assertEqual(extra['assumed_total_shares'],100)
        self.assertLess(extra['net_profit'],low['net_profit'])
        self.assertGreater(extra['cash_cost'],low['cash_cost'])
        self.assertAlmostEqual(result['weighted']['expected_net_profit'],2140.8233216438357)

    def test_exact_allocation_and_no_subscription_have_no_residual_case(self):
        self.spec['scenarios'][1]['allocation_rate']=1
        self.assertIsNone(evaluate(self.spec)['scenarios'][1]['residual_extra_100_share_sensitivity'])
        self.spec['budget']=0
        self.assertTrue(all(r['residual_extra_100_share_sensitivity'] is None for r in evaluate(self.spec)['scenarios']))

    def test_fee_assumption_with_no_finite_break_even_rejected(self):
        self.spec['fees']['commission_rate']=1
        with self.assertRaises(ValueError):evaluate(self.spec)

    def test_readable_tables_are_escaped_and_preserve_literal_pipe(self):
        self.spec['scenarios'][0]['id']='<script>|demo'
        md,page=report('scenarios',evaluate(self.spec),'completed_with_limits')
        page=page.decode('utf-8')
        self.assertIn('<table>',page)
        self.assertNotIn('<script>',page)
        self.assertIn('&lt;script&gt;|demo',page)
        self.assertIn('盈亏平衡',page)
        self.assertIn('发行价假设',page)


if __name__=='__main__':unittest.main()
