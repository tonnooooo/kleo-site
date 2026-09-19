#!/usr/bin/env python3
"""The site in every language of tools/check.py LANGS, built from the English pages. Run from the repo root.

The English pages are the only source. This tool cuts them into translatable pieces (every run of text with its
inline markup, the title, the descriptions, the alt/aria-label texts, the JSON-LD names and descriptions, plus the
few strings site.js prints), keys each piece by a hash of its English text, and keeps one translation memory per
language in tools/i18n/<lang>.json. A page rebuilt from that memory is the English page with every piece replaced,
the links pointing at the same language, the canonical and Open Graph tags at the translated address, the
hreflang alternates of every language, and a language switcher above the footer. When an English sentence changes,
its hash changes, the old translation is dropped and `status` reports the sentence as missing until it is
translated again — the site never shows a translation of a sentence that no longer exists.

  python3 tools/i18n.py status                     what is translated, per language
  python3 tools/i18n.py pending --lang de [--out dir]   write the untranslated pieces of one language for a translator
  python3 tools/i18n.py import --lang de --from dir     read the translator's files back, checked, into the memory
  python3 tools/i18n.py build [--lang de|all]       write /de/… from the memory (and refresh the English pages' chrome)
  python3 tools/i18n.py source                     rebuild tools/i18n/source.json (every English piece, where it is used)

A translator's file is JSON: {"<id>": "<translation>"} — the inline tags of a piece must come back exactly as they
were, the text inside <code> untouched; `import` refuses anything else and says why.
"""
import argparse, hashlib, html, json, re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from check import PAGES, SITE_URL, LANGS, ASSETS_V, lang_route, lang_file

MEM = ROOT / 'tools' / 'i18n'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
# inside a run of text these tags travel with the text (the translator sees and keeps them)
INLINE = {'a', 'b', 'i', 'em', 'strong', 'code', 'span', 'br', 'small', 'kbd', 'sup', 'sub', 'abbr', 'mark', 'time',
          'wbr', 's', 'u', 'q', 'cite', 'var', 'samp', 'bdi', 'bdo', 'del', 'ins', 'label'}
# nothing inside these is text to translate
OPAQUE = {'script', 'style', 'svg', 'pre', 'video', 'audio', 'iframe', 'template', 'textarea', 'select', 'input', 'img',
          'source', 'track', 'canvas', 'object', 'math', 'noscript', 'head', '!comment'}
ATTRS = ('alt', 'aria-label', 'title', 'placeholder')
SKIP_ATTR_IDS = {'line'}            # the spoken line on the looks page: the shots cut on its English word indices
LD_TEXT = {'name', 'description', 'headline', 'alternativeHeadline', 'caption', 'text', 'operatingSystem', 'abstract'}
LD_URL = {'url', '@id', 'item', 'target', 'mainEntityOfPage'}
LD_SHARED = {'website', 'software', 'organization', 'person'}   # #fragments of the one site-wide node, never per language
HEAD_MARK = ('<!-- i18n:head -->', '<!-- /i18n:head -->')
LANGS_MARK = ('<!-- i18n:langs -->', '<!-- /i18n:langs -->')
ALIASES = {'zh-hk': 'zh-tw', 'zh-mo': 'zh-tw', 'zh-hant': 'zh-tw', 'zh-hans': 'zh', 'zh-cn': 'zh', 'zh-sg': 'zh', 'nb': 'no', 'nn': 'no'}


# ---------------------------------------------------------------- a tree with byte offsets
class Tree(HTMLParser):
    """Every element with the offsets of its start tag, its end tag and its content in the raw source."""

    def __init__(self, raw):
        super().__init__(convert_charrefs=False)
        self.raw, self.root, self.stack = raw, {'tag': '#root', 'attrs': {}, 'children': [], 'start': 0, 'open_end': 0, 'close_start': len(raw), 'end': len(raw)}, []
        self.lines = [0]
        for i, ch in enumerate(raw):
            if ch == '\n': self.lines.append(i + 1)
        self.feed(raw); self.close()
        while self.stack: self.stack.pop()

    def abs(self):
        line, col = self.getpos(); return self.lines[line - 1] + col

    def parent(self): return self.stack[-1] if self.stack else self.root

    def handle_starttag(self, tag, attrs):
        s = self.abs(); rawtag = self.get_starttag_text()
        node = {'tag': tag, 'attrs': dict(attrs), 'children': [], 'start': s, 'open_end': s + len(rawtag), 'rawtag': rawtag}
        self.parent()['children'].append(node)
        if tag in VOID or rawtag.endswith('/>'):
            node['close_start'] = node['end'] = node['open_end']
        else: self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1]['tag'] == tag and self.stack[-1]['start'] == self.abs():
            n = self.stack.pop(); n['close_start'] = n['end'] = n['open_end']

    def handle_endtag(self, tag):
        s = self.abs(); e = self.raw.index('>', s) + 1
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]['tag'] == tag:
                for n in self.stack[i + 1:]: n['close_start'] = n['end'] = s   # tags left open: closed here
                n = self.stack[i]; n['close_start'], n['end'] = s, e
                del self.stack[i:]
                return

    def _leaf(self, tag, length):
        s = self.abs(); self.parent()['children'].append({'tag': tag, 'attrs': {}, 'children': [], 'start': s, 'open_end': s + length, 'close_start': s + length, 'end': s + length})

    def handle_comment(self, data): self._leaf('!comment', len(data) + 7)
    def handle_decl(self, data): self._leaf('!decl', len(data) + 3)
    def handle_pi(self, data): self._leaf('!pi', len(data) + 2)
    def unknown_decl(self, data): self._leaf('!decl', len(data) + 3)


def walk(node):
    yield node
    for c in node['children']: yield from walk(c)


def find(node, tag, **attrs):
    for n in walk(node):
        if n['tag'] == tag and all(n['attrs'].get(k) == v for k, v in attrs.items()): yield n


def is_inline(node, memo):
    key = id(node)
    if key not in memo:
        memo[key] = node['tag'] in INLINE and node['tag'] not in OPAQUE and all(is_inline(c, memo) or c['tag'] == '!comment' for c in node['children'])
    return memo[key]


def items(node, raw):
    """The children of an element with the text between them, in order: ('text', s, e) or the child node."""
    out, pos = [], node['open_end']
    for c in node['children']:
        if c['start'] > pos: out.append(('text', pos, c['start']))
        out.append(c); pos = c['end']
    if node['close_start'] > pos: out.append(('text', pos, node['close_start']))
    return out


def is_text(it): return isinstance(it, tuple)
def norm(s): return ' '.join(s.split())
def sid(kind, text): return hashlib.sha1((kind + '\x00' + norm(text)).encode('utf-8')).hexdigest()[:10]
def has_letters(s): return re.search(r'[^\W\d_]', html.unescape(re.sub(r'<[^>]+>', '', s))) is not None


class Piece:
    __slots__ = ('kind', 'src', 'id', 's', 'e', 'where')

    def __init__(self, kind, src, s, e, where):
        self.kind, self.src, self.s, self.e, self.where = kind, src, s, e, where
        self.id = sid('html' if kind == 'html' else 'text', src)


def attr_span(node, name):
    """Offsets of the value of an attribute inside the start tag, or None."""
    m = re.search(r'\s%s=(?:"([^"]*)"|\'([^\']*)\')' % re.escape(name), node['rawtag'])
    if not m: return None
    g = 1 if m.group(1) is not None else 2
    return node['start'] + m.start(g), node['start'] + m.end(g)


def pieces(raw, tree, excluded):
    """Every translatable piece of one page: html runs, attributes, title, metas, JSON-LD texts."""
    out, memo = [], {}
    body = next(find(tree.root, 'body'), None)

    def inside_excluded(s, e): return any(s >= a and e <= b for a, b in excluded)

    def flush(run, where):
        while run and is_text(run[0]) and not raw[run[0][1]:run[0][2]].strip(): run.pop(0)
        while run and is_text(run[-1]) and not raw[run[-1][1]:run[-1][2]].strip(): run.pop()
        if not run: return
        if len(run) == 1 and not is_text(run[0]): collect(run[0], where); return   # one inline element alone: its content
        s = run[0][1] if is_text(run[0]) else run[0]['start']
        e = run[-1][2] if is_text(run[-1]) else run[-1]['end']
        frag = raw[s:e]
        if is_text(run[0]): frag = frag.lstrip(); s = e - len(frag)
        if is_text(run[-1]): frag = frag.rstrip(); e = s + len(frag)
        if has_letters(frag) and not inside_excluded(s, e): out.append(Piece('html', frag, s, e, where))

    def collect(node, where):
        if node['tag'] in OPAQUE: return
        here = where if node['tag'] in INLINE else node['tag'] + ('#' + node['attrs']['id'] if node['attrs'].get('id') else '')
        run = []
        for it in items(node, raw):
            if is_text(it) or is_inline(it, memo): run.append(it)
            else:
                flush(run, here); run = []
                if it['tag'] != '!comment': collect(it, here)
        flush(run, here)

    if body: collect(body, 'body')
    # attributes with words in them, on every element outside svg — unless the element sits inside a collected run
    runs = [(p.s, p.e) for p in out]
    for n in walk(tree.root):
        if n['tag'].startswith('!') or n['tag'] in ('svg', 'path', 'meta', 'link', 'title'): continue
        if any(n['start'] >= a and n['end'] <= b for a, b in runs): continue
        if n['attrs'].get('id') in SKIP_ATTR_IDS: continue
        for a in ATTRS:
            v = n['attrs'].get(a)
            if v and has_letters(v):
                span = attr_span(n, a)
                if span and not inside_excluded(*span): out.append(Piece('attr', html.unescape(raw[span[0]:span[1]]), span[0], span[1], n['tag'] + '[' + a + ']'))
    t = next(find(tree.root, 'title'), None)
    if t: out.append(Piece('title', html.unescape(raw[t['open_end']:t['close_start']]), t['open_end'], t['close_start'], 'title'))
    for n in find(tree.root, 'meta'):
        key = n['attrs'].get('name') or n['attrs'].get('property') or ''
        if key in ('description', 'twitter:title', 'twitter:description', 'og:title', 'og:description', 'og:image:alt') and n['attrs'].get('content'):
            span = attr_span(n, 'content')
            out.append(Piece('meta', html.unescape(raw[span[0]:span[1]]), span[0], span[1], 'meta ' + key))
    for n in find(tree.root, 'script', type='application/ld+json'):
        try: obj = json.loads(raw[n['open_end']:n['close_start']])
        except json.JSONDecodeError: continue
        for s in ld_texts(obj): out.append(Piece('ld', s, n['open_end'], n['close_start'], 'json-ld'))
    return out


def ld_texts(obj, out=None):
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in LD_TEXT and isinstance(v, str) and has_letters(v): out.append(v)
            else: ld_texts(v, out)
    elif isinstance(obj, list):
        for v in obj: ld_texts(v, out)
    return out


def ld_translate(obj, mem, lang, missing):
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            if k in LD_TEXT and isinstance(v, str) and has_letters(v):
                t = mem.get(sid('text', v))
                if t is None: missing.append(v); t = v
                new[k] = t
            elif k in LD_URL and isinstance(v, str) and v.startswith(SITE_URL + '/'):
                new[k] = lang_url(v, lang)
            elif k == 'inLanguage' and v == 'en': new[k] = LANGS[lang][0]
            else: new[k] = ld_translate(v, mem, lang, missing)
        return new
    if isinstance(obj, list): return [ld_translate(v, mem, lang, missing) for v in obj]
    return obj


def lang_url(url, lang):
    """An absolute or root-relative address of an English page → the same page in `lang`; anything else unchanged."""
    m = re.match(r'^(%s)?(/[^#?]*)(\?[^#]*)?(#.*)?$' % re.escape(SITE_URL), url)
    if not m: return url
    base, path, query, frag = m.group(1) or '', m.group(2), m.group(3) or '', m.group(4) or ''
    if path not in PAGES or (frag and frag[1:] in LD_SHARED): return url
    return base + lang_route(lang, path) + query + frag


def excluded_regions(raw):
    out = []
    for a, b in (HEAD_MARK, LANGS_MARK):
        i, j = raw.find(a), raw.find(b)
        if i >= 0 and j > i: out.append((i, j + len(b)))
    return out


# ---------------------------------------------------------------- the memory
def load_mem(lang):
    f = MEM / (lang + '.json')
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}


def save_mem(lang, mem):
    MEM.mkdir(exist_ok=True)
    (MEM / (lang + '.json')).write_text(json.dumps(dict(sorted(mem.items())), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def extra_strings():
    f = MEM / 'extra.json'
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else []


def all_pieces():
    """id → (kind, source, [where…]) over every English page and the extra strings, in page order."""
    out = {}
    for route, file in PAGES.items():
        raw = (ROOT / file).read_text(encoding='utf-8')
        for p in pieces(raw, Tree(raw), excluded_regions(raw)):
            out.setdefault(p.id, [p.kind, norm(p.src) if p.kind == 'html' else p.src, []])[2].append(file + ' ' + p.where)
    for s in extra_strings():
        out.setdefault(sid('text', s), ['extra', s, []])[2].append('site.js')
    return out


# ---------------------------------------------------------------- import: the translator's files, checked
def tags_of(s): return [re.sub(r'\s+', ' ', t) for t in re.findall(r'<[^>]+>', s)]
def codes_of(s): return re.findall(r'<code[^>]*>(.*?)</code>', s, re.S)


def check_piece(kind, src, tr):
    if not isinstance(tr, str) or not tr.strip(): return 'empty'
    if kind == 'html':
        if tags_of(src) != tags_of(tr): return 'inline tags differ: %s → %s' % (tags_of(src), tags_of(tr))
        if codes_of(src) != codes_of(tr): return 'text inside <code> changed'
    else:
        if '<' in tr and '<' not in src: return 'markup in a plain-text piece'
    if re.search(r'&(?!(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);)', tr) and not re.search(r'&(?!(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);)', src): return 'a bare & (write &amp;)'
    return None


def cmd_import(lang, src_dir):
    known, mem = all_pieces(), load_mem(lang)
    added, bad = 0, []
    for f in sorted(Path(src_dir).glob('*.json')):
        try: data = json.loads(f.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e: bad.append('%s: not JSON (%s)' % (f.name, e)); continue
        strings = data.get('strings', data) if isinstance(data, dict) else {}
        for pid, tr in strings.items():
            if isinstance(tr, dict): tr = tr.get('tr', tr.get(lang))
            if pid not in known: bad.append('%s: unknown id %s' % (f.name, pid)); continue
            kind, src = known[pid][0], known[pid][1]
            why = check_piece(kind, src, tr)
            if why: bad.append('%s: %s — %s\n     en: %s\n     %s: %s' % (f.name, pid, why, src[:160], lang, str(tr)[:160])); continue
            mem[pid] = norm(tr) if kind == 'html' else tr.strip()
            added += 1
    for pid in [p for p in mem if p not in known]: del mem[pid]   # translations of sentences that no longer exist
    save_mem(lang, mem)
    print('%s: %d pieces imported, %d in memory, %d missing, %d refused' % (lang, added, len(mem), len([p for p in known if p not in mem]), len(bad)))
    for b in bad: print(' -', b)
    return 1 if bad else 0


def cmd_pending(lang, out_dir):
    known, mem = all_pieces(), load_mem(lang)
    out = Path(out_dir) / lang; out.mkdir(parents=True, exist_ok=True)
    for f in out.glob('*.json'): f.unlink()
    by_file, seen = {}, set()
    for pid, (kind, src, where) in known.items():
        if pid in mem: continue
        file = where[0].split(' ')[0]
        by_file.setdefault(file, {})[pid] = {'en': src, 'kind': kind, 'where': where[0].split(' ', 1)[1] if ' ' in where[0] else ''}
    order = ['site.js'] + list(PAGES.values())
    n = 0
    for i, file in enumerate(order):
        if file not in by_file: continue
        name = '%02d-%s.json' % (i, re.sub(r'[^a-z0-9]+', '-', file.replace('/index.html', '').replace('.html', '')).strip('-') or 'home')
        (out / name).write_text(json.dumps({'lang': lang, 'page': file, 'strings': by_file[file]}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        n += len(by_file[file])
    print('%s: %d pieces to translate in %s' % (lang, n, out))


def cmd_status():
    known = all_pieces()
    print('%d English pieces (%d html runs, %d attributes/titles/metas, %d JSON-LD, %d site.js)' % (
        len(known), sum(1 for v in known.values() if v[0] == 'html'), sum(1 for v in known.values() if v[0] in ('attr', 'title', 'meta')),
        sum(1 for v in known.values() if v[0] == 'ld'), sum(1 for v in known.values() if v[0] == 'extra')))
    for lang in LANGS:
        mem = load_mem(lang); have = sum(1 for p in known if p in mem)
        print('  %-6s %4d / %d%s' % (lang, have, len(known), '' if have == len(known) else '   missing %d' % (len(known) - have)))


def cmd_source():
    known = all_pieces()
    MEM.mkdir(exist_ok=True)
    (MEM / 'source.json').write_text(json.dumps({k: {'kind': v[0], 'en': v[1], 'where': v[2]} for k, v in known.items()}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('%d pieces → tools/i18n/source.json' % len(known))


# ---------------------------------------------------------------- build
def head_block(lang, route):
    lines = [HEAD_MARK[0]]
    for code in ['en'] + list(LANGS):
        lines.append('<link rel="alternate" hreflang="%s" href="%s%s">' % ('en' if code == 'en' else LANGS[code][0], SITE_URL, lang_route(code, route)))
    lines.append('<link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE_URL, route))
    # the visitor's language: an explicit choice (the switcher, kept in localStorage) wins; otherwise the browser's
    # preferred languages, the first one that is either English or a language the site has. Same page, other folder.
    lines.append('<script>(function(){try{var L=%s,A=%s,p=location.pathname,m=p.match(/^\\/([a-z]{2}(?:-[a-z]{2})?)(?=\\/)/),on=m&&L.indexOf(m[1])>=0?m[1]:"en",rest=on==="en"?p:p.slice(on.length+1),want=null,s=null;'
                 'try{s=localStorage.getItem("kleo-lang")}catch(e){}if(s==="en"||L.indexOf(s)>=0)want=s;else{var nl=navigator.languages||[navigator.language||""];'
                 'for(var i=0;i<nl.length&&!want;i++){var t=String(nl[i]).toLowerCase(),b=t.split("-")[0];t=A[t]||t;b=A[b]||b;want=t==="en"||b==="en"?"en":L.indexOf(t)>=0?t:L.indexOf(b)>=0?b:null}}'
                 'if(want&&want!==on&&!/404/.test(p))location.replace((want==="en"?"":"/"+want)+rest+location.search+location.hash)}catch(e){}})()</script>'
                 % (json.dumps(list(LANGS)), json.dumps(ALIASES)))
    if lang != 'en':
        mem = load_mem(lang)
        strings = {s: mem[sid('text', s)] for s in extra_strings() if sid('text', s) in mem}
        lines.append('<script type="application/json" id="i18n">%s</script>' % json.dumps(strings, ensure_ascii=False).replace('</', '<\\/'))
    lines.append(HEAD_MARK[1])
    return '\n'.join(lines)


def langs_block(lang, route, mem):
    label = mem.get(sid('text', 'Language'), 'Language') if lang != 'en' else 'Language'
    links = []
    for code in ['en'] + list(LANGS):
        tag, name = ('en', 'English') if code == 'en' else LANGS[code][:2]
        if code == lang: links.append('<b lang="%s">%s</b>' % (tag, name))
        else: links.append('<a href="%s" hreflang="%s" lang="%s">%s</a>' % (lang_route(code, route), tag, tag, name))
    return '%s\n<nav class="langs" aria-label="%s">\n  <div class="wrap">\n    <span>%s</span>\n    %s\n  </div>\n</nav>\n%s' % (
        LANGS_MARK[0], html.escape(label, quote=True), html.escape(label), '\n    '.join(links), LANGS_MARK[1])


def replace_block(raw, mark, new):
    i, j = raw.find(mark[0]), raw.find(mark[1])
    if i < 0 or j < i: raise SystemExit('missing markers %s in a page: run `init` first' % mark[0])
    return raw[:i] + new + raw[j + len(mark[1]):]


def build_page(lang, route, file):
    raw = (ROOT / file).read_text(encoding='utf-8')
    mem = load_mem(lang) if lang != 'en' else {}
    missing = []
    if lang != 'en':
        tree = Tree(raw); ops = []
        for p in pieces(raw, tree, excluded_regions(raw)):
            if p.kind == 'ld': continue
            t = mem.get(p.id)
            if t is None: missing.append(p.src); continue
            ops.append((p.s, p.e, t if p.kind == 'html' else html.escape(t, quote=True)))
        for n in find(tree.root, 'script', type='application/ld+json'):
            try: obj = json.loads(raw[n['open_end']:n['close_start']])
            except json.JSONDecodeError: continue
            ops.append((n['open_end'], n['close_start'], '\n' + json.dumps(ld_translate(obj, mem, lang, missing), ensure_ascii=False, indent=2) + '\n'))
        for s, e, t in sorted(ops, reverse=True): raw = raw[:s] + t + raw[e:]
        # the links, the canonical, Open Graph and the document language
        raw = re.sub(r'(<a\b[^>]*\shref=")([^"]*)(")', lambda m: m.group(1) + lang_url(m.group(2), lang) + m.group(3), raw)
        raw = re.sub(r'(<link rel="canonical" href=")([^"]*)(")', lambda m: m.group(1) + lang_url(m.group(2), lang) + m.group(3), raw)
        raw = re.sub(r'(<meta property="og:url" content=")([^"]*)(")', lambda m: m.group(1) + lang_url(m.group(2), lang) + m.group(3), raw)
        raw = raw.replace('<meta property="og:locale" content="en_US">', '<meta property="og:locale" content="%s">' % LANGS[lang][2])
        raw = re.sub(r'^<html lang="en"', '<html lang="%s"%s' % (LANGS[lang][0], ' dir="rtl"' if LANGS[lang][3] == 'rtl' else ''), raw, count=1, flags=re.M)
    raw = replace_block(raw, HEAD_MARK, head_block(lang, route))
    raw = replace_block(raw, LANGS_MARK, langs_block(lang, route, mem))
    out = ROOT / lang_file(lang, file)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists() or out.read_text(encoding='utf-8') != raw: out.write_text(raw, encoding='utf-8')
    return missing


def cmd_build(which):
    langs = ['en'] + list(LANGS) if which == 'all' else [which]
    for lang in langs:
        missing = set()
        for route, file in PAGES.items(): missing.update(build_page(lang, route, file))
        print('%-6s %d pages%s' % (lang, len(PAGES), '' if not missing else ' — %d pieces still in English' % len(missing)))


def cmd_init():
    """Put the two marker blocks into every English page once (the head block after the canonical, the switcher before the footer)."""
    for file in PAGES.values():
        p = ROOT / file; raw = p.read_text(encoding='utf-8')
        if HEAD_MARK[0] not in raw:
            raw = re.sub(r'(<link rel="canonical" href="[^"]*">\n)', lambda m: m.group(1) + HEAD_MARK[0] + '\n' + HEAD_MARK[1] + '\n', raw, count=1)
        if LANGS_MARK[0] not in raw:
            raw = raw.replace('\n<footer>', '\n' + LANGS_MARK[0] + '\n' + LANGS_MARK[1] + '\n\n<footer>', 1)
        p.write_text(raw, encoding='utf-8')
    print('markers in %d pages' % len(PAGES))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['status', 'pending', 'import', 'build', 'source', 'init'])
    ap.add_argument('--lang', default='all')
    ap.add_argument('--out', default=str(ROOT / 'tools' / 'i18n' / 'pending'))
    ap.add_argument('--from', dest='src', default=None)
    a = ap.parse_args()
    if a.cmd != 'build' and a.cmd not in ('status', 'source', 'init') and a.lang not in LANGS: raise SystemExit('--lang must be one of ' + ', '.join(LANGS))
    if a.cmd == 'status': cmd_status()
    elif a.cmd == 'source': cmd_source()
    elif a.cmd == 'init': cmd_init()
    elif a.cmd == 'pending': cmd_pending(a.lang, a.out)
    elif a.cmd == 'import': sys.exit(cmd_import(a.lang, a.src or str(Path(a.out) / a.lang)))
    elif a.cmd == 'build':
        if a.lang != 'all' and a.lang not in LANGS and a.lang != 'en': raise SystemExit('--lang must be all, en or one of ' + ', '.join(LANGS))
        cmd_build(a.lang)


if __name__ == '__main__':
    main()
