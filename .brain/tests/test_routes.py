from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.brain/scripts'))
from brain_governance import validate_route,session_context
class RouteIntegrationTests(unittest.TestCase):
    def test_actual_project_route_and_both_entrypoints(self):
        self.assertEqual(validate_route(ROOT),[])
        self.assertEqual({r['role'] for r in session_context(ROOT)},{'developer_vault','project_vault'})
    def test_root_instructions_require_the_brain(self):
        text=(ROOT/'AGENTS.md').read_text(encoding='utf-8-sig')
        self.assertEqual(text.count('<!-- knowledge-brain:start -->'),1)
        self.assertIn('skill-first',text)
        self.assertNotIn('C:'+chr(92)+'Personal-Notes',text)
if __name__=='__main__':unittest.main()
