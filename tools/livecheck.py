#!/usr/bin/env python3
"""After a deploy: every indexable page answers 200 with the repo's exact bytes, an unknown path is a real 404,
robots/sitemap/llms/key file are served, the sample films answer range requests. Run from the repo root on the
commit that is live. Exit 1 on any mismatch."""
import hashlib, sys, urllib.request, urllib.error
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from check import PAGES, SITE_URL
UA = {'User-Agent': 'Mozilla/5.0 (compatible; KleoReleaseCheck/1.0; +https://kleooai.com/)', 'Cache-Control': 'no-cache'}

def get(url, headers=None):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={**UA, **(headers or {})}), timeout=30)
        return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)

errors = []
for route, path in PAGES.items():
    st, body, h = get(SITE_URL + route)
    local = (ROOT / path).read_bytes()
    same = hashlib.sha256(body).digest() == hashlib.sha256(local).digest()
    print('%s %-32s %s' % (st, route, 'same bytes' if same else 'DIFFERENT (%d vs %d)' % (len(body), len(local))))
    if st != 200 or not same: errors.append(route)
for extra, ctype in [('/robots.txt', 'text/plain'), ('/sitemap.xml', 'xml'), ('/sitemap', 'xml'), ('/llms.txt', 'text/plain'), ('/6d501967255b4889a19297ad25fe6c51.txt', 'text/plain'), ('/site.css?v=20260915', 'css'), ('/site.js?v=20260915', 'javascript'), ('/config.json', 'json')]:
    st, body, h = get(SITE_URL + extra)
    ok = st == 200 and ctype in h.get('Content-Type', '')
    print('%s %-42s %s' % (st, extra, h.get('Content-Type', '')))
    if not ok: errors.append(extra)
st, body, h = get(SITE_URL + '/this-page-does-not-exist/')
print('%s /this-page-does-not-exist/ %s' % (st, 'real 404, custom page' if st == 404 and b'This scene was cut' in body else 'UNEXPECTED'))
if st != 404: errors.append('404')
for f in ['realistic-tether.mp4', 'realistic-signal.mp4', 'animation-octopus.mp4', 'cinema.mp4', 'stickman-omg.mp4']:
    st, body, h = get(SITE_URL + '/samples/' + f, {'Range': 'bytes=0-1023'})
    print('%s /samples/%-24s %s %s' % (st, f, h.get('Content-Type', ''), h.get('Content-Range', '')))
    if st != 206: errors.append(f)
key = get(SITE_URL + '/6d501967255b4889a19297ad25fe6c51.txt')[1].decode().strip()
print('IndexNow key file:', 'ok' if key == '6d501967255b4889a19297ad25fe6c51' else 'WRONG')
print('\n%d problems' % len(errors), errors)
sys.exit(1 if errors else 0)
