# Kleo — the website

Static site for Kleo, the remote MCP server that makes complete narrated films (realistic or animation) from inside
Claude, ChatGPT, Grok, Claude Code, Cursor, VS Code, OpenCode and Gemini CLI. Served by GitHub Pages at
https://kleooai.com/ (CNAME + .nojekyll); no build step: edit the HTML, run the checks, push to `main`, the site
updates within a few minutes.

## Pages

| Route | File | What it is |
|---|---|---|
| `/` | `index.html` | Home: the promise, how it works, the address, price, five FAQ answers. Section ids `how`, `template` (use cases — the word never appears in the text), `engine`, `pricing`, `connect`, `faq`, `account` are stable: links already shared point at them, and `site.js` maps the four old Italian ids (`#come #connetti #prezzi #quinte`). |
| `/ai-youtube-video-generator/` | `ai-youtube-video-generator/index.html` | The guide: brief → treatment → storyboard → render → download. |
| `/connect/` | `connect/index.html` | The hub: one card per client with the tested steps and copyable config. |
| `/integrations/claude/`, `/integrations/chatgpt/` | `integrations/*/index.html` | The two long guides. |
| `/video-generation-mcp/` | `video-generation-mcp/index.html` | The server documented: endpoint, OAuth, the tools in the order they run, the parameters of a render. |
| `/examples/`, `/examples/tether/`, `/examples/signal-delay/` | `examples/**` | The gallery and one page per real film. |
| `/styles.html` | `styles.html` | The two looks, realistic and animation. Historical route, keep the `.html`. |
| `/pricing/` | `pricing/index.html` | Packs, the calculator (`#duration` → `#credit-result`, same rule as the server), the cost table. |
| `/faq/`, `/about/` | `faq/index.html`, `about/index.html` | |
| `/privacy.html`, `/terms.html` | | Historical routes. Legal wording is the owner's; only product facts get corrected. |
| `/404.html` | | Served by GitHub Pages with a real 404 for any unknown path. `noindex`. |

Every page works with JavaScript switched off (the menu, the address, the films' posters, the calculator's table
of costs are all in the markup).

Discovery files: `sitemap.xml` (exactly the indexable pages above; `lastmod` is the date a page really changed, not
the build date — `/sitemap` is the same file, GitHub Pages resolves the extension), `robots.txt` (allows everything,
names the sitemap), `llms.txt` (an optional summary for language models: keep it in step with the titles and
descriptions), `6d501967255b4889a19297ad25fe6c51.txt` (the IndexNow key, public by protocol).

## The one stylesheet, the one script

- `site.css` — the design the site has always had: graphite ground, amber accent, Bricolage Grotesque headlines
  (Instrument Sans body, IBM Plex Mono for the camera lines), the aurora behind a hero, the floating glass pill
  nav, numbered eyebrows, hairline sections, the render-tracks demo. The `INNER PAGES` block holds what the other
  pages need (page hero, breadcrumbs, prose, panels, definition rows, calculator, the film players that used to live
  in `styles.html`, the legal layout that used to live in `privacy.html`). Phones: everything phone-specific sits at
  the END of the file (`PHONE`, scoped to `max-width:820px` / `600px`); nothing in there may change the page at
  821px and up. Light theme follows `prefers-color-scheme` (or `data-theme` on `<html>`).
- `site.js` — one script for every page, each block looking for its own elements: the menu button under 820px
  (with scripts off the `no-js` class on `<html>` wraps the links inside the pill instead), the copy buttons
  (`data-copy`, toast, an aria-label that says what is copied), the `config.json` override below, reveal on scroll,
  the progress hairline, the REC timecode and the render loop on the home (real stages: treatment, storyboard,
  footage, narration, finish), the pricing calculator (`#duration` → `#credit-result`, the server's rule), the sample
  films (they play muted while in view and are only fetched then; no controls, no menu, no drag: shown, not handed
  over), the Italian hash map, the looks page tint. No analytics, no cookies, no remote code: the privacy page
  promises that.
- Both are linked with `?v=20260915`; bump it when you change either, so nobody reads a new page with an old
  stylesheet from the cache. The only remote resources on the site are the three Google Fonts faces.

## The server address

The address `https://mcp.kleooai.com/mcp` ships IN the markup (so a reader without JavaScript gets one that answers)
and `config.json` overrides it at load time: change `mcp_url` there to move the server without touching every page,
and, when convenient, the markup too. The optional `note` in `config.json` is shown above the address on the home
and on `/connect/` (`#server-note`); keep it true to the product (it says what a new account gets).

## Rules

- The pages may only promise what the deployed server does. Today: one narrated film, realistic or animation, every
  shot generated as moving footage, 15 s to 5 min, 16:9 or 9:16, English or Italian, 4K 60 fps, no music, no
  captions, no automatic publishing; 1 credit = 2 s, 10 credits minimum, 7 credits on connecting, packs €5/€15/€40.
  When the server changes, change the pages the same day — and `tools/check.py` (its `FORBIDDEN` list) refuses the
  words that were wrong before ("8 minutes", "free film", "template", …).
- Every page has a unique title and description, an absolute canonical, Open Graph/Twitter tags and pretty-printed
  JSON-LD (`WebSite`, `WebPage`, `BreadcrumbList`; `SoftwareApplication` on the home; `VideoObject` on the film pages
  with the attested `uploadDate` = the commit that published the file). No ratings, no reviews, no invented dates.
- The header and footer are the same markup on every page (the checker diffs them); `aria-current="page"` only on a
  header link that points at the page itself.
- No destructive cleanup of the public folder: `samples/` (the MP4s and posters), `brand/`, `worker/kleo_worker.py`
  (a copy of the GPU worker a rented machine could download at boot when `VAST_BOOTSTRAP_URL` is set; the production
  image already ships it) stay.

## Checks — before every push, no browser needed

```sh
python3 tools/check.py && node --check site.js
```

`tools/check.py` proves: every page is well-formed (tags balance, one h1, unique ids), every local link, anchor,
image, poster and video points at a file that exists, titles/descriptions/canonicals are unique and consistent,
JSON-LD parses, header/footer are identical everywhere, the sitemap lists exactly the indexable pages with real
dates, robots.txt names the sitemap, the videos follow the owner's rule, and no page says a forbidden thing.

After a deploy: `python3 tools/indexnow.py --since <previous live commit>` (dry run) then `--submit` sends the changed
URLs to IndexNow once the live pages match the repo byte for byte. Google does not use IndexNow: after a change to
the sitemap, ask Search Console to re-read it, and inspect the priority pages once.
