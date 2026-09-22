"""Assemble the same static site locally and on GitHub Pages (standard library only)."""

from pathlib import Path
import hashlib
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def build():
    destination = ROOT / "_site"
    destination.mkdir(exist_ok=True)
    sources = sorted(source for source in (ROOT / "web").iterdir()
                     if source.is_file() and source.suffix in {".html", ".css", ".js", ".py", ".svg"})
    modules = sorted((ROOT / "battle_simulator").glob("*.py"))
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version = "([^"]+)"', project, re.MULTILINE).group(1)
    digest = hashlib.sha256(version.encode())
    for source in sources + modules:
        digest.update(source.relative_to(ROOT).as_posix().encode())
        digest.update(source.read_bytes())
    asset_version = digest.hexdigest()[:16]
    for source in sources:
        if source.suffix == ".html":
            content = source.read_text(encoding="utf-8")
            content = re.sub(r'((?:src|href)="[\w.-]+\.(?:js|css))(?:\?v=[^"]*)?"',
                             rf'\1?v={asset_version}"', content)
            content = re.sub(r'(<span data-app-version>).*?(</span>)',
                             rf'\g<1>v{version}\2', content)
            (destination / source.name).write_text(content, encoding="utf-8")
        elif source.suffix == ".css":
            content = source.read_text(encoding="utf-8")
            content = re.sub(r'url\("([\w.-]+\.svg)"\)',
                             rf'url("\1?v={asset_version}")', content)
            (destination / source.name).write_text(content, encoding="utf-8")
        else:
            shutil.copy2(source, destination / source.name)
    package = destination / "battle_simulator"
    package.mkdir(exist_ok=True)
    for source in modules:
        shutil.copy2(source, package / source.name)
    (destination / ".nojekyll").touch()
    print(f"Site ready: {destination}")


if __name__ == "__main__":
    build()
