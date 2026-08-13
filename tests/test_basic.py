"""Basic package import smoke tests for PrinterXPL-Forge."""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    assert match is not None, "version not found in pyproject.toml"
    return match.group(1)


def test_import_src_version() -> None:
    """Canonical version module must import cleanly."""
    module = importlib.import_module("src.version")
    assert module is not None


def test_version_matches_pyproject() -> None:
    """src.version.__version__ must match pyproject.toml and be semver."""
    module = importlib.import_module("src.version")
    version = getattr(module, "__version__", None)
    assert isinstance(version, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), version
    assert version == _pyproject_version()