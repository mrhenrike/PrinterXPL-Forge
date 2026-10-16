"""Validate pyproject.toml entrypoints for PrinterXPL-Forge."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _scripts() -> dict[str, str]:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    in_scripts = False
    scripts: dict[str, str] = {}
    for line in text.splitlines():
        if re.match(r'\[project\.scripts\]', line):
            in_scripts = True
            continue
        if in_scripts and re.match(r'\[', line):
            break
        if in_scripts:
            m = re.match(r'\s*(\S+)\s*=\s*"([^"]+)"', line)
            if m:
                scripts[m.group(1)] = m.group(2)
    return scripts


def test_pxf_entrypoint_declared() -> None:
    assert "pxf" in _scripts()


def test_pxf_points_to_src_main() -> None:
    scripts = _scripts()
    assert scripts["pxf"] == "src.main:main", scripts.get("pxf")


def test_src_main_has_main_function() -> None:
    src_main = ROOT / "src" / "main.py"
    assert src_main.exists()
    text = src_main.read_text(encoding="utf-8")
    assert re.search(r'^def main\b', text, re.MULTILINE), "main() not found in src/main.py"


def test_profile_cli_entrypoint_correct() -> None:
    scripts = _scripts()
    assert scripts.get("pxf-profile") == "src.utils.profile_cli:main", scripts.get("pxf-profile")
