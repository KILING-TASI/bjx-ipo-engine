import copy
import json
import unittest
from pathlib import Path
from engine import evaluate


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).resolve().parents[1] / 'examples/scenarios.json').read_text(encoding='utf-8'))

    def test_zero_allocation_still_costs_money(self):
        row = evaluate(self.data)['scenarios'][0]
        self.assertEqual(row['proportional_shares'], 0)
        self.assertEqual(row['sell_cost'], 0)
        self.assertLess(row['net_profit'], 0)

    def test_joint_weights_and_cash_retention(self):
        out = evaluate(self.data)
        self.assertEqual(out['subscribed_shares'], 444400)
        self.assertAlmostEqual(out['weighted']['expected_proportional_hands'], 1)
        self.assertAlmostEqual(out['weighted']['probability_zero_proportional_hands'], .3)
        row = out['scenarios'][1]
        self.assertAlmostEqual(row['capital_days'], out['frozen_amount']*2 + 1800*6)

    def test_fee_minimum_is_max_not_addition(self):
        row = evaluate(self.data)['scenarios'][1]
        self.assertAlmostEqual(row['sell_cost'], 5 + 3960*.00051)

    def test_exact_lot_boundary(self):
        self.data.update(budget=1800, max_subscription_shares=100)
        self.data['scenarios'] = [dict(id='one', allocation_rate=1, listing_return=0, basis='test')]
        out = evaluate(self.data)
        self.assertEqual(out['scenarios'][0]['proportional_shares'], 100)
        self.assertNotIn('weighted', out)

    def test_invalid_inputs_fail(self):
        for key, value in [('capital', True), ('budget', float('nan')), ('refund_available_date', '2026-10-11')]:
            d = copy.deepcopy(self.data)
            d[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                evaluate(d)
        self.data['scenarios'][0]['probability'] = .1
        with self.assertRaises(ValueError):
            evaluate(self.data)


if __name__ == '__main__':
    unittest.main()
