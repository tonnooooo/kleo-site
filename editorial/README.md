# Kleo production guide library

81 authored guides, 8 topic hubs, 1 central library: 90 new routes, 107 total with the original 17.
English content, matching the current site. No claim that French or other localized pages exist.

## Editing

Each record in `*.txt` has seven pipe-separated fields:
slug | title | direct answer | three method steps separated by ~ | original example brief | three review questions separated by ~ | pitfall.

These are original editorial methods and fictional planning examples. They are not customer results, rendered examples, tested prompts, an independent product review, measured search demand or evidence of a ranking gain.

Run from the repository root:

```sh
python3 tools/build_guides.py
python3 tools/sitemap.py
python3 tools/check.py
python3 tools/check_guides.py
node --check site.js
```

`build_guides.py` regenerates the guide HTML, worksheets, eight vector diagrams, routes, inventory and library CSS. It also adds the same Guides link to existing footers and an entrance in the main YouTube product guide, preserving existing metadata and links. The generator obtains the existing head/navigation/footer from that main guide. Keep the common footer synchronized if changing its design.

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

## Publication facts to confirm

The public website and MCP repository have discrepancies about output resolution and included audio/caption deliverables. The new guides avoid promising an exact master resolution or bundled caption files and direct users to inspect the export. The owner must confirm any product wording they change before deployment. Existing claims on pre-existing pages were not rewritten in this delivery.

No publication date is invented in Article markup. The visible editorial-review date is the preparation date. Generate the sitemap on the actual integration day; lastmod reflects changed/new files using the existing project tool.
