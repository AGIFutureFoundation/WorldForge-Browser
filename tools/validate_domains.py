#!/usr/bin/env python3
"""validate_domains.py -- check all local refs in domains/*/ HTML resolve to files."""
import re, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent / 'domains'
pat = re.compile(r'''(?:src|href|poster)\s*=\s*["']([^"']+)["']''')
missing, dpl, nextimg = [], 0, 0
for site in root.iterdir():
    if not site.is_dir():
        continue
    for f in site.rglob('*.html'):
        for m in pat.finditer(f.read_text(errors='replace')):
            u = m.group(1)
            if u.startswith(('http', 'mailto:', 'tel:', 'data:', '#', '//')):
                continue
            if '?dpl=' in u:
                dpl += 1
            if '/_next/image' in u:
                nextimg += 1
            clean = u.split('#')[0].split('?')[0]
            if not clean or clean == '/':
                continue
            target = site / clean.lstrip('/')   # refs are absolute from the site root
            if not target.exists():
                missing.append((str(f.relative_to(root)), u))
print(f'dpl refs left: {dpl}, _next/image refs left: {nextimg}, missing files: {len(missing)}')
for f, u in missing[:20]:
    print(' MISSING', f, '->', u)
sys.exit(1 if missing else 0)
