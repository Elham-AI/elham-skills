from pathlib import Path
import re
import unittest

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


if __name__ == "__main__":
    unittest.main()
