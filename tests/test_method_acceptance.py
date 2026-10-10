import copy
import json
import unittest
from pathlib import Path
from repo_reference import repo_reference
from research import Calendar, ledger, repo_interest
from engine import evaluate

ROOT = Path(__file__).resolve().parents[1]

class MethodAcceptanceTests(unittest.TestCase):
    def test_declared_zero_fee_and_subcent_interest_can_replay(self):
        spec = json.loads((ROOT/'examples/repo-reference.json').read_text(encoding='utf-8'))
        spec['fee']['principal_rate'] = '0'
        spec['fee']['source'] = 'Explicit teaching waiver, not an unknown fee'
        result = repo_reference(spec)
        out = ledger(dict(initial_cash='100000', calendar=spec['calendar'], events=result['cash_plan']['events']))
        self.assertTrue(out['executable'])
        self.assertEqual(out['final_available_cash_exact'], '100011.44')
        spec['principal'] = '1'
        result = repo_reference(spec)
        out = ledger(dict(initial_cash='1', calendar=spec['calendar'], events=result['cash_plan']['events']))
        self.assertEqual(result['gross_interest_cent'], '0.00')
        self.assertEqual(out['final_available_cash_exact'], '1')

    def test_holiday_interest_and_same_day_cash_do_not_use_nominal_tenor(self):
        calendar = dict(source='https://www.sse.com.cn/disclosure/announcement/general/c/c_20260915_10832273.shtml',
            basis='assumption', coverage_start='2026-09-29', coverage_end='2026-10-09',
            trading_dates=['2026-09-29','2026-09-30','2026-10-08','2026-10-09'])
        trade = dict(principal='100000', annual_rate='0.02', fee='0',trade_date='2026-09-29',
            first_settlement_date='2026-09-30',maturity_settlement_date='2026-10-08',
            principal_available_date='2026-09-30',evidence={'basis':'assumption','source':'Teaching dates and rate; schedule informed by SSE notice'})
        interest = repo_interest(trade, Calendar(calendar))
        self.assertEqual(interest['interest_days'],8)
        self.assertAlmostEqual(interest['gross_interest'],100000*.02*8/365)
        evidence = {'basis':'assumption','source':'Teaching cash events, no actual account order'}
        events = [dict(id='open',instrument='R',date='2026-09-29',kind='repo_open',amount='100000',evidence=evidence),
                  dict(id='return',instrument='R',date='2026-09-30',kind='repo_principal',amount='100000',evidence=evidence),
                  dict(id='next',instrument='IPO',date='2026-09-30',kind='freeze',amount='100000',evidence=evidence)]
        out = ledger(dict(initial_cash='100000',calendar=calendar,events=events))
        self.assertFalse(out['executable'])
        self.assertEqual(out['conflicts'][0]['shortage'],100000)
        for event in events[1:]:
            event['order'] = 0 if event['id']=='return' else 1
            event['timing_evidence'] = evidence
        self.assertTrue(ledger(dict(initial_cash='100000',calendar=calendar,events=events))['executable'])

    def test_historical_allocation_rate_without_weights_has_no_expectation(self):
        spec = json.loads((ROOT/'examples/scenarios.json').read_text(encoding='utf-8'))
        for scenario in spec['scenarios']:
            scenario.pop('probability',None)
            scenario['basis'] = 'Teaching use of a historical-reference pair, not next-issue probability'
        spec.pop('probability_basis',None)
        self.assertNotIn('weighted',evaluate(spec))

if __name__ == '__main__':
    unittest.main()
