#!/usr/bin/env python3
"""mirror_kylon.py -- recursively mirror a kylon.app Next.js/Vite static site
into a local directory, rewriting it for static hosting on GitHub Pages.

Usage:
  python3 tools/mirror_kylon.py <subdomain> <out_dir> [--prefix /sacred]

- Pages:   /mission  -> out/mission/index.html   (links rewritten to /mission/)
- Assets:  /_next/static/..., /heroes/... downloaded, ?dpl= queries stripped
- Images:  /_next/image?url=%2Ffoo.png&w=.. -> /foo.png (srcset simplified)
- CSS:     url(...) references resolved and downloaded
- --prefix: rewrite absolute refs so the site can be mounted at a sub-path
  (files saved under out_dir; HTML/CSS refs become <prefix>/...)
"""
import re, sys, time, urllib.parse, urllib.request, urllib.error, pathlib, argparse

UA = {'User-Agent': 'Mozilla/5.0 (mirror-kylon/1.0)'}
ASSET_EXT = re.compile(r'\.(css|js|mjs|png|jpe?g|svg|ico|woff2?|ttf|mp4|webm|webp|json|txt|xml)(\?|$)', re.I)
HTML_LINK = re.compile(r'''(src|href|poster)\s*=\s*["']([^"']+)["']''', re.I)
CSS_URL = re.compile(r'url\(\s*["\']?([^"\')]+?)["\']?\s*\)', re.I)


def fetch(url, tries=3, depth=0):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and depth < 3:
                loc = e.headers.get('Location')
                if loc:
                    return fetch(urllib.parse.urljoin(url, loc), tries, depth + 1)
            if i == tries - 1:
                print(f'  !! fail {url}: {e}')
                return None
            time.sleep(1.5)
        except Exception as e:
            if i == tries - 1:
                print(f'  !! fail {url}: {e}')
                return None
            time.sleep(1.5)


def posix_dir(p):
    return '/'.join(p.strip('/').split('/')[:-1]) + '/'


class Mirror:
    def __init__(self, base, out, prefix=''):
        self.base = base.rstrip('/')
        self.out = pathlib.Path(out)
        self.prefix = prefix.rstrip('/')
        self.pages, self.assets, self.done, self.done_pages = [], set(), set(), set()

    # ---- local file placement -------------------------------------------------
    def local_path(self, abspath):
        p = abspath.split('?')[0]
        return self.out / p.lstrip('/')

    def save(self, abspath, data):
        f = self.local_path(abspath)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        print(f'  + {abspath} ({len(data)}B)')

    def queue_asset(self, abspath):
        if abspath in self.done:
            return
        self.done.add(abspath)
        data = fetch(self.base + abspath)
        if data is not None:
            self.save(abspath, data)
            if abspath.split('?')[0].endswith('.css'):
                self.pull_css_refs(abspath, data.decode('utf-8', 'replace'))

    def pull_css_refs(self, css_path, css_text):
        css_dir = '/' + posix_dir(css_path)
        for m in CSS_URL.finditer(css_text):
            u = m.group(1)
            if u.startswith(('data:', 'http://', 'https://', '#')):
                continue
            if u.startswith('/'):
                target = u.split('?')[0]
            else:
                target = (posix_dir(css_dir) + u).split('?')[0]
            self.queue_asset(target)

    def ref_prefix(self, abspath):
        return (self.prefix + abspath) if self.prefix else abspath

    def rewrite_asset_ref(self, u):
        orig = u
        u = u.replace('&amp;', '&')
        m = re.match(r'^/_next/image\?url=([^&]+)', u)   # optimizer -> original
        if m:
            src = urllib.parse.unquote(m.group(1)).split('?')[0]
            self.queue_asset(src)
            return self.ref_prefix(src)
        if u.startswith(('/', './', '../')) and not u.startswith('//'):
            clean = (u if u.startswith('/') else '/' + u).split('?')[0]
            if ASSET_EXT.search(clean) or clean.startswith('/_next/'):
                self.queue_asset(clean)
                return self.ref_prefix(clean)
        return orig

    def rewrite_html(self, html):
        def sub(m):
            attr, val = m.group(1), m.group(2)
            if val.startswith(('mailto:', 'tel:', 'data:', 'http://', 'https://', '//', '#')):
                return m.group(0)
            v = val.replace('&amp;', '&')
            # strip deployment/noise query params
            v = re.sub(r'[?&]dpl=[^&"\']*', '', v)
            v = re.sub(r'[?&](w|q)=[0-9]+(&|$)', r'\2', v)
            v = v.rstrip('?&')
            if v.rstrip('/').startswith('/_next/') or ASSET_EXT.search(v.split('?')[0]):
                v = self.rewrite_asset_ref(v)
                return f'{attr}="{v}"'
            if v.startswith('/'):
                # internal page route: dir-index style
                route = v.split('#')[0].split('?')[0]
                if route and route != '/' and ASSET_EXT.search(route) is None:
                    if route not in self.pages and route not in self.done_pages:
                        self.pages.append(route)
                    frag = ('#' + v.split('#')[1]) if '#' in v else ''
                    v = route.rstrip('/') + '/' + frag
                return f'{attr}="{v}"'
            return f'{attr}="{val}"'
        return HTML_LINK.sub(sub, html)

    def crawl_page(self, route):
        if route in self.done_pages:
            return
        self.done_pages.add(route)
        url = self.base + route.rstrip('/')   # canonical: no trailing slash (server 308s slashes)
        data = fetch(url)
        if data is None:
            return
        html = data.decode('utf-8', 'replace')
        html = self.rewrite_html(html)

        def srcset_sub(m):
            urls = [u.strip() for u in m.group(1).split(',')
                    if not u.strip().startswith('/_next/image')]
            return 'srcset="' + ', '.join(urls) + '"' if urls else 'srcset=""'

        html = re.sub(r'srcset="([^"]+)"', srcset_sub, html)
        out = (self.out / route.strip('/') / 'index.html') if route != '/' else self.out / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html)
        print(f'  PAGE {route or "/"} -> {out.relative_to(self.out)}')
        for r in list(self.pages):
            self.crawl_page(r)
        for extra in ('/favicon.ico', '/robots.txt', '/sitemap.xml'):
            if extra not in self.done:
                self.queue_asset(extra)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('subdomain')
    ap.add_argument('out_dir')
    ap.add_argument('--prefix', default='')
    a = ap.parse_args()
    m = Mirror(f'https://{a.subdomain}.kylon.app', a.out_dir, a.prefix)
    m.crawl_page('/')
    print(f'done: {len(m.done)} assets, {len(m.done_pages)} pages -> {a.out_dir}')


if __name__ == '__main__':
    main()
