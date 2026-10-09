import tempfile
import unittest
from pathlib import Path
from audit import digest,load
from demo import demo


class DemoTests(unittest.TestCase):
    def test_public_scope_teaching_limits_and_portable_input_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'demo';demo(out)
            r=load(out/'result.json');m=load(out/'preview-manifest.json')
            self.assertEqual(r['matrix']['real_issuance_count'],1)
            self.assertEqual(r['public_sample']['individual_actual_allocation'],'unknown')
            self.assertEqual([c['proportional_shares'] for c in r['matrix']['cases']],[0,100,200])
            self.assertEqual(m['files']['index.html'],digest((out/'index.html').read_bytes()))
            self.assertNotIn(str(Path.cwd()),(out/'input.json').read_text(encoding='utf-8'))
            self.assertIn('未认证券商到账',(out/'index.html').read_text(encoding='utf-8'))
            with self.assertRaises(FileExistsError):demo(out)


if __name__=='__main__':unittest.main()
