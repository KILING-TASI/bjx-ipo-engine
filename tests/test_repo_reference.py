import copy,json,tempfile,unittest
from pathlib import Path
from repo_reference import repo_reference
from comparison import compare_cash
class RepoReferenceTests(unittest.TestCase):
 def setUp(self):self.s=json.loads(Path('examples/repo-reference.json').read_text(encoding='utf-8'))
 def test_weekend_interest_and_separate_fees(self):
  r=repo_reference(self.s);self.assertEqual(r['interest_days'],3);self.assertEqual(r['gross_interest_cent'],'11.44');self.assertEqual(r['fee_exact'],'1.00');self.assertEqual(r['net_reference_interest'],'10.44')
  s=json.loads(Path('examples/public-reference-cash.json').read_text(encoding='utf-8'));s['plans'][0]=r['cash_plan'];out=compare_cash(s)
  self.assertEqual(out['plans'][0]['realized_cash_profit'],'10.44');self.assertEqual(out['plans'][0]['paid_separate_fees'],'1.00')
  s['initial_cash']='100000';self.assertEqual(compare_cash(s)['plans'][0]['status'],'cash_conflict')
 def test_unknown_fee_blocks_net_and_plan(self):
  self.s['fee']=dict(status='unknown',basis='unknown',source='No broker tariff checked');r=repo_reference(self.s)
  self.assertIsNone(r['net_reference_interest']);self.assertIsNone(r['cash_plan']);self.assertEqual(r['status'],'fee_unknown_net_blocked')
 def test_fee_floor_and_loss_preserved(self):
  self.s['fee']['minimum']='20';r=repo_reference(self.s);self.assertEqual(r['net_reference_interest'],'-8.56')
 def test_dates_and_missing_fee_rejected(self):
  for key,value in [('trade_date','2026-10-09'),('maturity_settlement_date','2026-10-09'),('interest_available_date','2026-10-09')]:
   s=copy.deepcopy(self.s);s['dates'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):repo_reference(s)
  self.s['fee'].pop('minimum')
  with self.assertRaises(ValueError):repo_reference(self.s)
 def test_raw_hash_and_percent_mismatch(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/'fake.html';p.write_text('changed');self.s['raw_quote_path']=str(p)
   with self.assertRaises(ValueError):repo_reference(self.s)
   del self.s['raw_quote_path'];q=json.loads(Path(self.s['quote_record']).read_text(encoding='utf-8'));q['annual_rate_fraction']='1.392';p=Path(temp)/'quote.json';p.write_text(json.dumps(q));self.s['quote_record']=str(p)
   with self.assertRaises(ValueError):repo_reference(self.s)
if __name__=='__main__':unittest.main()
