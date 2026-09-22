import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import build_site


class BuildSiteTest(unittest.TestCase):
    def test_python_changes_invalidate_both_pages_and_styles(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(build_site, "ROOT", Path(folder)):
            root = Path(folder)
            (root / "web").mkdir()
            (root / "battle_simulator").mkdir()
            (root / "pyproject.toml").write_text('[project]\nversion = "0.5.0"\n')
            html = '<script src="game.js?v=old"></script><span data-app-version>v0.3</span>'
            for page in ("index.html", "simulator.html"):
                (root / "web" / page).write_text(html)
            (root / "web" / "game.css").write_text('body { background: url("battlefield.svg"); }')
            module = root / "battle_simulator" / "models.py"
            module.write_text("RULE = 1\n")
            build_site.build()
            first = (root / "_site" / "index.html").read_text()
            build_site.build()
            self.assertEqual(first, (root / "_site" / "index.html").read_text())
            module.write_text("RULE = 2\n")
            build_site.build()
            second = (root / "_site" / "index.html").read_text()
            self.assertNotEqual(first, second)
            self.assertEqual(second, (root / "_site" / "simulator.html").read_text())
            self.assertIn('data-app-version>v0.5.0', second)
            version = re.search(r'\?v=([a-f0-9]+)', second).group(1)
            self.assertIn(f'battlefield.svg?v={version}', (root / "_site" / "game.css").read_text())
            self.assertEqual((root / "_site" / "battle_simulator" / "models.py").read_text(), "RULE = 2\n")
