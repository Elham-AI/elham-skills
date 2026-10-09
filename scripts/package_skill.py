"""Build the uploadable skill ZIP from an explicit, reviewed file list."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "scripts/elham.py",
    "references/account.md",
    "references/connections.md",
    "references/datasets.md",
    "references/models.md",
    "references/predictions.md",
)


def build(destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in FILES:
            entry = zipfile.ZipInfo("elham/" + relative, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            content = (ROOT / "skills/elham" / relative).read_text(encoding="utf-8")
            archive.writestr(entry, content.encode("utf-8"))


if __name__ == "__main__":
    build(ROOT / "downloads/elham.zip")
    print("Built downloads/elham.zip")
