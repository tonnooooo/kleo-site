# Kleo production guide library

81 authored guides, 8 topic hubs, 1 central library: 90 new routes, 107 total with the original 17.
English content, matching the current site. No claim that French or other localized pages exist.

## Editing

Each record in `*.txt` has seven pipe-separated fields:
slug | title | direct answer | three method steps separated by ~ | original example brief | three review questions separated by ~ | pitfall.

These are original editorial methods and fictional planning examples. They are not customer results, rendered examples, tested prompts, an independent product review, measured search demand or evidence of a ranking gain.

`guide-enrichments.json` holds subject-specific sections for four decision guides: the free offer, a first animatic, animatic versus film, and credit planning. Sections can contain paragraphs, accessible comparison tables, ordered steps, short questions/answers and related links. Their worksheet fields and reference notes are also exported to the downloadable text files. Keep those examples distinct from claims of actually rendered work; their review date applies only to the enriched guide.

Run from the repository root:

```sh
python3 tools/build_guides.py
python3 tools/sitemap.py
python3 tools/check.py
python3 tools/check_guides.py
node --check site.js
```

`build_guides.py` regenerates the guide HTML, worksheets, eight vector diagrams, routes, inventory and library CSS. It also adds the same Guides link to existing footers and an entrance in the main YouTube product guide, preserving existing metadata and links. The generator obtains the existing head/navigation/footer from that main guide. Keep the common footer synchronized if changing its design.

For content-only work while other site pages are being edited, use `python3 tools/build_guides.py --guides-only`. It reads the current shared head/navigation/footer but writes only the library and its editorial inventory; it does not rewrite the existing pages or their footers. A normal generation remains suitable after integration.

`check.py`, `livecheck.py` and `indexnow.py` share the route inventory through `editorial/routes.json`. The expected counts in `check_guides.py` should change deliberately when adding/removing guides. No runtime server, package install, external tracking or new backend is required.

## Sources checked 23 September 2026

- https://kleooai.com/faq/ — public product scope, duration/language/format restrictions and downloads.
- https://kleooai.com/pricing/ — starter credits, animatic and paid-film conditions. Check the quote at actual production time.
- https://kleooai.com/connect/ — supported-client connection guidance; assistant plans are separate.
- https://support.google.com/youtube/answer/15424877?hl=en — Shorts classification. The guides deliberately do not paraphrase the changing music/Content ID exception rules.
- https://support.google.com/youtube/answer/57407?hl=en — upload process.
- https://support.google.com/youtube/answer/14328491?hl=en — altered/synthetic-content disclosure.
- https://www.w3.org/WAI/media/av/captions/ — captions and human accuracy review.
- https://modelcontextprotocol.io/docs/learn/architecture — host/client/server distinction.

External source pages support the narrowly identified platform/accessibility/protocol statements. They do not endorse Kleo or validate the original editorial examples.

## Free intent

Four distinct guides: scope of the free starting offer; using one starter-credit animatic; planning before production; choosing an animatic versus a paid film. The public offer checked is 7 starter credits, 5 credits per animatic, a pack purchase required for generated-footage films. Do not convert this into an unlimited or fully free-film promise. The user's observation about FREE in YouTube titles is an editorial hypothesis, not measured Google query volume.

Credit eligibility checked 24 September 2026: the arithmetic of 7 starter + 10 purchased = 17 total credits is distinct from how many credits can be used for films. The published Terms restrict given credits to animatics. Do not promise that unused starter credits fund a 30-second film after a €5 purchase until the operator aligns that policy with the account behavior. Examples based on purchased credits alone are safe: 10 purchased credits cover a 20-second film; a 30-second film costs 15 eligible credits. After one 5-credit starter animatic and a €5 pack, the total balance is 12, not 17.

## Publication facts to confirm

The public website and MCP repository have discrepancies about output resolution and included audio/caption deliverables. The new guides avoid promising an exact master resolution or bundled caption files and direct users to inspect the export. The owner must confirm any product wording they change before deployment. Existing claims on pre-existing pages were not rewritten in this delivery.

No publication date is invented in Article markup. The visible editorial-review date is the preparation date. Generate the sitemap on the actual integration day; lastmod reflects changed/new files using the existing project tool.

When a generated page is unchanged apart from CSS/JS cache versions, the generator keeps its existing bytes. This avoids moving content modification dates on unrelated guides. Updated pages receive the current shared asset versions during integration; cache-only rollouts should be deliberate.
