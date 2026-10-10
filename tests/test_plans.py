import copy,json,unittest
from pathlib import Path
from comparison import compare_plans
class PlansTests(unittest.TestCase):
 def setUp(self): self.s=json.loads(Path('examples/compare-plans.json').read_text(encoding='utf-8'))
 def test_subsets_conflict_and_reference_not_deducted(self):
  r=compare_plans(self.s);self.assertEqual(r['candidate_count'],7)
  by={p['id']:p for p in r['plans']}
  self.assertEqual(by['subset:issue-A,issue-B']['status'],'cash_conflict')
  self.assertIsNone(by['subset:issue-A,issue-B']['locked_capital_days'])
  self.assertEqual(by['ipo-plan']['realized_cash_profit'],'50.00')
  self.assertAlmostEqual(float(by['ipo-plan']['reference_sensitivity'][0]['gross_locked_capital_cost']),3200*.02/365)
  self.assertIsNone(by['ipo-plan']['reference_sensitivity'][0]['adjusted_profit'])
 def test_unsettled_and_negative_outcomes(self):
  self.s['plans'][0]['events'].pop();r=compare_plans(self.s)
  self.assertEqual(r['plans'][0]['status'],'unsettled_principal');self.assertIsNone(r['plans'][0]['realized_cash_profit'])
 def test_limits_and_missing_reference_metadata(self):
  for change in ('limit','metadata','duplicate'):
   s=copy.deepcopy(self.s)
   if change=='limit':s['candidate_issues']*=3
   if change=='metadata':s['reference_rates'][0].pop('fee_basis')
   if change=='duplicate':s['plans'][1]['id']=s['plans'][0]['id']
   with self.subTest(change=change),self.assertRaises(ValueError):compare_plans(s)
if __name__=='__main__':unittest.main()
