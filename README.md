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
| `/pricing/` | `pricing/index.html` | Packs, the calculator (`#duration` → `#credit-result`, same rules as the server; the film/animatic switch is the pair of `.chip[data-product]` buttons), the cost table. |
| `/faq/`, `/about/` | `faq/index.html`, `about/index.html` | |
| `/legal.html`, `/privacy.html`, `/terms.html` | | Historical routes. Operator: Kanaky Tech, NZBN 9429053554017. |
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
  previews (they play muted while in view and are only fetched then); the four individual film pages instead use
  native playback, sound and fullscreen controls, identified by `data-watch-player` and `.watch-media`, the Italian hash map, the looks page tint. No analytics, no cookies, no remote code: the privacy page
  promises that.
- Assets carry dated `?v=` versions; bump them on updated pages when changing shared assets, so nobody reads a new page with an old
  stylesheet from the cache. The only remote resources on the site are the three Google Fonts faces.

## The server address

The address `https://mcp.kleooai.com/mcp` ships IN the markup (so a reader without JavaScript gets one that answers)
and `config.json` overrides it at load time: change `mcp_url` there to move the server without touching every page,
and, when convenient, the markup too. The optional `note` in `config.json` is shown above the address on the home
and on `/connect/` (`#server-note`); keep it true to the product (it says what a new account gets).

## Rules

- The pages may only promise what the deployed server does. Today: two products from one storyboard — the FILM,
  realistic or animation, every frame drawn by Google Nano Banana Pro and every shot generated as moving footage by
  ByteDance Seedance 2.5, 15 s to 5 min, 16:9 or 9:16, English (default) or Italian, 4K 60 fps, an optional AI upscale
  (Real-ESRGAN + RIFE, film only, the film's credits again with a minimum of 5, refunded automatically if it cannot be
  applied), a music track (Suno) and burned-in subtitles on request, no automatic publishing; 1 credit = 2 s, 10 credits minimum, made only for
  accounts that have bought a pack — and the ANIMATIC, the same storyboard's drawn frames under a moving camera, no
  generated clip, 15–60 s, 5 credits flat, for every account. 7 credits on connecting (one animatic), packs €5/€15/€40.
  The intake asks in one message: look, film or animatic, AI upscale (film only), music, subtitles, narration
  language. A vision model checks every picture against the request; the user's photos become character references.
  Public texts name Seedance 2.5 and Nano Banana Pro and never name the retired clip provider. The privacy page must
  still name every processor truthfully: pictures, clips and music go through the ePhone AI gateway (PULSE AI
  SINGAPORE PTE. LTD.) to Google, ByteDance and Suno. Current Terms
  specify a Kleo mark and a permission requirement for service resale; preserve those until the operator updates them.
  A €5 pack buys 10 credits: enough for a 20-second film. Do not promise a 30-second film from a 12-credit balance
  after a starter animatic. Gift-credit eligibility must be aligned by the operator before advertising its film use.
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

After a deploy: `python3 tools/livecheck.py` proves every page is live with the repo's exact bytes, the 404 is real,
the discovery files and the films are served; then `python3 tools/indexnow.py --since <previous live commit>` (dry run)
and `--submit` send the changed URLs to IndexNow once the live pages match the repo byte for byte. Google does not use IndexNow: after a change to
the sitemap, ask Search Console to re-read it, and inspect the priority pages once.

## Website improvement release — 24 September 2026

The homepage retains the original graphite/amber palette, type, REC and rendering demo. Original animated light
trails add ambience without remote code or media. Their motion pauses offscreen, respects reduced motion, and has
a pause control. The connection studio ships its final geometry before its deferred enhancement to avoid layout
shifts. Without JavaScript the native disclosures still show the connection instructions.

The four `/examples/<film>/` pages deliberately allow native video controls and fullscreen. The old no-controls
rule still applies to silent previews in the home/gallery/other pages. `tools/check.py` enforces both modes and
prevents marking arbitrary preview pages as watch players. The main film source/poster/VideoObject remain in HTML;
playback is initiated by the visitor and volume is not reset by the autoplay script. Hiding download UI is not DRM.

Home and connection pages distinguish the 5-credit starter animatic from paid films, with approval required in
each copied prompt. Product policy and backend changes remain the operator’s responsibility; this website release
does not modify the engine, MCP worker, account system, Terms, Privacy or prices.

The homepage serves the original font families from `brand/fonts/` with their OFL licenses and source URLs,
preloading its display and body faces. Inner pages retain their existing Google Fonts loading.

## Homepage cinematic interlude

`cinema-scroll.css` animates the amber curves. The film sequence now has three independent, clickable image planes. Three.js core Matrix4/Quaternion transforms place and rotate each plane; CSS perspective and the browser compositor draw them, with no WebGL render loop. A pinned section advances Signal Delay → Apex → Tether as the visitor scrolls. Progress is measured over the actual sticky travel, from 0 to 1, and the selected film is labeled 01/03–03/03.

The local MIT-licensed Three.js core loads near the section. No scroll interception. Motion uses time-based smoothing and stops after settling, while paused, offscreen or in a hidden tab. Reduced motion, Save-Data, JavaScript absence or module failure show ordinary image links. Images and text remain HTML, and the active plane is keyboard reachable. Film assets, metadata, copy and MCP are unchanged.

## Kleo vertical ad showcase

`/examples/kleo-ad/` contains the supplied 30-second English Kleo ad. Original master: 2160×3840, 60 fps, 528,631,814 bytes. Web MP4: 1080×1920, 60 fps, H.264 + AAC, faststart, 24,831,787 bytes. Poster extracted at 28 seconds. The original master stays outside the repository; no download of the 504 MB original is imposed on visitors. Homepage and example gallery link to the native controlled watch player.

## ChatGPT publication and publisher identity — 25 September 2026

The common footer and `/legal.html` identify Kanaky Tech, NZBN 9429053554017.
Privacy now covers reference pictures (30 days after last use), Stripe checkout email, image generation through
the model gateway for both products, hosting, fonts and overseas processing (updated 26 September 2026: ePhone AI
routing to Google, ByteDance and Suno). Terms preserve mandatory consumer rights.

`config.json` contains `chatgpt_url: null` until OpenAI approves and the publisher publishes the plugin.
The ChatGPT install promotion is hidden by default on the home, connection hub and ChatGPT guide, as requested
by the publisher. It must remain hidden until the app is approved and publicly available. Set the URL ONLY to
the real public Kleo directory URL copied from the publication portal. The promotion then becomes visible as
**Connect with ChatGPT** and the manual setup block is hidden. The URL is restricted
to HTTPS ChatGPT directory paths and must contain no credentials, query string or fragment. Invalid config or
a fetch failure keeps the existing setup available. Never put a private preview URL or OAuth token here.

After publication, also update the static ChatGPT guide requirements and fallback markup to the actual public
connection steps, then verify the link in a fresh account and on mobile. Changing a config URL does not submit,
approve, publish or silently connect a plugin; users still approve the sign-in in ChatGPT.

The public site identifies only Kanaky Tech. Keep personal names and personal email addresses out of public pages and metadata. The shared footer groups Create, Connect, Resources and Legal & support links, with social links under the brand and the NZBN in a separate bottom line.
