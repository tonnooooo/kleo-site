#!/usr/bin/env python3
"""Offline checks for kleooai.com — run from the repo root after editing any page. No browser, no network.

What it proves: every HTML page is well-formed (tags balance, ids unique, one h1), every local link, anchor, image,
poster and video points at a file that exists, every indexable page has a unique title, description and absolute
canonical, its JSON-LD parses, the header/footer are the same on every page, the sitemap lists exactly the indexable
pages and each lastmod is a real date, robots.txt names the sitemap, and no page says something the product does not
do (the words in FORBIDDEN). Exit code 1 on any error, so `python3 tools/check.py && git push` is a gate.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json, re, sys, datetime, html
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = 'https://kleooai.com'
# the indexable pages: route → file. The sitemap must list exactly these.
PAGES = {
    '/': 'index.html',
    '/pricing/': 'pricing/index.html',
    '/ai-youtube-video-generator/': 'ai-youtube-video-generator/index.html',
    '/connect/': 'connect/index.html',
    '/integrations/claude/': 'integrations/claude/index.html',
    '/integrations/chatgpt/': 'integrations/chatgpt/index.html',
    '/video-generation-mcp/': 'video-generation-mcp/index.html',
    '/examples/': 'examples/index.html',
    '/examples/tether/': 'examples/tether/index.html',
    '/examples/signal-delay/': 'examples/signal-delay/index.html',
    '/examples/octopus/': 'examples/octopus/index.html',
    '/examples/apex/': 'examples/apex/index.html',
    '/examples/kleo-ad/': 'examples/kleo-ad/index.html',
    '/styles.html': 'styles.html',
    '/faq/': 'faq/index.html',
    '/about/': 'about/index.html',
    '/terms.html': 'terms.html',
    '/privacy.html': 'privacy.html',
}
# Authored guide routes are generated from editorial/*.txt, shared by sitemap and live checks.
PAGES.update(json.loads((ROOT / 'editorial/routes.json').read_text()))
NOINDEX = ['404.html']
# The four dedicated watch pages have one accessible primary player. All other
# videos remain silent previews without controls, including the homepage Apex.
WATCH_PAGES = {
    'examples/kleo-ad/index.html',
    'examples/apex/index.html', 'examples/tether/index.html',
    'examples/octopus/index.html', 'examples/signal-delay/index.html',
}
# things the product does not do, or the site must not say (case-insensitive regexes over the visible text)
FORBIDDEN = [
    (r'\b8[ -]?min', 'films are 15 s to 5 min'),
    (r'\bfree film\b|\bfilm (is|for) free\b|\bone film free\b|\bfree short\b', 'the starter credits do not buy a film'),
    (r'\bapple\b', 'no Apple reference'),
    (r'\bviral\b', 'no virality claims'),
    (r'\btemplates?\b', 'the product has no templates (one workflow, film)'),
    (r'\bcartoon\.mp4|cyber\.mp4', 'retired samples (the owner keeps Cinema and Stickman on the looks page, 15 Sep)'),
    (r'(?<!full of )\bstock footage\b(?! is| —|,)', 'no stock footage'),
    (r'\b#1\b|\bnumber one\b|\bbest ai\b|\brank(s|ed|ing)? first\b', 'no ranking claims'),
    (r'\btestimonial|\bcustomers? (say|love)|\brated\b', 'no testimonials or ratings'),
    (r'\bcookies? (banner|consent)|(?<!\bno )\banalytics\b(?! is| are| —| of)', 'no analytics on the site'),
    (r'(?<!\bno )(?<!\bwithout a )\bsubscription\b(?! is not| free)', 'packs are one-off — say "no subscription" only'),
]
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Page(HTMLParser):
    def __init__(self, source, watch_page=False):
        super().__init__(convert_charrefs=True)
        self.tags, self.ids, self.links, self.stack, self.errors, self.jsonld = [], set(), [], [], [], []
        self.text, self._record, self._buf, self._skip = [], False, '', 0
        self.header, self.footer, self._grab = None, None, None
        self.h1 = 0
        self.watch_page, self.watch_count = watch_page, 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        # the chrome: the pill nav (<nav class="nav">) and the footer must be the same markup on every page
        if (tag == 'nav' and 'nav' in a.get('class', '').split()) or tag == 'footer':
            self._grab = [tag, self.getpos()[0]]
        if 'id' in a:
            if a['id'] in self.ids: self.errors.append('duplicate id ' + a['id'])
            self.ids.add(a['id'])
        if tag in ('a', 'link') and a.get('href'): self.links.append(a['href'])
        for k in ('src', 'poster'):
            if a.get(k): self.links.append(a[k])
        if tag == 'img' and 'alt' not in a: self.errors.append('img without alt: ' + a.get('src', '?'))
        if tag == 'video':
            watch = 'data-watch-player' in a
            if watch:
                self.watch_count += 1
                if not self.watch_page or 'main' not in self.stack:
                    self.errors.append('watch player outside a dedicated watch page main element')
                if 'controls' not in a: self.errors.append('watch player without accessible native controls')
                if 'playsinline' not in a: self.errors.append('watch player without inline playback')
                if 'nofullscreen' in a.get('controlslist', '').split(): self.errors.append('watch player blocks full screen')
                if 'autoplay' in a or 'loop' in a: self.errors.append('watch player must respect user-controlled playback')
                if not a.get('src') or not a.get('poster'): self.errors.append('watch player without source or poster')
            elif 'controls' in a:
                self.errors.append('preview video with controls (controls are limited to dedicated watch players)')
            if 'muted' not in a: self.errors.append('video not muted')
            if a.get('preload') != 'none': self.errors.append('video without preload="none"')
            if 'aria-label' not in a: self.errors.append('video without aria-label')
        if tag == 'h1': self.h1 += 1
        if tag == 'script':
            if a.get('type') == 'application/ld+json': self._record, self._buf = True, ''
            else: self._skip += 1
        if tag == 'style': self._skip += 1
        if tag not in VOID: self.stack.append(tag)

    def handle_data(self, data):
        if self._record: self._buf += data
        elif not self._skip: self.text.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self._record:
            try: self.jsonld.append(json.loads(self._buf))
            except json.JSONDecodeError as e: self.errors.append('JSON-LD does not parse: %s' % e)
            self._record = False
        elif tag in ('script', 'style') and self._skip: self._skip -= 1
        if not self.stack or self.stack[-1] != tag: self.errors.append('unbalanced </%s> at line %d' % (tag, self.getpos()[0]))
        else: self.stack.pop()
        if self._grab and tag == self._grab[0]:
            setattr(self, 'header' if tag == 'nav' else tag, (self._grab[1], self.getpos()[0])); self._grab = None

    def meta(self, name, key='name'):
        return [a.get('content', '') for t, a in self.tags if t == 'meta' and a.get(key) == name]


def block(source, span):
    lines = source.split('\n')
    return '\n'.join(lines[span[0] - 1:span[1]]).replace(' aria-current="page"', '')


def main():
    errors = []
    files = sorted(p for p in ROOT.rglob('*.html') if '.git' not in p.parts and 'node_modules' not in p.parts)
    sources = {f: f.read_text(encoding='utf-8') for f in files}
    parsed = {f: Page(s, str(f.relative_to(ROOT)) in WATCH_PAGES) for f, s in sources.items()}
    rel = lambda f: str(f.relative_to(ROOT))
    titles, descs, canonicals = {}, {}, {}
    header_ref = footer_ref = None
    for f, p in parsed.items():
        name = rel(f)
        errors += ['%s: %s' % (name, e) for e in p.errors]
        if p.watch_page and p.watch_count != 1:
            errors.append('%s: expected exactly one primary watch player, got %d' % (name, p.watch_count))
        if p.stack: errors.append('%s: unclosed %s' % (name, p.stack))
        if p.h1 != 1: errors.append('%s: %d h1' % (name, p.h1))
        for link in p.links:
            u = urlsplit(link)
            if u.scheme or u.netloc:
                if u.scheme == 'http' and 'kleooai' in u.netloc: errors.append('%s: http link %s' % (name, link))
                continue
            path = unquote(u.path)
            if not path: target = f
            elif path.startswith('/'): target = ROOT / path.lstrip('/')
            else: target = f.parent / path
            if target.is_dir(): target = target / 'index.html'
            if not target.exists(): errors.append('%s: missing %s' % (name, link))
            elif u.fragment and target in parsed and u.fragment not in parsed[target].ids: errors.append('%s: missing fragment %s' % (name, link))
            if path.endswith('index.html') and path != 'index.html' and not path.startswith('/'): pass
            if '/index.html' in link or link == 'index.html': errors.append('%s: links to index.html instead of the directory route: %s' % (name, link))
        # the visible text must not promise what the product does not do
        text = ' '.join(' '.join(p.text).split())
        for rx, why in FORBIDDEN:
            m = re.search(rx, text, re.I)
            if m: errors.append('%s: says "%s" — %s' % (name, text[max(0, m.start() - 40):m.end() + 40], why))
        if name in NOINDEX:
            if 'noindex' not in ''.join(p.meta('robots')): errors.append('%s: should be noindex' % name)
            continue
        route = next((r for r, fn in PAGES.items() if fn == name), None)
        if route is None: errors.append('%s: html file that is neither in PAGES nor NOINDEX' % name); continue
        m = re.search(r'<title>(.*?)</title>', sources[f], re.S); title = html.unescape(m.group(1).strip()) if m else ''
        if not title: errors.append('%s: no title' % name)
        elif title in titles: errors.append('%s: title duplicates %s' % (name, titles[title]))
        titles[title] = name
        d = p.meta('description')
        if not d or not d[0].strip(): errors.append('%s: no description' % name)
        else:
            if not 70 <= len(d[0]) <= 170: errors.append('%s: description is %d chars' % (name, len(d[0])))
            if d[0] in descs: errors.append('%s: description duplicates %s' % (name, descs[d[0]]))
            descs[d[0]] = name
        c = [a.get('href') for t, a in p.tags if t == 'link' and a.get('rel') == 'canonical']
        if c != [SITE_URL + route]: errors.append('%s: canonical %s, expected %s' % (name, c, SITE_URL + route))
        if p.meta('og:url', 'property') != [SITE_URL + route]: errors.append('%s: og:url differs from canonical' % name)
        if p.meta('og:title', 'property') != [title]: errors.append('%s: og:title differs from title' % name)
        if 'noindex' in ''.join(p.meta('robots')): errors.append('%s: noindex on an indexable page' % name)
        if not p.jsonld: errors.append('%s: no JSON-LD' % name)
        else:
            types = [n.get('@type') for g in p.jsonld for n in (g.get('@graph', [g]) if isinstance(g, dict) else [])]
            for want in ('WebSite', 'WebPage', 'BreadcrumbList'):
                if want not in types: errors.append('%s: JSON-LD without %s' % (name, want))
            for bad in ('AggregateRating', 'Review', 'FAQPage'):
                if bad in types: errors.append('%s: JSON-LD with %s' % (name, bad))
            for g in p.jsonld:
                for n in g.get('@graph', []):
                    if n.get('@type') == 'WebPage' and n.get('url') != SITE_URL + route: errors.append('%s: WebPage.url differs from canonical' % name)
                    if n.get('@type') == 'VideoObject' and 'uploadDate' not in n: errors.append('%s: VideoObject without uploadDate' % name)
        # the only remote resources allowed are the three Google Fonts faces the design has always used
        for t, a in p.tags:
            if t == 'link' and a.get('rel') not in ('canonical', 'alternate') and a.get('href', '').startswith('http') and not a['href'].startswith(('https://fonts.googleapis.com', 'https://fonts.gstatic.com')): errors.append('%s: remote resource %s' % (name, a['href']))
            if t == 'script' and a.get('src', '').startswith('http'): errors.append('%s: remote script' % name)
        if any(t == 'style' for t, a in p.tags): errors.append('%s: inline <style> block (use site.css)' % name)
        if not any(t == 'script' and urlsplit(a.get('src', '')).path == '/site.js' and not urlsplit(a.get('src', '')).netloc for t, a in p.tags): errors.append('%s: site.js not loaded' % name)
        # header/footer identical everywhere
        if p.header and p.footer:
            h, ft = block(sources[f], p.header), block(sources[f], p.footer)
            if header_ref is None: header_ref, footer_ref = (h, name), (ft, name)
            else:
                if h != header_ref[0]: errors.append('%s: header differs from %s' % (name, header_ref[1]))
                if ft != footer_ref[0]: errors.append('%s: footer differs from %s' % (name, footer_ref[1]))
        else: errors.append('%s: no header/footer' % name)
        # aria-current="page" only on a header link that points at this very page
        hdr = block(sources[f], p.header) if p.header else ''
        raw_hdr = '\n'.join(sources[f].split('\n')[p.header[0] - 1:p.header[1]]) if p.header else ''
        marked = re.findall(r'<a([^>]*aria-current="page"[^>]*)>', raw_hdr)
        for m in marked:
            href = re.search(r'href="([^"]*)"', m)
            if not href or href.group(1) != route: errors.append('%s: aria-current on a link to %s' % (name, href.group(1) if href else '?'))
        if 'aria-current="page"' in raw_hdr and not marked: errors.append('%s: aria-current outside a header link' % name)
        if 'class="no-js"' not in sources[f][:200]: errors.append('%s: <html> without class="no-js"' % name)
        if 'id="progress"' not in sources[f]: errors.append('%s: no progress hairline' % name)
        if re.search(r'href="%s"' % re.escape(route), raw_hdr) and not marked: errors.append('%s: header links here without aria-current' % name)
        if re.search(r'aria-current', sources[f].replace(raw_hdr, '')): errors.append('%s: aria-current outside the header' % name)
    # sitemap: exactly the indexable pages, real dates, lastmod not in the future
    sm = ET.parse(ROOT / 'sitemap.xml').getroot()
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    locs = [u.find('s:loc', ns).text for u in sm.findall('s:url', ns)]
    want = [SITE_URL + r for r in PAGES]
    if sorted(locs) != sorted(want): errors.append('sitemap: %s' % (set(locs) ^ set(want)))
    if len(locs) != len(set(locs)): errors.append('sitemap: duplicate loc')
    today = datetime.date.today()
    for u in sm.findall('s:url', ns):
        lm = u.find('s:lastmod', ns)
        if lm is None: errors.append('sitemap: %s without lastmod' % u.find('s:loc', ns).text); continue
        try:
            d = datetime.date.fromisoformat(lm.text[:10])
            if d > today + datetime.timedelta(days=1): errors.append('sitemap: lastmod in the future for %s' % u.find('s:loc', ns).text)
        except ValueError: errors.append('sitemap: bad lastmod %s' % lm.text)
    robots = (ROOT / 'robots.txt').read_text()
    if 'Sitemap: %s/sitemap.xml' % SITE_URL not in robots: errors.append('robots.txt: no https sitemap line')
    if re.search(r'^Disallow:\s*\S', robots, re.M): errors.append('robots.txt: disallows something')
    for must in ('CNAME', '.nojekyll', '6d501967255b4889a19297ad25fe6c51.txt', 'llms.txt', 'config.json', '404.html', 'worker/kleo_worker.py'):
        if not (ROOT / must).exists(): errors.append('missing ' + must)
    if (ROOT / 'CNAME').read_text().strip() != 'kleooai.com': errors.append('CNAME is not kleooai.com')
    if (ROOT / '6d501967255b4889a19297ad25fe6c51.txt').read_text().strip() != '6d501967255b4889a19297ad25fe6c51': errors.append('IndexNow key file content')
    for banned in ('implementation', 'contenus', 'ready-to-deploy', 'audit-pearl'):
        if (ROOT / banned).exists(): errors.append('%s/ must not be published' % banned)
    print('%d html files, %d indexable, %d errors' % (len(files), len(PAGES), len(errors)))
    for e in errors: print(' -', e)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
