"""Version consistency checks for PrinterXPL-Forge."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    assert m is not None
    return m.group(1)


def test_version_semver() -> None:
    v = _pyproject_version()
    assert re.fullmatch(r"\d+\.\d+\.\d+", v), v


def test_src_version_matches_pyproject() -> None:
    from version import __version__
    assert __version__ == _pyproject_version()
