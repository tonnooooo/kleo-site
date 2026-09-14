#!/usr/bin/env python3
"""IndexNow for kleooai.com — tells Bing (and the engines that share the protocol) which pages changed.

Run it only AFTER a deploy, from the repo root, on the commit that is live:

    python3 tools/indexnow.py            # dry run: prints the URLs it would send and the checks it made
    python3 tools/indexnow.py --submit   # sends them

It refuses to submit unless (1) the key file is public at its keyLocation, (2) every URL answers 200 with the same
bytes as the local file — so it never announces a page that is not the one in the repo. Which URLs: those whose file
changed in the commits since the last submission (`--since <commit>`), or all indexable pages with `--all`. A 200/202
receipt is not proof of indexing, only of reception. It does not talk to Google (Google does not use IndexNow).
"""
import argparse, hashlib, json, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from check import PAGES, SITE_URL  # the same inventory the checker enforces

KEY = '6d501967255b4889a19297ad25fe6c51'
UA = {'User-Agent': 'Mozilla/5.0 (compatible; KleoReleaseCheck/1.0; +https://kleooai.com/)'}


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--submit', action='store_true', help='actually send (default: dry run)')
    ap.add_argument('--since', help='git commit: submit only pages whose file changed since it')
    ap.add_argument('--all', action='store_true', help='submit every indexable page')
    a = ap.parse_args()
    if not a.since and not a.all:
        sys.exit('say which pages: --since <commit> or --all')
    routes = list(PAGES)
    if a.since:
        changed = subprocess.run(['git', 'diff', '--name-only', a.since, 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
        routes = [r for r, f in PAGES.items() if f in changed]
        print('changed since %s: %s' % (a.since, ', '.join(routes) or 'nothing'))
    if not routes:
        return
    if fetch('%s/%s.txt' % (SITE_URL, KEY)).decode().strip() != KEY:
        sys.exit('key file is not public — deploy first')
    for r in routes:
        live = fetch(SITE_URL + r)
        local = (ROOT / PAGES[r]).read_bytes()
        if hashlib.sha256(live).digest() != hashlib.sha256(local).digest():
            sys.exit('live %s differs from the repo — deploy (or wait for GitHub Pages) first' % r)
        print('ok  %s' % (SITE_URL + r))
    payload = {'host': 'kleooai.com', 'key': KEY, 'keyLocation': '%s/%s.txt' % (SITE_URL, KEY), 'urlList': [SITE_URL + r for r in routes]}
    if not a.submit:
        print('dry run — would send:\n' + json.dumps(payload, indent=2))
        return
    req = urllib.request.Request('https://api.indexnow.org/indexnow', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json', **UA}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as resp:
        print('IndexNow HTTP %s — receipt only, not proof of indexing' % resp.status)


if __name__ == '__main__':
    main()
