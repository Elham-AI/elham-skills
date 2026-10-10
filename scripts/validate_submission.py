"""Check local submission metadata and archives; not a provider approval validator."""
import json
from pathlib import Path
import struct
import zipfile

from package_skill import FILES, PLUGIN_FILES, ROOT


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate():
    versions = set()
    for folder in (".codex-plugin", ".claude-plugin", ".cursor-plugin"):
        manifest = json.loads((ROOT / folder / "plugin.json").read_text(encoding="utf-8"))
        versions.add(manifest["version"])
        require(manifest["name"] == "elham", "Unexpected plugin name")
        require(manifest["license"] == "MIT", "License must match LICENSE")
        require(manifest["author"]["email"] == "faris@elham.ai", "Publisher contact mismatch")
        require((ROOT / manifest["skills"]).resolve() == (ROOT / "skills").resolve(), "Skill path mismatch")
    require(len(versions) == 1, "Provider versions differ")
    manifest = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    interface = manifest["interface"]
    for field, limit in (("displayName", 30), ("shortDescription", 30),
                         ("longDescription", 4000), ("developerName", 80)):
        require(0 < len(interface[field]) <= limit, f"Invalid {field} length")
    for field in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        require(interface[field].startswith("https://"), f"Invalid {field}")
    prompts = interface["defaultPrompt"]
    require(len(prompts) <= 3, "Too many starter prompts")
    require(all(0 < len(p) <= 128 and "@" not in p for p in prompts), "Invalid starter prompt")
    for field in ("logo", "composerIcon"):
        data = (ROOT / interface[field]).read_bytes()
        require(data[:8] == b"\x89PNG\r\n\x1a\n", "Expected PNG logo")
        width, height = struct.unpack(">II", data[16:24])
        require(width == height and 48 <= width <= 4096, "Logo dimensions invalid")
        require(len(data) <= 5 * 1024 * 1024, "Logo exceeds size limit")
    require((ROOT / manifest["extensions"]["com.openai"]["onboardingSkill"]).is_file(), "Missing onboarding skill")
    require("MIT License" in (ROOT / "LICENSE").read_text(), "Missing MIT license")
    require(len((ROOT / "README.md").read_text(encoding="utf-8").split()) >= 40, "README too short")
    for name, paths, source in (("elham.zip", FILES, ROOT / "skills/elham"),
                                ("elham-plugin.zip", PLUGIN_FILES, ROOT)):
        with zipfile.ZipFile(ROOT / "downloads" / name) as archive:
            require(len(archive.namelist()) == len(paths), f"Duplicate/extra entry in {name}")
            require(set(archive.namelist()) == {"elham/" + p for p in paths}, f"Unexpected files in {name}")
            require(len(paths) <= 512, "Too many plugin files")
            for relative in paths:
                path = source / relative
                expected = path.read_bytes() if path.suffix == ".png" else path.read_text(encoding="utf-8").encode("utf-8")
                require(archive.read("elham/" + relative) == expected, f"Stale archive file: {relative}")
                require(Path(relative).suffix not in {".zip", ".exe", ".ico", ".pdf"}, "Unsupported nested artifact")
                require(path.suffix == ".png" or len(expected) < 256 * 1024, f"Oversize text file: {relative}")
    print("Local submission checks passed; provider review and hosted authentication remain separate.")


if __name__ == "__main__":
    validate()
