#!/usr/bin/env python3
"""The video wall: gallery/films.json -> the cards on /gallery/ and the slice on the home.

The video files are NOT in this repo. They live in the Cloudflare R2 bucket `kleo-media`, served at
https://media.kleooai.com/gallery/<slug>.mp4 (1080p, muted), <slug>-p.mp4 (the light loop on the wall) and
<slug>.jpg (the poster). To add a film: upload the three files, add one entry to gallery/films.json, run

    python3 tools/gallery.py && python3 tools/check.py

Each page keeps its wall between the markers <!-- wall:start --> and <!-- wall:end -->; nothing else is touched.
Entries with "home": true also appear on the home, in the order of the file.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://media.kleooai.com/gallery/'
PAGES = {'gallery/index.html': False, 'index.html': True}   # page -> home slice only
MARK = re.compile(r'(<!-- wall:start -->)(.*?)(\n\s*<!-- wall:end -->)', re.S)


def card(f, indent):
    e = lambda s: html.escape(str(s), quote=True)
    ar = '%d/%d' % (f['w'], f['h'])
    shape = '9:16' if f['h'] > f['w'] else '16:9'
    meta = '%s · %s s · %s' % (f['kind'], f['dur'], shape)
    url = BASE + f['slug']
    lines = [
        '<figure class="wall-item" data-tags="%s" data-full="%s.mp4" data-poster="%s.jpg">' % (e(' '.join(f['tags'])), url, url),
        ' <div class="wall-media" style="--ar:%s"><video src="%s-p.mp4" poster="%s.jpg" width="%d" height="%d" muted loop playsinline preload="none" disablepictureinpicture disableremoteplayback controlslist="nodownload nofullscreen noremoteplayback" aria-label="%s"></video></div>'
        % (ar, url, url, f['w'], f['h'], e(f['alt'])),
        ' <button class="wall-open" type="button" aria-label="Watch %s larger"></button>' % e(f['title']),
        ' <figcaption class="wall-cap"><div><b>%s</b><span>%s</span></div>%s</figcaption>' % (
            e(f['title']), e(meta),
            '<button class="wall-copy" type="button" data-copy="%s" aria-label="Copy the prompt of %s">Copy prompt</button>' % (e(f['prompt']), e(f['title'])) if f.get('prompt') else ''),
        '</figure>',
    ]
    return '\n'.join(indent + l for l in lines)


def main():
    films = json.loads((ROOT / 'gallery/films.json').read_text(encoding='utf-8'))
    for page, home_only in PAGES.items():
        p = ROOT / page
        src = p.read_text(encoding='utf-8')
        m = MARK.search(src)
        if not m:
            raise SystemExit('%s: no <!-- wall:start --> / <!-- wall:end --> markers' % page)
        indent = re.search(r'([ \t]*)<!-- wall:start -->', src).group(1)
        chosen = [f for f in films if f.get('home')] if home_only else films
        body = '\n' + '\n'.join(card(f, indent) for f in chosen)
        p.write_text(src[:m.start(2)] + body + src[m.end(2):], encoding='utf-8', newline='\n')
        print('%s: %d films' % (page, len(chosen)))


if __name__ == '__main__':
    main()
