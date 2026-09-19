#!/usr/bin/env python3
"""Rebuild sitemap.xml and llms.txt from the pages themselves.

sitemap.xml lists exactly the indexable pages of tools/check.py, in every language, with, for each, the date of the last commit that
touched its file (or today, for a file not yet committed) — a real modification date, never the build date.
llms.txt repeats each page's title and description, so it cannot drift from the HTML. Run from the repo root.
"""
import datetime, html, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from check import PAGES, ALL_PAGES, SITE_URL


def last_change(path):
    out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', path], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', path], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return datetime.date.today().isoformat() if (dirty or not out) else out


def meta(path):
    s = (ROOT / path).read_text(encoding='utf-8')
    title = html.unescape(re.search(r'<title>(.*?)</title>', s, re.S).group(1).strip())
    desc = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', s).group(1))
    return title, desc


urls = []
for route, path in ALL_PAGES.items():
    urls.append('  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n  </url>' % (SITE_URL, route, last_change(path)))
(ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
    '<!-- Exactly the indexable pages, rebuilt by tools/sitemap.py; lastmod is the last commit that touched the page. -->\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % '\n'.join(urls), encoding='utf-8')

lines = ['# Kleo AI', '',
    '> Kleo makes complete narrated films from a brief, inside the AI assistant you already use: a treatment, a storyboard, every shot generated as moving footage, one narrator, a 4K 60 fps MP4 you download and publish. Two looks, realistic and animation. A remote MCP server with OAuth.',
    '', '## Pages']
for route, path in PAGES.items():
    t, d = meta(path)
    lines.append('- [%s](%s%s): %s' % (t, SITE_URL, route, d))
lines += ['', '## Facts (deployed server, 14 September 2026)', '',
    '15 seconds to 5 minutes; 16:9 or 9:16; English or Italian narration; realistic or animation look; 4K 60 fps MP4; no background music, no captions, no automatic publishing; a render takes about 25–35 minutes on a rented GPU. 1 credit = 2 seconds of film, rounded up, 10 credits minimum. 7 credits on connecting; packs €5 = 10 credits, €15 = 35, €40 = 100, one-off, no subscription. MCP endpoint: https://mcp.kleooai.com/mcp (Streamable HTTP, OAuth 2.1). Contact: kleooai@gmail.com. Source: https://github.com/tonnooooo/kleo-mcp',
    '']
(ROOT / 'llms.txt').write_text('\n'.join(lines), encoding='utf-8')
print('sitemap.xml: %d urls; llms.txt: %d pages' % (len(urls), len(PAGES)))
