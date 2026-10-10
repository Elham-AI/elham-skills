"""Build the uploadable skill ZIP from an explicit, reviewed file list."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "SKILL.md",
    "assets/logo.png",
    "agents/openai.yaml",
    "scripts/elham.py",
    "references/account.md",
    "references/connections.md",
    "references/datasets.md",
    "references/models.md",
    "references/predictions.md",
)
PLUGIN_FILES = (
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    "README.md",
    "LICENSE",
    "BRANDING.md",
    "SECURITY.md",
) + tuple("skills/elham/" + path for path in FILES)


def build(destination, plugin=False):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in PLUGIN_FILES if plugin else FILES:
            entry = zipfile.ZipInfo("elham/" + relative, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            source = ROOT / relative if plugin else ROOT / "skills/elham" / relative
            content = source.read_bytes() if source.suffix == ".png" else source.read_text(encoding="utf-8").encode("utf-8")
            archive.writestr(entry, content)


if __name__ == "__main__":
    build(ROOT / "downloads/elham.zip")
    build(ROOT / "downloads/elham-plugin.zip", plugin=True)
    print("Built skill-only and complete plugin ZIPs in downloads/")
