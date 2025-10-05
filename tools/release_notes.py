#!/usr/bin/env python3
"""
Generate release notes from git commits between tags.

Usage:
  python tools/release_notes.py v2.4.2 v2.5.3
  python tools/release_notes.py --latest
"""

import subprocess
import argparse
import sys
from datetime import datetime


def get_git_tags():
    """Get all git tags sorted by date"""
    try:
        output = subprocess.check_output(
            ['git', 'tag', '--sort=-creatordate'],
            text=True,
            stderr=subprocess.DEVNULL
        )
        return [tag.strip() for tag in output.strip().split('\n') if tag.strip()]
    except subprocess.CalledProcessError:
        return []


def get_commits_between(tag1, tag2=None):
    """Get commits between two tags (or tag..HEAD)"""
    range_spec = f"{tag1}..{tag2 or 'HEAD'}"
    try:
        output = subprocess.check_output(
            ['git', 'log', range_spec, '--oneline', '--no-merges'],
            text=True,
            stderr=subprocess.DEVNULL
        )
        return [line.strip() for line in output.strip().split('\n') if line.strip()]
    except subprocess.CalledProcessError:
        return []


def categorize_commits(commits):
    """Categorize commits by type (feat, fix, docs, chore, etc.)"""
    categories = {
        'feat': [],
        'fix': [],
        'docs': [],
        'chore': [],
        'test': [],
        'refactor': [],
        'style': [],
        'perf': [],
        'other': [],
    }
    
    for commit in commits:
        # Parse: hash type(scope): message
        parts = commit.split(' ', 1)
        if len(parts) < 2:
            categories['other'].append(commit)
            continue
        
        hash_part, msg = parts
        
        # Extract type
        for ctype in categories.keys():
            if msg.startswith(f'{ctype}:') or msg.startswith(f'{ctype}('):
                categories[ctype].append(f"{hash_part} {msg}")
                break
        else:
            categories['other'].append(commit)
    
    return categories


def generate_release_notes(from_tag, to_tag=None):
    """Generate markdown release notes"""
    to_label = to_tag or "HEAD"
    commits = get_commits_between(from_tag, to_tag)
    
    if not commits:
        print(f"No commits found between {from_tag} and {to_label}")
        return
    
    categories = categorize_commits(commits)
    
    # Header
    print(f"# Release Notes: {from_tag} → {to_label}")
    print(f"\n**Date**: {datetime.now().strftime('%B %d, %Y')}")
    print(f"\n**Total Commits**: {len(commits)}\n")
    print("---\n")
    
    # Category labels
    category_labels = {
        'feat': '✨ Features',
        'fix': '🐛 Bug Fixes',
        'docs': '📚 Documentation',
        'chore': '🧹 Chores',
        'test': '🧪 Tests',
        'refactor': '♻️ Refactoring',
        'style': '💄 Style',
        'perf': '⚡ Performance',
        'other': '📦 Other',
    }
    
    # Print each category
    for ctype, label in category_labels.items():
        if not categories[ctype]:
            continue
        
        print(f"## {label}\n")
        for commit in categories[ctype]:
            # Format: - hash: message
            parts = commit.split(' ', 1)
            if len(parts) == 2:
                hash_part, msg = parts
                # Remove type prefix if present
                for prefix in ['feat:', 'fix:', 'docs:', 'chore:', 'test:', 'refactor:', 'style:', 'perf:']:
                    if msg.startswith(prefix):
                        msg = msg[len(prefix):].strip()
                        break
                # Remove scope in parentheses for cleaner output
                msg = msg.split(':', 1)[-1].strip() if ':' in msg else msg
                print(f"- `{hash_part}` {msg}")
            else:
                print(f"- {commit}")
        print()
    
    print("---\n")
    print(f"**Full Changelog**: https://github.com/mrhenrike/PrinterReaper/compare/{from_tag}...{to_label}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Generate release notes from git commits")
    parser.add_argument('from_tag', nargs='?', help='Starting tag')
    parser.add_argument('to_tag', nargs='?', help='Ending tag (default: HEAD)')
    parser.add_argument('--latest', action='store_true', help='Use latest two tags')
    
    args = parser.parse_args()
    
    if args.latest:
        tags = get_git_tags()
        if len(tags) < 2:
            print("Error: Need at least 2 tags for --latest")
            sys.exit(1)
        from_tag, to_tag = tags[1], tags[0]
        print(f"Using latest tags: {from_tag} → {to_tag}\n")
    elif args.from_tag:
        from_tag = args.from_tag
        to_tag = args.to_tag
    else:
        parser.print_help()
        sys.exit(1)
    
    generate_release_notes(from_tag, to_tag)


if __name__ == "__main__":
    main()

