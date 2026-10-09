from pathlib import Path
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class SkillPackageTests(unittest.TestCase):
    def test_installable_skill_and_all_references_exist(self):
        skill = ROOT / "skills/elham/SKILL.md"
        content = skill.read_text(encoding="utf-8")
        self.assertRegex(content, r"\A---\nname: elham\ndescription: [^\n]+\n---\n")
        for document in [skill, *(skill.parent / "references").glob("*.md")]:
            for target in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                if not target.startswith("https:"):
                    self.assertTrue((document.parent / target).is_file(), target)
        self.assertTrue((skill.parent / "scripts/elham.py").is_file())

    def test_native_manifests_resolve_to_the_same_skill(self):
        manifests = [json.loads((ROOT / folder / "plugin.json").read_text())
                     for folder in (".codex-plugin", ".claude-plugin", ".cursor-plugin")]
        self.assertEqual(len({m["version"] for m in manifests}), 1)
        for manifest in manifests:
            self.assertEqual(manifest["name"], "elham")
            resolved = (ROOT / manifest["skills"]).resolve()
            self.assertEqual(resolved, (ROOT / "skills").resolve())
            self.assertTrue((resolved / "elham/SKILL.md").is_file())
            self.assertNotIn("mcpServers", manifest)

    def test_marketplaces_reference_packaged_plugin(self):
        for folder, manifest_folder in ((".agents/plugins", ".codex-plugin"),
                                        (".claude-plugin", ".claude-plugin"),
                                        (".cursor-plugin", ".cursor-plugin")):
            marketplace = json.loads((ROOT / folder / "marketplace.json").read_text())
            self.assertEqual(marketplace["name"], "elham-skills")
            self.assertEqual(len(marketplace["plugins"]), 1)
            entry = marketplace["plugins"][0]
            source = entry["source"]
            relative = source["path"] if isinstance(source, dict) else source
            plugin_root = (ROOT / relative).resolve()
            self.assertEqual(plugin_root, ROOT.resolve())
            plugin = json.loads((plugin_root / manifest_folder / "plugin.json").read_text())
            self.assertEqual(entry["name"], plugin["name"])

    def test_upload_archive_matches_source_and_helper_runs(self):
        spec = importlib.util.spec_from_file_location("package_skill", ROOT / "scripts/package_skill.py")
        packager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packager)
        with zipfile.ZipFile(ROOT / "downloads/elham.zip") as archive:
            expected = {"elham/" + relative for relative in packager.FILES}
            self.assertEqual(set(archive.namelist()), expected)
            for relative in packager.FILES:
                content = (ROOT / "skills/elham" / relative).read_text(encoding="utf-8").encode("utf-8")
                self.assertEqual(archive.read("elham/" + relative), content, relative)
            with tempfile.TemporaryDirectory() as folder:
                archive.extractall(folder)
                result = subprocess.run([sys.executable, str(Path(folder) / "elham/scripts/elham.py"), "--help"],
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("login", result.stdout)

    def test_archive_build_is_reproducible(self):
        spec = importlib.util.spec_from_file_location("package_skill", ROOT / "scripts/package_skill.py")
        packager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(packager)
        with tempfile.TemporaryDirectory() as folder:
            first, second = Path(folder) / "first.zip", Path(folder) / "second.zip"
            packager.build(first)
            packager.build(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
