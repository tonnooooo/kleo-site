#!/usr/bin/env python3
"""The videos of the site: gallery/films.json -> every looping video card, on /gallery/ and on every other page.

The video files are NOT in this repo. They live in the Cloudflare R2 bucket `kleo-media`, served at
https://media.kleooai.com/gallery/<slug>.mp4 (the full copy, muted, for the viewer), <slug>-p.mp4 (the light loop on
a card), <slug>-h1.mp4, -h2.mp4 ... (other short loops of the same video, for variety from page to page) and
<slug>.jpg (the poster; an entry's "poster" field names another file when the usual frame must not be shown).
To add a video: upload the files, add one entry to gallery/films.json, run

    python3 tools/gallery.py && python3 tools/check.py

films.json, one entry per video: slug, title, line (one sentence under the card), alt (what is on screen), kind, dur
(seconds), w and h, section, prompt (a copyable Kleo prompt, or ""), and for the newer entries `by` (how the Kleo
team made it, shown in the viewer), `hl` (the -hN loops that may be shown; a loop that shows something the site must
not say, such as an old price, is simply left out) and `full: false` when the full copy must not open in the viewer
(the card then loops without the button and the badge). A Kleo Templates result (kind "Template") also carries `app`,
the template's key in the app ("trend-window-peeper"): the site ignores it, the app's Explore opens that template.

1. The gallery: every section is a grid of identical cards ("ads-wide" 2 per row, "ads-tall" 4, "wide" 3, "tall" 4,
   "series" 3) between <!-- wall:<section>:start --> and <!-- wall:<section>:end --> on /gallery/; the home keeps
   `home-wide` (the first 3 "wide" films with "home": true) and `home-tall` (the first 4 "tall" ones).
2. Every other placement is written in the page itself, as a marker naming the loops it shows:
       <!-- vids:hero kleo-x-claude-ad -->      one card that starts at once (autoplay): the page's showcase loop
       <!-- vids:grid kleo-x-claude-ad:h2 kleo-reel-r3-wide lighthouse-sketch-ad:h1 -->   a row of cards
       <!-- vids:viewer -->                     the larger silent viewer the cards open
   each closed by <!-- /vids -->. `slug` alone is the -p loop, `slug:h2` the -h2 loop. Only the hero autoplays; the
   other cards are fetched and played by site.js only while they are on screen. This script rewrites what is between
   the markers and nothing else, so the heading line above a grid is ordinary HTML in the page.
3. The guides (guides/**/index.html, written by tools/build_guides.py) get a hero loop and a closing row of cards
   automatically: a guide page without markers receives them here, so run this script again after build_guides.py.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://media.kleooai.com/gallery/'
APP = 'https://app.kleooai.com/'
WIDE = {'wide', 'ads-wide'}
SECTIONS = ('ads-wide', 'ads-tall', 'wide', 'tall', 'series')
GRIDS = {
    'gallery/index.html': {s: (lambda s: lambda fs: [f for f in fs if f['section'] == s])(s) for s in SECTIONS},
    'index.html': {'home-wide': lambda fs: [f for f in fs if f['section'] == 'wide' and f.get('home')][:3],
                   'home-tall': lambda fs: [f for f in fs if f['section'] == 'tall' and f.get('home')][:4]},
}
VIDS = re.compile(r'([ \t]*)<!-- vids:(hero|grid|viewer)((?: [a-z0-9:-]+)*) -->.*?<!-- /vids -->', re.S)


def esc(s):
    return html.escape(str(s), quote=True)


def wide(f):
    return f['section'] in WIDE


def seconds(f):
    return '%g' % f['dur']


def loops(f):
    return ['p'] + list(f.get('hl', []))


def card(f, indent, loop='p', hero=False):
    url = BASE + f['slug']
    src = url + ('-p.mp4' if loop == 'p' else '-%s.mp4' % loop)
    poster = BASE + f.get('poster', f['slug']) + '.jpg'
    full = f.get('full', True)
    meta = '%s · %s s · %s' % (f['kind'], seconds(f), '16:9' if wide(f) else '9:16')
    if f.get('by'):
        meta += ' · made by the Kleo team ' + f['by']
    cls = 'wall-item' + ('' if full else ' loop-only') + (' vhero' if hero else '')
    data = (' data-full="%s.mp4" data-poster="%s" data-meta="%s" data-prompt="%s"' % (url, poster, esc(meta), esc(f.get('prompt', '')))
            if full else '')
    video = ('<video src="%s" poster="%s" width="%d" height="%d"%s muted loop playsinline preload="none" disablepictureinpicture'
             ' disableremoteplayback controlslist="nodownload nofullscreen noremoteplayback" aria-label="%s"></video>'
             % (src, poster, f['w'], f['h'], ' autoplay' if hero else '', esc(f['alt'])))
    badge = '<span class="wall-dur" aria-hidden="true">%s s</span>' % seconds(f) if full else ''
    lines = ['<figure class="%s"%s>' % (cls, data),
             ' <div class="wall-media%s">%s%s</div>' % (' w' if wide(f) else '', video, badge)]
    if full:
        lines.append(' <button class="wall-open" type="button" aria-label="Watch %s larger"></button>' % esc(f['title']))
    lines += [' <figcaption class="wall-cap"><b>%s</b><span>%s</span></figcaption>' % (esc(f['title']), esc(f['line'])),
              '</figure>']
    return '\n'.join(indent + l for l in lines)


VIEWER = '''<dialog class="viewer" id="viewer" aria-label="Film viewer">
  <div class="viewer-shell">
    <button class="viewer-close" type="button" aria-label="Close the viewer">×</button>
    <div class="viewer-box">
      <div class="viewer-frame"><video muted loop playsinline preload="none" disablepictureinpicture disableremoteplayback controlslist="nodownload nofullscreen noremoteplayback" aria-label="The film, larger and silent"></video></div>
      <div class="viewer-text">
        <h3>Film</h3>
        <p class="viewer-meta"></p>
        <blockquote></blockquote>
        <div class="viewer-actions">
          <button class="btn btn-primary btn-sm" type="button" data-copy="" aria-label="Copy the prompt of this film">Copy prompt</button>
          <a class="btn btn-ghost btn-sm" href="%s">Open Kleo</a>
        </div>
      </div>
    </div>
  </div>
</dialog>''' % APP


def interleave(films):
    """Every loop of every film, one film after another (p of each, then h1 of each, ...): neighbours differ."""
    out, depth = [], max(len(loops(f)) for f in films)
    for i in range(depth):
        out += ['%s%s' % (f['slug'], '' if i == 0 else ':' + loops(f)[i]) for f in films if i < len(loops(f))]
    return out


def pick(pool, start, count, avoid):
    chosen, slugs, i = [], set(avoid), start
    while len(chosen) < count:
        clip = pool[i % len(pool)]
        if clip.split(':')[0] not in slugs:
            chosen.append(clip)
            slugs.add(clip.split(':')[0])
        i += 1
    return chosen


def add_guide_markers(films):
    """A guide page without markers gets a hero loop beside its title and a closing row of cards (see 3. above)."""
    tall = interleave([f for f in films if not wide(f)])
    wides = interleave([f for f in films if wide(f)])
    pages = sorted(ROOT.glob('guides/**/index.html'))
    for n, p in enumerate(pages):
        src = p.read_text(encoding='utf-8')
        if '<!-- vids:' in src:
            continue
        hero = tall[(n * 7) % len(tall)]
        head = '<section class="page-hero hero"><div class="wrap">\n'
        a = src.index(head)
        b = src.index('\n</div></section>', a)
        inner = src[a + len(head):b]
        src = (src[:a] + '<section class="page-hero hero has-vid vid-tall"><div class="wrap">\n<div>\n' + inner +
               '\n</div>\n<!-- vids:hero %s -->\n<!-- /vids -->' % hero + src[b:])
        if n % 2:
            grid, kind = pick(tall, (n // 2) * 4 + 3, 4, [hero.split(':')[0]]), 'tall'
        else:
            grid, kind = pick(wides, (n // 2) * 3, 3, []), 'wide'
        strip = ('<section class="vsection" aria-labelledby="watch-title"><div class="wrap">\n'
                 '<div class="wall-head"><div><h2 id="watch-title">Made by the Kleo team</h2><p>Ads, spots and short films we made'
                 ' ourselves. Open one to watch it larger, silent.</p></div><a class="btn btn-ghost btn-sm" href="/gallery/">All the'
                 ' videos <span class="arr" aria-hidden="true">→</span></a></div>\n'
                 '<div class="wall-grid %s strip">\n<!-- vids:grid %s -->\n<!-- /vids -->\n</div>\n'
                 '</div></section>\n<!-- vids:viewer -->\n<!-- /vids -->\n' % (kind, ' '.join(grid)))
        m = src.index('</main>')
        src = src[:m] + strip + src[m:]
        p.write_text(src, encoding='utf-8', newline='\n')


def fill(path, src, films, problems):
    by_slug = {f['slug']: f for f in films}
    used = []

    def resolve(clip):
        slug, _, loop = clip.partition(':')
        loop = loop or 'p'
        f = by_slug.get(slug)
        if not f:
            problems.append('%s: unknown video %s' % (path, slug))
        elif loop not in loops(f):
            problems.append('%s: %s has no loop %s that may be shown' % (path, slug, loop))
        else:
            used.append(clip)
            return f, loop
        return None, None

    def sub(m):
        indent, kind, args = m.group(1), m.group(2), m.group(3).split()
        if kind == 'viewer':
            body = '\n'.join(indent + l for l in VIEWER.split('\n'))
        else:
            cards = [resolve(c) for c in args]
            cards = [(f, loop) for f, loop in cards if f]
            if kind == 'hero' and len(cards) != 1:
                problems.append('%s: a hero shows exactly one video' % path)
            if kind == 'grid' and len({wide(f) for f, _ in cards}) > 1:
                problems.append('%s: a grid mixes 16:9 and 9:16 (%s)' % (path, ' '.join(args)))
            if kind == 'hero' and cards:
                section = src[:m.start()].rsplit('<section', 1)[-1].split('>', 1)[0]
                if 'page-hero' in section and ('vid-wide' if wide(cards[0][0]) else 'vid-tall') not in section:
                    problems.append('%s: the hero section needs class %s' % (path, 'vid-wide' if wide(cards[0][0]) else 'vid-tall'))
            body = '\n'.join(card(f, indent, loop, kind == 'hero') for f, loop in cards)
        return '%s<!-- vids:%s%s -->\n%s\n%s<!-- /vids -->' % (indent, kind, m.group(3), body, indent)

    out = VIDS.sub(sub, src)
    if len(set(used)) != len(used):
        problems.append('%s: the same loop twice on one page' % path)
    if 'class="wall-open"' in out and 'id="viewer"' not in out:
        problems.append('%s: cards that open the viewer, but no <!-- vids:viewer --> on the page' % path)
    return out


def main():
    films = json.loads((ROOT / 'gallery/films.json').read_text(encoding='utf-8'))
    problems = []
    for page, grids in GRIDS.items():
        p = ROOT / page
        src = p.read_text(encoding='utf-8')
        for name, choose in grids.items():
            m = re.search(r'([ \t]*)<!-- wall:%s:start -->(.*?)(\n[ \t]*<!-- wall:%s:end -->)' % (name, name), src, re.S)
            if not m:
                raise SystemExit('%s: no <!-- wall:%s:start --> / end markers' % (page, name))
            chosen = choose(films)
            body = '\n' + '\n'.join(card(f, m.group(1)) for f in chosen)
            src = src[:m.start(2)] + body + src[m.end(2):]
            print('%s %s: %d films' % (page, name, len(chosen)))
        p.write_text(src, encoding='utf-8', newline='\n')
    add_guide_markers(films)
    pages = videos = 0
    for p in sorted(ROOT.rglob('*.html')):
        if '.git' in p.parts:
            continue
        src = p.read_text(encoding='utf-8')
        if '<!-- vids:' not in src:
            continue
        out = fill(p.relative_to(ROOT).as_posix(), src, films, problems)
        if out != src:
            p.write_text(out, encoding='utf-8', newline='\n')
        pages += 1
        videos += out.count('<figure class="wall-item')
    print('vids markers: %d pages, %d cards' % (pages, videos))
    for x in problems:
        print(' -', x)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
