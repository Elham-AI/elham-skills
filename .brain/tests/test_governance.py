from pathlib import Path
import importlib.util,tempfile,unittest,subprocess,sys
SPEC=importlib.util.spec_from_file_location('brain_governance',Path(__file__).resolve().parents[1]/'scripts/brain_governance.py')
g=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(g)

class GovernanceTests(unittest.TestCase):
    def test_description_limits_match_portable_skill_format(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):g.create_skill(Path(d),'too-long','x'*1025,'Workflow')
            self.assertFalse((Path(d)/'too-long').exists())
            with self.assertRaises(ValueError):g.create_skill(Path(d),'bad-markup','Use <thing> here','Workflow')
    def test_malformed_yaml_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a-skill';p.mkdir();(p/'SKILL.md').write_text('---\nname: a-skill\ndescription: [unterminated\n---\nBody\n')
            self.assertTrue(any('YAML' in s for s in g.validate_skill(p)))
    def test_initialize_and_read_both_brains_without_overwriting(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);dev=root/'Developer';dev.mkdir();(dev/'Knowledge MOC.md').write_text('Shared engineering knowledge')
            project=root/'project';g.initialize_project(project,dev)
            self.assertEqual(g.validate_route(project),[])
            content=g.session_context(project)
            self.assertEqual(len(content),2);self.assertIn('Shared engineering',content[0]['content'])
            self.assertIn('Project MOC',content[1]['content'])
            with self.assertRaises(FileExistsError):g.initialize_project(project,dev)
    def test_skill_name_rejects_path_escape_and_malformed(self):
        for name in ['../escape','Bad_Name','a--b','-bad','x'*65]:self.assertFalse(g.valid_skill_name(name))
        self.assertTrue(g.valid_skill_name('check-knowledge-names'))
    def test_create_executable_valid_skill_and_reject_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path=g.create_skill(Path(d),'example-workflow','Validate sample inputs when testing a workflow.','Read inputs and validate the result before reporting success.')
            self.assertEqual(g.validate_skill(path),[])
            result=subprocess.run([sys.executable,str(path/'scripts/validate_skill.py')],capture_output=True)
            self.assertEqual(result.returncode,0)
            with self.assertRaises(FileExistsError):g.create_skill(Path(d),'example-workflow','description','body')
    def test_missing_script_and_wrong_name_fail(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a-skill';p.mkdir();(p/'SKILL.md').write_text('---\nname: wrong-name\ndescription: A real description.\n---\nBody\n')
            issues=g.validate_skill(p)
            self.assertTrue(any('name' in s for s in issues));self.assertTrue(any('script' in s for s in issues))
    def test_invalid_python_is_rejected_without_running(self):
        with tempfile.TemporaryDirectory() as d:
            p=g.create_skill(Path(d),'example-workflow','A real description.','A real workflow.')
            (p/'scripts/broken.py').write_text('def broken(:\n')
            self.assertTrue(any('syntax' in s for s in g.validate_skill(p)))
    def test_titles_are_idempotent_and_preserve_acronyms(self):
        self.assertEqual(g.note_title('JWT and API contracts'),'JWT and API Contracts')
        self.assertEqual(g.note_title('knowledge in the brain'),'Knowledge in the Brain')
        self.assertEqual(g.note_title(g.note_title('a new i18n rule')),'A New i18n Rule')
    def test_empty_folder_check_ignores_git_but_finds_content(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'.git/objects/info').mkdir(parents=True);(p/'Empty').mkdir()
            self.assertEqual(g.empty_content_dirs(p),['Empty'])
    def test_route_is_required_and_validates_real_entrypoints(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.assertTrue(g.validate_route(p))
            (p/'.brain.json').write_text('{"developer_vault":"missing","project_vault":"missing"}')
            self.assertTrue(any('missing' in e.lower() for e in g.validate_route(p)))
    def test_sensitive_paths_cannot_be_selected_as_brain(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'.brain.json').write_text('{"developer_vault":"C:/Personal-Notes","project_vault":null}')
            self.assertTrue(any('personal' in e.lower() for e in g.validate_route(p)))

if __name__=='__main__':unittest.main()
