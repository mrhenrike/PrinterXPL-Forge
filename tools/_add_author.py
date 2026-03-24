#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internal tool: inject author block into all PrinterReaper Python source files.
Run from the project root: python tools/_add_author.py
"""
# Author    : Andre Henrique (@mrhenrike)
# GitHub    : https://github.com/mrhenrike
# LinkedIn  : https://linkedin.com/in/mrhenrike
# X/Twitter : https://x.com/mrhenrike

import os
import re

AUTHOR_BLOCK = (
    "# Author    : Andre Henrique (@mrhenrike)\n"
    "# GitHub    : https://github.com/mrhenrike\n"
    "# LinkedIn  : https://linkedin.com/in/mrhenrike\n"
    "# X/Twitter : https://x.com/mrhenrike\n"
)

AUTHOR_RE = re.compile(r"# Author\s*:", re.IGNORECASE)

# Replace outdated author fields (e.g. "Author: Andre Henrique" or "ChatGPT")
REPLACE_AUTHOR_RE = re.compile(
    r"(# Author\s*:.*\n)"
    r"(# GitHub\s*:.*\n)?"
    r"(# LinkedIn\s*:.*\n)?"
    r"(# X(/Twitter)?\s*:.*\n)?",
    re.IGNORECASE,
)

FILES = [
    "printer-reaper.py",
    "scripts/help_selftest.py",
    "scripts/selftest_help_run.py",
    "setup.py",
    "src/core/attack_orchestrator.py",
    "src/core/capabilities.py",
    "src/core/discovery.py",
    "src/core/osdetect.py",
    "src/core/printer.py",
    "src/main.py",
    "src/modules/pcl.py",
    "src/modules/pjl.py",
    "src/modules/ps.py",
    "src/payloads/__init__.py",
    "src/protocols/__init__.py",
    "src/protocols/firmware.py",
    "src/protocols/ipp.py",
    "src/protocols/ipp_attacks.py",
    "src/protocols/lpd.py",
    "src/protocols/network_map.py",
    "src/protocols/raw.py",
    "src/protocols/smb.py",
    "src/protocols/ssrf_pivot.py",
    "src/protocols/storage.py",
    "src/utils/banner_grabber.py",
    "src/utils/codebook.py",
    "src/utils/config.py",
    "src/utils/discovery_online.py",
    "src/utils/fuzzer.py",
    "src/utils/helper.py",
    "src/utils/local_printers.py",
    "src/utils/ml_engine.py",
    "src/utils/operators.py",
    "src/utils/vuln_scanner.py",
    "src/version.py",
    "tests/qa_comprehensive_test.py",
    "tests/test_runner.py",
    "tools/db_merge.py",
    "tools/release_notes.py",
]


def _insert_author(content: str) -> str:
    """Return content with AUTHOR_BLOCK inserted after the opening header."""
    lines = content.splitlines(keepends=True)
    i = 0

    # Skip shebang line
    if lines and lines[0].startswith("#!"):
        i = 1

    # Skip coding declaration (e.g. # -*- coding: utf-8 -*-)
    if i < len(lines) and "coding" in lines[i] and lines[i].startswith("#"):
        i += 1

    # Skip a blank line between coding and docstring
    if i < len(lines) and lines[i].strip() == "":
        i += 1

    # Skip opening docstring (single or multi-line)
    if i < len(lines) and lines[i].strip().startswith('"""'):
        first_dq = lines[i].index('"""')
        rest_of_line = lines[i][first_dq + 3:]
        if '"""' in rest_of_line:
            # Single-line docstring
            i += 1
        else:
            # Multi-line — find closing triple-quote
            i += 1
            while i < len(lines):
                if '"""' in lines[i]:
                    i += 1
                    break
                i += 1

    insert_at = i

    # Build new content
    before = lines[:insert_at]
    after = lines[insert_at:]

    # Remove leading blank lines from 'after' to prevent double blank
    while after and after[0].strip() == "":
        after = after[1:]

    author_lines = ["\n"] + AUTHOR_BLOCK.splitlines(keepends=True) + ["\n"]
    return "".join(before + author_lines + after)


def process_file(fpath: str) -> str:
    """Process a single file. Returns 'inserted', 'updated', or 'ok'."""
    if not os.path.exists(fpath):
        return "not_found"

    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()

    if AUTHOR_RE.search(content):
        # Replace/normalise existing author block
        new_content = REPLACE_AUTHOR_RE.sub(AUTHOR_BLOCK, content, count=1)
        if new_content == content:
            return "ok"
        with open(fpath, "w", encoding="utf-8") as fh:
            fh.write(new_content)
        return "updated"

    # Insert fresh
    new_content = _insert_author(content)
    with open(fpath, "w", encoding="utf-8") as fh:
        fh.write(new_content)
    return "inserted"


def main() -> None:
    results = {"inserted": [], "updated": [], "ok": [], "not_found": []}
    for fpath in FILES:
        status = process_file(fpath)
        results[status].append(fpath)

    for status, label in [
        ("inserted", "Inserted"),
        ("updated",  "Updated "),
        ("ok",       "Already "),
        ("not_found","Missing "),
    ]:
        for f in results[status]:
            print(f"  [{label}] {f}")

    total = len(results["inserted"]) + len(results["updated"])
    print(f"\n  {total} file(s) modified.")


if __name__ == "__main__":
    main()
