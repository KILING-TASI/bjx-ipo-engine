import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from audit import load, verify

ROOT=Path(__file__).resolve().parents[1]


class BridgeFailureTests(unittest.TestCase):
    def test_changed_external_response_is_blocked_and_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'new-result'
            command=[sys.executable,'-c','print("{}")']
            run=subprocess.run([sys.executable,'-S',str(ROOT/'.github/scripts/check_bridge_cases.py'),
                '--bridge-command-json',json.dumps(command),'--out-dir',str(out)],
                cwd=ROOT,capture_output=True,timeout=20)
            self.assertEqual(run.returncode,2,run.stderr.decode('utf-8',errors='replace'))
            result=load(out/'result.json')
            self.assertEqual(result['status'],'blocked')
            self.assertIn('joint-unweighted',result['message'])
            self.assertFalse(result['workbench_checked'])
            self.assertEqual(verify(out)['status'],'content_matches_manifest')


if __name__=='__main__':unittest.main()
