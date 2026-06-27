#!/usr/bin/env python3
"""Detect, create and sync PrinterXPL-Forge local .venv (PEP 668 safe).

Used by pxf.py / src/main.py so `python pxf.py` works
on Debian/Ubuntu without touching system pip.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

VENV_DIR_NAME = ".venv"
REQUIREMENTS = "requirements.txt"
MARKER = ".printerxpl-venv-ready"
SRC_DIR = "src"


def repo_root(entry: Path | None = None) -> Path:
    if entry is not None:
        entry = entry.resolve()
        if entry.is_file():
            candidate = entry.parent
            if candidate.name == SRC_DIR and (candidate.parent / REQUIREMENTS).is_file():
                return candidate.parent
            if (candidate / REQUIREMENTS).is_file() and (candidate / SRC_DIR).is_dir():
                return candidate
        if entry.is_dir() and (entry / REQUIREMENTS).is_file() and (entry / SRC_DIR).is_dir():
            return entry
    return Path(__file__).resolve().parent.parent


def src_dir(root: Path) -> Path:
    return root / SRC_DIR


def venv_dir(root: Path) -> Path:
    return root / VENV_DIR_NAME


def venv_python(root: Path) -> Path:
    base = venv_dir(root)
    if sys.platform == "win32":
        return base / "Scripts" / "python.exe"
    return base / "bin" / "python"


def venv_pip(root: Path) -> Path:
    base = venv_dir(root)
    if sys.platform == "win32":
        return base / "Scripts" / "pip.exe"
    return base / "bin" / "pip"


def in_virtualenv() -> bool:
    return sys.prefix != sys.base_prefix or bool(os.environ.get("VIRTUAL_ENV"))


def _venv_usable(root: Path) -> bool:
    py = venv_python(root)
    if not py.is_file():
        return False
    try:
        subprocess.run(
            [str(py), "-c", "import sys"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
        return True
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return False


def _probe_imports(python: Path, root: Path) -> list[str]:
    script = (
        "import importlib.util, sys\n"
        "root = sys.argv[1]\n"
        "src = sys.argv[2]\n"
        "if src not in sys.path:\n"
        "    sys.path.insert(0, src)\n"
        "missing = []\n"
        "for mod in ('requests', 'colorama', 'urllib3', 'yaml'):\n"
        "    if importlib.util.find_spec(mod) is None:\n"
        "        missing.append(mod)\n"
        "if importlib.util.find_spec('core.osdetect') is None:\n"
        "    missing.append('core')\n"
        "print(','.join(missing))\n"
    )
    try:
        proc = subprocess.run(
            [str(python), "-c", script, str(root), str(src_dir(root))],
            check=True,
            capture_output=True,
            text=True,
            timeout=90,
            cwd=str(root),
        )
        out = (proc.stdout or "").strip()
        return [m for m in out.split(",") if m]
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return ["bootstrap"]


def _run(cmd: list[str], root: Path, quiet: bool = False) -> None:
    kwargs = {"cwd": str(root), "check": True}
    if quiet:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    subprocess.run(cmd, **kwargs)


def _create_venv(root: Path) -> None:
    vdir = venv_dir(root)
    if vdir.exists() and not _venv_usable(root):
        print(f"[printerxpl] Removing broken venv at {vdir}")
        import shutil

        shutil.rmtree(vdir, ignore_errors=True)

    print(f"[printerxpl] Creating virtual environment at {vdir}")
    _run([sys.executable, "-m", "venv", str(vdir)], root)


def _install_deps(root: Path) -> None:
    pip = venv_pip(root)
    req = root / REQUIREMENTS
    if not req.is_file():
        raise SystemExit(f"[printerxpl] Missing {req}")

    print("[printerxpl] Installing dependencies into .venv (PEP 668 safe)...")
    _run([str(pip), "install", "--upgrade", "pip"], root, quiet=True)
    _run([str(pip), "install", "-r", str(req)], root)
    (venv_dir(root) / MARKER).write_text("ok\n", encoding="utf-8")


def _sync_if_needed(root: Path, python: Path) -> None:
    missing = _probe_imports(python, root)
    if not missing:
        return
    print(f"[printerxpl] Syncing venv (missing: {', '.join(missing)})")
    _install_deps(root)


def ensure_runtime(entry_script: str | Path) -> None:
    """Re-exec with .venv or create/sync it before PrinterXPL imports."""
    root = repo_root(Path(entry_script))
    entry = Path(entry_script).resolve()

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    src = src_dir(root)
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    py = venv_python(root)
    if not in_virtualenv():
        if _venv_usable(root):
            missing = _probe_imports(py, root)
            if missing:
                _sync_if_needed(root, py)
            os.execv(str(py), [str(py), str(entry), *sys.argv[1:]])
        _create_venv(root)
        if not _venv_usable(root):
            raise SystemExit("[printerxpl] Failed to create .venv — run ./setup_venv.sh")
        _install_deps(root)
        os.execv(str(py), [str(py), str(entry), *sys.argv[1:]])

    _sync_if_needed(root, Path(sys.executable))
