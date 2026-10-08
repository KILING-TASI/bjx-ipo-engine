import copy
import unittest
from research import Calendar, facts, ledger, repo_interest


EV = {'basis': 'assumption', 'source': 'teaching example only'}
CAL = {'source': 'explicit teaching calendar, not an official calendar', 'basis': 'assumption',
       'coverage_start': '2026-10-12', 'coverage_end': '2026-10-20',
       'trading_dates': ['2026-10-12', '2026-10-13', '2026-10-14', '2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20']}


def event(identity, day, kind, amount, instrument='A', **extra):
    return dict(id=identity, date=day, kind=kind, amount=amount, instrument=instrument, evidence=EV, **extra)


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.data = dict(initial_cash=1000, calendar=CAL, events=[
            event('buy', '2026-10-12', 'freeze', 1000),
            event('refund', '2026-10-14', 'refund', 800),
            event('sale', '2026-10-20', 'sale', 250, principal_released=200)])

    def test_cash_conservation_and_retained_principal(self):
        out = ledger(self.data)
        self.assertTrue(out['executable'])
        self.assertEqual(out['events'][1]['ipo_principal'], 200)
        self.assertEqual(out['final_available_cash'], 1050)
        self.assertEqual(out['outstanding_ipo_principal'], 0)

    def test_same_day_unknown_release_cannot_fund_order(self):
        self.data['events'].insert(2, event('second', '2026-10-14', 'freeze', 800, 'B'))
        out = ledger(self.data)
        self.assertFalse(out['executable'])
        self.assertEqual(out['conflicts'][0]['shortage'], 800)
        self.assertEqual(len(out['events']), 1)

    def test_verified_order_can_reuse_release(self):
        self.data['events'][1].update(order=0, timing_evidence=EV)
        self.data['events'].insert(2, event('second', '2026-10-14', 'freeze', 800, 'B', order=1, timing_evidence=EV))
        self.assertTrue(ledger(self.data)['executable'])

    def test_partial_timing_is_conservative(self):
        self.data['events'][1].update(order=0, timing_evidence=EV)
        self.data['events'].insert(2, event('second', '2026-10-14', 'freeze', 800, 'B'))
        self.assertFalse(ledger(self.data)['executable'])

    def test_same_day_orders_checked_as_one_group(self):
        self.data['events'] = [event('x', '2026-10-12', 'freeze', 700), event('y', '2026-10-12', 'freeze', 400, 'B')]
        out = ledger(self.data)
        self.assertFalse(out['executable'])
        self.assertEqual(out['events'], [])
        self.assertEqual(out['final_available_cash'], 1000)

    def test_impossible_release_fails(self):
        self.data['events'][1]['amount'] = 1001
        with self.assertRaises(ValueError):
            ledger(self.data)

    def test_total_loss_sale_releases_principal(self):
        self.data['events'][-1]['amount'] = 0
        out = ledger(self.data)
        self.assertEqual(out['outstanding_ipo_principal'], 0)
        self.assertEqual(out['final_available_cash'], 800)

    def test_missing_calendar_and_nontrading_day_fail(self):
        for day in ['2026-10-17', '2026-10-21']:
            d = copy.deepcopy(self.data)
            d['events'][-1]['date'] = day
            with self.subTest(day=day), self.assertRaises(ValueError):
                ledger(d)

    def test_repo_actual_days_and_cash_events(self):
        trade = dict(principal=1000, annual_rate=.0365, fee=.01, trade_date='2026-10-15',
                     principal_available_date='2026-10-16', first_settlement_date='2026-10-16',
                     maturity_settlement_date='2026-10-19', evidence=EV)
        result = repo_interest(trade, Calendar(CAL))
        self.assertEqual(result['interest_days'], 3)
        self.assertAlmostEqual(result['net_interest'], .29)
        d = dict(initial_cash=1000, calendar=CAL, events=[
            event('open', '2026-10-15', 'repo_open', 1000, 'R'),
            event('return', '2026-10-16', 'repo_principal', 1000, 'R'),
            event('interest', '2026-10-19', 'repo_interest', .29, 'R')])
        self.assertAlmostEqual(ledger(d)['final_available_cash'], 1000.29)

    def test_fact_conflicts_missing_and_unverified(self):
        c = dict(value=18, unit='CNY', **EV)
        data = dict(security='DEMO', rule_version='example', required_fields=['Q'],
                    fields={'price': [c, dict(c, value=19)], 'date': [dict(c, value='2026-10-12', unit='date')]})
        out = facts(data)['fields']
        self.assertEqual(out['price']['status'], 'conflict')
        self.assertEqual(out['Q']['status'], 'missing')
        self.assertEqual(out['date']['status'], 'recorded_unverified')
        self.assertIsNone(out['date']['resolved_value'])

    def test_original_source_requires_provenance(self):
        data = dict(security='DEMO', rule_version='example', fields={
            'price': [dict(value=18, unit='CNY', basis='original', source='https://example.com/a.pdf')]})
        with self.assertRaises(KeyError):
            facts(data)


if __name__ == '__main__':
    unittest.main()
