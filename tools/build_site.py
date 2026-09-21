"""Assemble the same static site locally and on GitHub Pages (standard library only)."""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build():
    destination = ROOT / "_site"
    destination.mkdir(exist_ok=True)
    for source in (ROOT / "web").iterdir():
        if source.is_file() and source.suffix in {".html", ".css", ".js", ".py", ".svg"}:
            shutil.copy2(source, destination / source.name)
    package = destination / "battle_simulator"
    package.mkdir(exist_ok=True)
    for source in (ROOT / "battle_simulator").glob("*.py"):
        shutil.copy2(source, package / source.name)
    (destination / ".nojekyll").touch()
    print(f"Site ready: {destination}")


if __name__ == "__main__":
    build()
