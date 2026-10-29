#!/usr/bin/env python3
"""Check relative links and image paths in every tracked Markdown file.

Fails on:
  * a relative link/image whose target file does not exist
  * an absolute file:// link (only works on the author's machine, broken on GitHub)
Anchors (#...) are stripped; http(s)/mailto links are not fetched.

Usage: python3 scripts/check_links.py   (from the repository root)
"""
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

LINK = re.compile(r'!?\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')


def tracked_markdown():
    out = subprocess.run(['git', 'ls-files', '*.md'], capture_output=True, text=True, check=True)
    return [Path(p) for p in out.stdout.split()]


def main():
    errors = []
    files = tracked_markdown()
    for md in files:
        in_code = False
        for lineno, line in enumerate(md.read_text(encoding='utf-8').splitlines(), 1):
            if line.lstrip().startswith('```'):
                in_code = not in_code
                continue
            if in_code:
                continue
            for target in LINK.findall(line):
                if target.startswith('file://'):
                    errors.append(f'{md}:{lineno}: absolute file:// link: {target}')
                    continue
                if re.match(r'^[a-z]+:', target) or target.startswith('#'):
                    continue
                path = unquote(target.split('#', 1)[0])
                if path and not (md.parent / path).exists():
                    errors.append(f'{md}:{lineno}: missing target: {target}')
    for e in errors:
        print(e)
    print(f'checked {len(files)} markdown files, {len(errors)} broken link(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
