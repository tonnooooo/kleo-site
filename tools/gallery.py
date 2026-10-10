#!/usr/bin/env python3
"""The video wall: gallery/films.json -> the cards on /gallery/ and on the home.

The video files are NOT in this repo. They live in the Cloudflare R2 bucket `kleo-media`, served at
https://media.kleooai.com/gallery/<slug>.mp4 (1080p, muted), <slug>-p.mp4 (the light loop on the card) and
<slug>.jpg (the poster). To add a film: upload the three files, add one entry to gallery/films.json, run

    python3 tools/gallery.py && python3 tools/check.py

Every film belongs to one section ("wide" 16:9, "tall" 9:16, "series" three shots of one character); a section is a
grid of identical cards, so keep its count a multiple of its columns (wide 3, tall 4, series 3) or the last row
stays short. Each grid sits between <!-- wall:<name>:start --> and <!-- wall:<name>:end -->: on /gallery/ the names
are the sections, on the home `home-wide` (the first 3 wide films with "home": true) and `home-tall` (the first 4
tall ones). Nothing else in the pages is touched.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://media.kleooai.com/gallery/'
GRIDS = {
    'gallery/index.html': {'wide': lambda fs: [f for f in fs if f['section'] == 'wide'],
                           'tall': lambda fs: [f for f in fs if f['section'] == 'tall'],
                           'series': lambda fs: [f for f in fs if f['section'] == 'series']},
    'index.html': {'home-wide': lambda fs: [f for f in fs if f['section'] == 'wide' and f.get('home')][:3],
                   'home-tall': lambda fs: [f for f in fs if f['section'] == 'tall' and f.get('home')][:4]},
}


def card(f, indent):
    e = lambda s: html.escape(str(s), quote=True)
    url = BASE + f['slug']
    ar = '16/9' if f['section'] == 'wide' else '9/16'
    lines = [
        '<figure class="wall-item" data-full="%s.mp4" data-poster="%s.jpg" data-meta="%s · %s s · %s" data-prompt="%s">'
        % (url, url, e(f['kind']), e(f['dur']), '16:9' if ar == '16/9' else '9:16', e(f.get('prompt', ''))),
        ' <div class="wall-media" style="--ar:%s"><video src="%s-p.mp4" poster="%s.jpg" width="%d" height="%d" muted loop playsinline preload="none" disablepictureinpicture disableremoteplayback controlslist="nodownload nofullscreen noremoteplayback" aria-label="%s"></video><span class="wall-dur" aria-hidden="true">%s s</span></div>'
        % (ar, url, url, f['w'], f['h'], e(f['alt']), e(f['dur'])),
        ' <button class="wall-open" type="button" aria-label="Watch %s larger"></button>' % e(f['title']),
        ' <figcaption class="wall-cap"><b>%s</b><span>%s</span></figcaption>' % (e(f['title']), e(f['line'])),
        '</figure>',
    ]
    return '\n'.join(indent + l for l in lines)


def main():
    films = json.loads((ROOT / 'gallery/films.json').read_text(encoding='utf-8'))
    for page, grids in GRIDS.items():
        p = ROOT / page
        src = p.read_text(encoding='utf-8')
        for name, pick in grids.items():
            m = re.search(r'([ \t]*)<!-- wall:%s:start -->(.*?)(\n[ \t]*<!-- wall:%s:end -->)' % (name, name), src, re.S)
            if not m:
                raise SystemExit('%s: no <!-- wall:%s:start --> / end markers' % (page, name))
            chosen = pick(films)
            body = '\n' + '\n'.join(card(f, m.group(1)) for f in chosen)
            src = src[:m.start(2)] + body + src[m.end(2):]
            print('%s %s: %d films' % (page, name, len(chosen)))
        p.write_text(src, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
