#!/usr/bin/env python3
"""build_links_page.py -- generate site/links.html: the live-pages directory.

Every published page with its full GitHub Pages URL, grouped by section, plus live
repo counts (worlds / geo datasets / preview videos / team docs) computed at build
time. Rerun after adding pages; the page is fully static HTML.

    python3 tools/build_links_page.py
"""
import html
import json
import pathlib
import re
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
BASE_URL = 'https://www.agifuturefoundation.org/'   # canonical custom domain (Hostinger DNS -> GitHub Pages)

DESC = {
    'index.html': 'SmartCiti.X WorldForge landing page: every project surface, one list.',
    'links.html': 'This page: the complete directory of live pages.',
    'earth/index.html': 'Earth training worlds: 544 worlds on real Earth maps, grouped by city and industry.',
    'earth/world.html': 'One 3-D world page: ?world=&lt;slug&gt; loads real terrain, robots, agents and HUD.',
    'earth/gallery.html': 'Visual gallery of the Earth training worlds.',
    'earth/video-gallery.html': 'Video gallery: 3-second flyovers captured from the live world pages.',
    'earth/datasets.html': 'ROS 2 training datasets catalog: free samples, x402/USDC paid episodes on Base.',
    'earth/marketplace.html': 'WorldForge marketplace: worlds, datasets and programs.',
    'earth/omega-marketplace.html': 'Omega marketplace: premium packs and partner offers.',
    'earth/live-dashboard.html': 'Live dashboard: D3/Chart graphs over worlds, videos, geo and datasets.',
    'earth/dashboard.html': 'WorldForge dashboard: operations overview.',
    'earth/training.html': 'Trades training simulator home.',
    'earth/motion-lm.html': 'Movement LM: our own tiny GPT over robot + human movement episodes (trained locally), samples and replays in-browser.',
    'earth/ar-training.html': 'AR training: anchors and overlays for on-site use.',
    'earth/console.html': 'Earth console: per-world board with geo/video/content status and deep links.',
    'consoles/worldforge/index.html': 'WorldForge console: Master Cards, rights, avatars and voice lines.',
    'worldforge/viewer.html': '3-D WorldForge viewer (three.js): Master Card zones and landmarks.',
    'worldforge/whitepaper/out/index.html': 'WorldForge whitepaper: features, roadmap, stack.',
    'worldforge/review/out/whitepaper.html': 'Review whitepaper: the review round with its film and captions.',
    'worldforge/out/overview/index.html': 'World overviews: one overview page per world.',
    'agents/teams.html': 'Agent teams directory.',
}


def counts():
    earth = SITE / 'earth'
    out = {}
    try:
        out['worlds'] = len(json.loads((earth / 'worlds.json').read_text()))
    except Exception:
        out['worlds'] = 0
    out['geo'] = len(list((earth / 'data').glob('*.geo.json')))
    out['videos'] = len(list((earth / 'videos').glob('*.mp4')))
    out['team'] = len(list((earth / 'team' / 'world').glob('*.json')))
    return out


def pages():
    out = []
    for p in SITE.rglob('*.html'):
        rel = p.relative_to(SITE).as_posix()
        t = re.search(r'<title[^>]*>(.*?)</title>', p.read_text(errors='ignore'), re.S)
        title = (t.group(1).strip() if t else rel.split('/')[-1])
        out.append({'rel': rel, 'title': title, 'desc': DESC.get(rel, '')})
    return out


def group(rel):
    if '/' not in rel:
        return 'Top'
    return {'earth': 'Earth Training Worlds', 'consoles': 'Consoles', 'worldforge': 'WorldForge',
            'agents': 'Agents'}.get(rel.split('/')[0], 'Other')

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0f14;color:#e2e8f0;font:15px/1.5 system-ui,sans-serif}
a{color:#34d399;text-decoration:none}a:hover{color:#6ee7b7}
header{padding:40px 20px 24px;text-align:center;border-bottom:1px solid rgba(52,211,153,.2)}
header h1{font-size:2rem;margin-bottom:6px}header h1 span{color:#34d399}
header p{color:#94a3b8}.stats{display:flex;justify-content:center;gap:24px;padding:18px;flex-wrap:wrap}
.stats div{text-align:center}.stats b{display:block;font-size:1.5rem;color:#34d399}
.stats span{font-size:.72rem;color:#64748b;text-transform:uppercase}
main{max-width:860px;margin:0 auto;padding:24px 16px 48px}
h2{font-size:1.15rem;color:#34d399;margin:28px 0 10px;padding-bottom:6px;border-bottom:1px solid rgba(52,211,153,.2)}
h2 small{font-size:.75rem;color:#64748b;font-weight:normal;margin-left:8px}
ul.links{list-style:none}ul.links li{border-top:1px solid rgba(255,255,255,.07);padding:10px 0}
ul.links li a{font-size:1rem}ul.links code{display:block;font-size:.78rem;color:#64748b;word-break:break-all}
ul.links span{display:block;color:#94a3b8;font-size:.85rem}
footer{padding:20px;color:#64748b;font-size:.8rem;text-align:center;border-top:1px solid rgba(255,255,255,.07)}
"""


def render():
    c = counts()
    ps = pages()
    order = ['Top', 'Earth Training Worlds', 'Consoles', 'WorldForge', 'Agents', 'Other']
    sections = []
    for g in order:
        items = sorted((p for p in ps if group(p['rel']) == g and p['rel'] != 'links.html'),
                       key=lambda p: p['rel'])
        if not items:
            continue
        rows = '\n'.join(
            f'<li><a href="{BASE_URL}{html.escape(p["rel"])}">{html.escape(p["title"])}</a>'
            f'<code>{BASE_URL}{html.escape(p["rel"])}</code>'
            f'<span>{html.escape(p["desc"])}</span></li>'
            for p in items)
        sections.append(f'<h2>{g} <small>{len(items)} pages</small></h2><ul class="links">{rows}</ul>')
    body = '\n'.join(sections)
    stats = (f'<div class="stats"><div><b>{c["worlds"]}</b><span>Worlds</span></div>'
             f'<div><b>{c["geo"]}</b><span>Geo datasets</span></div>'
             f'<div><b>{c["videos"]}</b><span>Preview videos</span></div>'
             f'<div><b>{c["team"]}</b><span>Worlds with content</span></div></div>')
    stamp = time.strftime('%Y-%m-%d %H:%M')
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>WorldForge Live Pages - Directory</title><style>' + CSS + '</style></head><body>'
            '<header><h1>WorldForge <span>Live Pages</span></h1>'
            '<p>Every published page, with its live URL</p>' + stats + '</header>'
            '<main>' + body + '</main>'
            '<footer>Generated by tools/build_links_page.py at ' + stamp +
            ' &middot; Agents operate; people govern &middot; AGI Future Foundation PBC</footer>'
            '</body></html>\n')


def main():
    (SITE / 'links.html').write_text(render())
    print('wrote site/links.html with', len(pages()), 'pages;', 'counts:', counts())


if __name__ == '__main__':
    main()
