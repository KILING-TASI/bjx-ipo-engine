import copy
import unittest
from pathlib import Path
from audit import load
from api import calculate,legacy_result
from engine import evaluate
from research import ledger
from sample_validation import validate_sample

ROOT=Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_scenario_same_input_exact_legacy_result(self):
        spec=load(ROOT/'examples/scenarios.json')
        before=copy.deepcopy(spec)
        out=calculate(dict(api_version='1.0',operation='scenario.v1',input=spec))
        self.assertEqual(out['result'],legacy_result(evaluate(spec)))
        self.assertEqual(spec,before)
        self.assertEqual(out['status'],'completed_with_limits')

    def test_cash_same_input_exact_precision_and_unknown_state(self):
        spec=load(ROOT/'examples/ledger.json')
        out=calculate(dict(api_version='1.0',operation='cash_ledger.v1',input=spec))
        self.assertEqual(out['result'],legacy_result(ledger(spec)))

    def test_cash_conflict_is_infeasible_not_invalid_or_silent_financing(self):
        spec=load(ROOT/'examples/ledger.json');spec['initial_cash']=500
        out=calculate(dict(api_version='1.0',operation='cash_ledger.v1',input=spec))
        self.assertEqual(out['status'],'infeasible')
        self.assertEqual(out['result']['events'],[])

    def test_version_unknown_operation_missing_and_nonfinite_fail(self):
        cases=[dict(api_version='2.0',operation='scenario.v1',input={}),
               dict(api_version='1.0',operation='annual.v1',input={}),
               dict(api_version='1.0',operation='scenario.v1',input={}),
               dict(api_version='1.0',operation='scenario.v1',input={'capital':float('nan')})]
        for spec in cases:
            with self.subTest(spec=spec):
                out=calculate(spec)
                self.assertEqual(out['status'],'failed')
                self.assertIsNone(out['result'])
                self.assertIsNotNone(out['error'])

    def test_contract_sample_count_and_cash_shortfall_remain_hypothetical(self):
        # Use repository cwd for the portable example's explicit relative paths.
        import os
        before=Path.cwd()
        try:
            os.chdir(ROOT)
            out=validate_sample({'sample_input':'examples/public-sample.json'})
        finally:os.chdir(before)
        self.assertEqual(out['real_issuance_count'],1)
        self.assertEqual([r['proportional_shares'] for r in out['cases']],[0,100,200])
        self.assertTrue(all(r['actual_individual_shares']=='unknown' for r in out['cases']))
        self.assertFalse(out['teaching_multi_issue_conflict']['executable'])
        self.assertEqual(out['teaching_multi_issue_conflict']['conflicts'][0]['shortage'],5999288)

    def test_isolated_stdin_protocol_preserves_exact_result_and_failure_exit(self):
        import subprocess,sys,json
        spec=load(ROOT/'examples/scenarios.json')
        p=subprocess.run([sys.executable,'-S',str(ROOT/'api.py')],input=json.dumps(dict(api_version='1.0',operation='scenario.v1',input=spec),ensure_ascii=False),capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(p.returncode,0)
        self.assertEqual(json.loads(p.stdout)['result'],legacy_result(evaluate(spec)))
        bad=subprocess.run([sys.executable,'-S',str(ROOT/'api.py')],input='{"api_version":"1.0","api_version":"2.0"}',capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(bad.returncode,2)
        self.assertEqual(json.loads(bad.stdout)['status'],'failed')


if __name__=='__main__':unittest.main()
